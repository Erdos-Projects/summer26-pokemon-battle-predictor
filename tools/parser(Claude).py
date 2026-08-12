"""
Pokemon Showdown battle log parser.

Parses a Showdown battle log (the |...|...|... protocol format) into a
"time series" of turns. For each turn, we get a full snapshot of battle
state (every Pokemon's HP/status/boosts, field weather/terrain, each
side's hazards) AND the list of raw events that happened during that turn.

Main entry points:
    parse_log(text)          -> BattleState (with .turns: List[TurnSnapshot])
    parse_log_to_dataframe(text) -> pandas.DataFrame, one row per Pokemon per turn
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional, Any
import copy
import re


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class PokemonState:
    """State of a single Pokemon at a point in time."""
    slot: str                      # e.g. "p1a" - the current slot identifier
    side: str                      # "p1" or "p2"
    name: str                      # nickname as shown in log, e.g. "Delphox"
    species: str                   # species name, e.g. "Delphox"
    level: Optional[int] = None
    gender: Optional[str] = None
    shiny: bool = False
    is_active: bool = False

    hp_cur: Optional[int] = None   # current HP (raw number if shown, else None)
    hp_max: Optional[int] = None   # max HP (raw number if shown, else None)
    hp_pct: Optional[float] = None # current HP as % of max (0-100), always derivable
    fainted: bool = False

    status: Optional[str] = None   # 'par','psn','brn','slp','frz','tox', or None
    boosts: Dict[str, int] = field(default_factory=lambda: {
        "atk": 0, "def": 0, "spa": 0, "spd": 0, "spe": 0, "accuracy": 0, "evasion": 0
    })

    ability: Optional[str] = None      # revealed ability, if known
    item: Optional[str] = None         # revealed item, if known
    item_was_removed: bool = False     # tracks knockoff/etc (item field set to None)
    terastallized: bool = False
    tera_type: Optional[str] = None
    volatile: List[str] = field(default_factory=list)  # e.g. ['confusion', 'substitute']

    def hp_fraction(self) -> Optional[float]:
        if self.hp_pct is not None:
            return self.hp_pct / 100.0
        if self.hp_cur is not None and self.hp_max:
            return self.hp_cur / self.hp_max
        return None


@dataclass
class SideState:
    """State of one player's side (hazards, screens, etc.)."""
    player: str                 # "p1" or "p2"
    username: Optional[str] = None
    side_conditions: Dict[str, int] = field(default_factory=dict)
    # side_conditions maps condition name -> layer count / turns remaining marker
    # e.g. {'Spikes': 2, 'Stealth Rock': 1, 'Reflect': 1}
    active_slot: Optional[str] = None   # which slot identifier is currently active, e.g. "p1a"


@dataclass
class FieldState:
    weather: Optional[str] = None
    terrain: Optional[str] = None
    pseudo_weather: List[str] = field(default_factory=list)  # trick room, etc.


@dataclass
class TurnSnapshot:
    """A full snapshot of battle state as of the end of a given turn."""
    turn: int
    pokemon: Dict[str, PokemonState]   # keyed by "p1a: Name"-style unique key (side+nickname)
    sides: Dict[str, SideState]
    field: FieldState
    events: List[Dict[str, Any]]       # raw parsed events that occurred during this turn
    winner: Optional[str] = None


@dataclass
class BattleState:
    p1_username: Optional[str] = None
    p2_username: Optional[str] = None
    tier: Optional[str] = None
    gen: Optional[str] = None
    turns: List[TurnSnapshot] = field(default_factory=list)
    winner: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

STAT_KEYS = ["atk", "def", "spa", "spd", "spe", "accuracy", "evasion"]

HP_RE = re.compile(r"^(\d+)/(\d+)$")          # e.g. "263/263"
HP_FNT_RE = re.compile(r"^0\s*fnt$")          # e.g. "0 fnt"
PCT_RE = re.compile(r"^(\d+)/(\d+)\s*(\w+)?$")  # also matches raw HP with status suffix


def parse_hp_field(hp_str: str):
    """
    Parse an HP field like '263/263', '309/397', '0 fnt', '109/100 par' (with status suffix).
    Returns (hp_cur, hp_max, hp_pct, fainted, status_suffix).
    Showdown sends either raw numbers (e.g. 263/263) or, with HP Percentage Mod,
    values that are *already* percentages (e.g. 78/100). Either way we treat the
    pair as cur/max and derive a percentage; this is correct for both cases.
    """
    if hp_str is None:
        return None, None, None, False, None

    hp_str = hp_str.strip()
    fainted = False
    status_suffix = None

    parts = hp_str.split()
    main = parts[0]
    if len(parts) > 1:
        status_suffix = parts[1]

    if main == "0":
        fainted = True
        return 0, None, 0.0, True, None

    m = re.match(r"^(\d+)/(\d+)$", main)
    if m:
        cur, mx = int(m.group(1)), int(m.group(2))
        pct = (cur / mx * 100.0) if mx else None
        return cur, mx, pct, False, status_suffix

    # Fallback: couldn't parse, just return raw string info
    return None, None, None, False, status_suffix


def parse_pokemon_details(details: str):
    """
    Parse the "details" field from |switch| / |drag|, e.g.:
      "Delphox, L84, F"
      "Wigglytuff, L96, F"
      "Mienshao, L83, F, shiny"
      "Tauros-Paldea-Aqua, L81, M"
    Returns dict with species, level, gender, shiny.
    """
    pieces = [p.strip() for p in details.split(",")]
    species = pieces[0] if pieces else details
    level = None
    gender = None
    shiny = False
    for p in pieces[1:]:
        if p.startswith("L") and p[1:].isdigit():
            level = int(p[1:])
        elif p in ("M", "F", "N"):
            gender = p
        elif p.lower() == "shiny":
            shiny = True
    return {"species": species, "level": level, "gender": gender, "shiny": shiny}


def parse_ident(ident: str):
    """
    Parse a pokemon identifier like 'p1a: Delphox' -> ('p1a', 'p1', 'Delphox')
    Returns (slot, side, nickname).
    """
    ident = ident.strip()
    if ":" in ident:
        slot, name = ident.split(":", 1)
        slot = slot.strip()
        name = name.strip()
    else:
        slot = ident
        name = ident
    side = slot[:2] if slot[:2] in ("p1", "p2") else slot
    return slot, side, name


def pokemon_key(side: str, nickname: str) -> str:
    """Stable key to track a single Pokemon across switches: side + nickname."""
    return f"{side}: {nickname}"


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

class BattleLogParser:
    def __init__(self):
        self.battle = BattleState()
        self.pokemon: Dict[str, PokemonState] = {}      # key -> PokemonState (persists across turns)
        self.slot_to_key: Dict[str, str] = {}            # current slot ("p1a") -> pokemon_key
        self.sides: Dict[str, SideState] = {
            "p1": SideState(player="p1"),
            "p2": SideState(player="p2"),
        }
        self.field = FieldState()
        self.current_turn = 0
        self.current_events: List[Dict[str, Any]] = []
        self.turns: List[TurnSnapshot] = []
        self.winner: Optional[str] = None

    # -- bookkeeping -------------------------------------------------------

    def _get_or_create_pokemon(self, slot: str, nickname: str, side: str) -> PokemonState:
        key = pokemon_key(side, nickname)
        if key not in self.pokemon:
            self.pokemon[key] = PokemonState(
                slot=slot, side=side, name=nickname, species=nickname
            )
        return self.pokemon[key]

    def _pokemon_at_slot(self, slot: str) -> Optional[PokemonState]:
        key = self.slot_to_key.get(slot)
        if key is None:
            return None
        return self.pokemon.get(key)

    def _set_active(self, slot: str, key: str):
        side = slot[:2]
        # Mark previous occupant of slot (if any) inactive
        prev_key = self.slot_to_key.get(slot)
        if prev_key is not None and prev_key in self.pokemon:
            self.pokemon[prev_key].is_active = False
        self.slot_to_key[slot] = key
        self.pokemon[key].is_active = True
        self.pokemon[key].slot = slot
        self.sides[side].active_slot = slot

    def _record_event(self, etype: str, raw: List[str], **kwargs):
        evt = {"type": etype, "raw": "|".join(raw)}
        evt.update(kwargs)
        self.current_events.append(evt)

    def _snapshot(self) -> TurnSnapshot:
        return TurnSnapshot(
            turn=self.current_turn,
            pokemon={k: copy.deepcopy(v) for k, v in self.pokemon.items()},
            sides={k: copy.deepcopy(v) for k, v in self.sides.items()},
            field=copy.deepcopy(self.field),
            events=list(self.current_events),
            winner=self.winner,
        )

    def _flush_turn(self):
        """Called when we hit a new |turn|N| marker or the end of the log."""
        self.turns.append(self._snapshot())
        self.current_events = []

    # -- main loop -----------------------------------------------------------

    def parse(self, text: str) -> BattleState:
        lines = text.splitlines()
        for line in lines:
            self._handle_line(line)

        # Flush whatever's left as a final snapshot (post-battle-end state),
        # but only if there were events since the last turn boundary.
        if self.current_events or not self.turns:
            self._flush_turn()

        self.battle.turns = self.turns
        self.battle.winner = self.winner
        return self.battle

    # -- line dispatch ---------------------------------------------------

    def _handle_line(self, line: str):
        if not line.startswith("|"):
            return
        parts = line.split("|")
        # parts[0] is '' because line starts with '|'
        if len(parts) < 2:
            return
        cmd = parts[1]
        args = parts[2:]

        if cmd == "":
            return  # blank separator line ("|"), no information content

        safe_cmd = cmd.replace("-", "_").replace(":", "_")
        handler = getattr(self, f"_h_{safe_cmd}", None)
        if handler is not None:
            handler(args, line)
        else:
            # Unhandled message types are still recorded for completeness
            self._record_event("other:" + cmd, [line], args=args)

    # -- handlers: meta ----------------------------------------------------

    def _h_player(self, args, raw):
        if len(args) >= 2:
            side, username = args[0], args[1]
            if side in self.sides:
                self.sides[side].username = username or self.sides[side].username
            if side == "p1" and username:
                self.battle.p1_username = username
            if side == "p2" and username:
                self.battle.p2_username = username

    def _h_tier(self, args, raw):
        self.battle.tier = args[0] if args else None

    def _h_gen(self, args, raw):
        self.battle.gen = args[0] if args else None

    def _h_turn(self, args, raw):
        # New turn begins: flush the previous turn's snapshot+events first.
        self._flush_turn()
        self.current_turn = int(args[0]) if args and args[0].isdigit() else self.current_turn + 1

    def _h_win(self, args, raw):
        self.winner = args[0] if args else None
        self._record_event("win", [raw], winner=self.winner)

    def _h_upkeep(self, args, raw):
        self._record_event("upkeep", [raw])

    # -- handlers: switches --------------------------------------------------

    def _switch_or_drag(self, args, raw, is_drag):
        ident, details, hp_str = args[0], args[1], args[2] if len(args) > 2 else None
        slot, side, nickname = parse_ident(ident)
        info = parse_pokemon_details(details)
        key = pokemon_key(side, nickname)

        poke = self._get_or_create_pokemon(slot, nickname, side)
        poke.species = info["species"]
        poke.level = info["level"]
        poke.gender = info["gender"]
        poke.shiny = info["shiny"]

        if hp_str:
            cur, mx, pct, fainted, status_suffix = parse_hp_field(hp_str)
            poke.hp_cur, poke.hp_max, poke.hp_pct = cur, mx, pct
            poke.fainted = fainted
            poke.status = status_suffix if status_suffix else None

        # On switch, volatile conditions and boosts reset (standard Showdown rule)
        poke.boosts = {k: 0 for k in STAT_KEYS}
        poke.volatile = []

        self._set_active(slot, key)

        self._record_event(
            "drag" if is_drag else "switch", [raw],
            slot=slot, side=side, pokemon=nickname, species=info["species"], hp=hp_str,
        )

    def _h_switch(self, args, raw):
        self._switch_or_drag(args, raw, is_drag=False)

    def _h_drag(self, args, raw):
        self._switch_or_drag(args, raw, is_drag=True)

    def _h_replace(self, args, raw):
        # Illusion reveal etc. - treat like switch but keep it labeled distinctly
        self._switch_or_drag(args, raw, is_drag=False)

    # -- handlers: moves / can't act -----------------------------------------

    def _h_move(self, args, raw):
        ident = args[0] if args else None
        movename = args[1] if len(args) > 1 else None
        target = args[2] if len(args) > 2 else None
        slot, side, nickname = parse_ident(ident) if ident else (None, None, None)
        self._record_event(
            "move", [raw], slot=slot, side=side, pokemon=nickname,
            move=movename, target=target,
        )

    def _h_cant(self, args, raw):
        ident = args[0] if args else None
        reason = args[1] if len(args) > 1 else None
        slot, side, nickname = parse_ident(ident) if ident else (None, None, None)
        self._record_event("cant", [raw], slot=slot, side=side, pokemon=nickname, reason=reason)

    # -- handlers: damage / heal ---------------------------------------------

    def _h__damage(self, args, raw):
        self._apply_hp_change(args, raw, "damage")

    def _h__heal(self, args, raw):
        self._apply_hp_change(args, raw, "heal")

    def _apply_hp_change(self, args, raw, kind):
        ident = args[0]
        hp_str = args[1] if len(args) > 1 else None
        extra = args[2:] if len(args) > 2 else []
        slot, side, nickname = parse_ident(ident)
        poke = self._pokemon_at_slot(slot)
        prev_pct = poke.hp_pct if poke else None
        if poke is not None and hp_str is not None:
            cur, mx, pct, fainted, status_suffix = parse_hp_field(hp_str)
            poke.hp_cur, poke.hp_max, poke.hp_pct = cur, mx, pct
            poke.fainted = fainted
            if status_suffix:
                poke.status = status_suffix
        source = None
        for e in extra:
            if e.startswith("[from]") or e.startswith("[of]"):
                source = (source + "; " if source else "") + e
        self._record_event(
            kind, [raw], slot=slot, side=side, pokemon=nickname,
            hp_after=hp_str, prev_hp_pct=prev_pct,
            new_hp_pct=(poke.hp_pct if poke else None), source=source,
        )

    # -- handlers: fainting ---------------------------------------------------

    def _h_faint(self, args, raw):
        ident = args[0]
        slot, side, nickname = parse_ident(ident)
        poke = self._pokemon_at_slot(slot)
        if poke is not None:
            poke.fainted = True
            poke.hp_cur = 0
            poke.hp_pct = 0.0
        self._record_event("faint", [raw], slot=slot, side=side, pokemon=nickname)

    # -- handlers: status -----------------------------------------------------

    def _h__status(self, args, raw):
        ident = args[0]
        status = args[1] if len(args) > 1 else None
        slot, side, nickname = parse_ident(ident)
        poke = self._pokemon_at_slot(slot)
        if poke is not None:
            poke.status = status
        self._record_event("status", [raw], slot=slot, side=side, pokemon=nickname, status=status)

    def _h__curestatus(self, args, raw):
        ident = args[0]
        status = args[1] if len(args) > 1 else None
        slot, side, nickname = parse_ident(ident)
        poke = self._pokemon_at_slot(slot)
        if poke is not None:
            poke.status = None
        self._record_event("curestatus", [raw], slot=slot, side=side, pokemon=nickname, status=status)

    # -- handlers: boosts -------------------------------------------------

    def _boost_change(self, args, raw, sign, kind):
        ident = args[0]
        stat = args[1] if len(args) > 1 else None
        amount = int(args[2]) if len(args) > 2 and args[2].lstrip("-").isdigit() else 0
        slot, side, nickname = parse_ident(ident)
        poke = self._pokemon_at_slot(slot)
        if poke is not None and stat in poke.boosts:
            poke.boosts[stat] = max(-6, min(6, poke.boosts[stat] + sign * amount))
        self._record_event(
            kind, [raw], slot=slot, side=side, pokemon=nickname, stat=stat, amount=sign * amount,
        )

    def _h__boost(self, args, raw):
        self._boost_change(args, raw, sign=1, kind="boost")

    def _h__unboost(self, args, raw):
        self._boost_change(args, raw, sign=-1, kind="unboost")

    def _h__setboost(self, args, raw):
        ident = args[0]
        stat = args[1] if len(args) > 1 else None
        amount = int(args[2]) if len(args) > 2 and args[2].lstrip("-").isdigit() else 0
        slot, side, nickname = parse_ident(ident)
        poke = self._pokemon_at_slot(slot)
        if poke is not None and stat in poke.boosts:
            poke.boosts[stat] = amount
        self._record_event("setboost", [raw], slot=slot, side=side, pokemon=nickname, stat=stat, amount=amount)

    def _h__clearboost(self, args, raw):
        ident = args[0]
        slot, side, nickname = parse_ident(ident)
        poke = self._pokemon_at_slot(slot)
        if poke is not None:
            poke.boosts = {k: 0 for k in STAT_KEYS}
        self._record_event("clearboost", [raw], slot=slot, side=side, pokemon=nickname)

    def _h__clearallboost(self, args, raw):
        for poke in self.pokemon.values():
            poke.boosts = {k: 0 for k in STAT_KEYS}
        self._record_event("clearallboost", [raw])

    def _h__swapboost(self, args, raw):
        # not unpacking detailed stat list; just record the event
        self._record_event("swapboost", [raw], args=args)

    def _h__invertboost(self, args, raw):
        ident = args[0]
        slot, side, nickname = parse_ident(ident)
        poke = self._pokemon_at_slot(slot)
        if poke is not None:
            poke.boosts = {k: -v for k, v in poke.boosts.items()}
        self._record_event("invertboost", [raw], slot=slot, side=side, pokemon=nickname)

    # -- handlers: ability / item reveals -------------------------------------

    def _h__ability(self, args, raw):
        ident = args[0]
        ability = args[1] if len(args) > 1 else None
        slot, side, nickname = parse_ident(ident)
        poke = self._pokemon_at_slot(slot)
        if poke is not None:
            poke.ability = ability
        self._record_event("ability", [raw], slot=slot, side=side, pokemon=nickname, ability=ability)

    def _h__item(self, args, raw):
        ident = args[0]
        item = args[1] if len(args) > 1 else None
        slot, side, nickname = parse_ident(ident)
        poke = self._pokemon_at_slot(slot)
        if poke is not None:
            poke.item = item
        self._record_event("item", [raw], slot=slot, side=side, pokemon=nickname, item=item)

    def _h__enditem(self, args, raw):
        ident = args[0]
        item = args[1] if len(args) > 1 else None
        slot, side, nickname = parse_ident(ident)
        poke = self._pokemon_at_slot(slot)
        if poke is not None:
            poke.item = None
            poke.item_was_removed = True
        self._record_event("enditem", [raw], slot=slot, side=side, pokemon=nickname, item=item)

    # -- handlers: terastallize -------------------------------------------

    def _h__terastallize(self, args, raw):
        ident = args[0]
        ttype = args[1] if len(args) > 1 else None
        slot, side, nickname = parse_ident(ident)
        poke = self._pokemon_at_slot(slot)
        if poke is not None:
            poke.terastallized = True
            poke.tera_type = ttype
        self._record_event("terastallize", [raw], slot=slot, side=side, pokemon=nickname, tera_type=ttype)

    # -- handlers: side conditions (hazards/screens) -------------------------

    def _h__sidestart(self, args, raw):
        side_full = args[0] if args else None  # e.g. "p2: N.TdaRajada"
        condition = args[1] if len(args) > 1 else None
        side = side_full.split(":")[0].strip() if side_full else None
        if side in self.sides and condition:
            self.sides[side].side_conditions[condition] = self.sides[side].side_conditions.get(condition, 0) + 1
        self._record_event("sidestart", [raw], side=side, condition=condition)

    def _h__sideend(self, args, raw):
        side_full = args[0] if args else None
        condition = args[1] if len(args) > 1 else None
        side = side_full.split(":")[0].strip() if side_full else None
        if side in self.sides and condition:
            self.sides[side].side_conditions.pop(condition, None)
        self._record_event("sideend", [raw], side=side, condition=condition)

    # -- handlers: field-wide conditions ------------------------------------

    def _h__weather(self, args, raw):
        weather = args[0] if args else None
        if weather in (None, "none", ""):
            self.field.weather = None
        elif args and len(args) > 1 and "[upkeep]" in args[1]:
            pass  # just an upkeep reminder, weather already set
        else:
            self.field.weather = weather
        self._record_event("weather", [raw], weather=weather)

    def _h__fieldstart(self, args, raw):
        condition = args[0] if args else None
        if condition and "Terrain" in condition:
            self.field.terrain = condition
        elif condition:
            if condition not in self.field.pseudo_weather:
                self.field.pseudo_weather.append(condition)
        self._record_event("fieldstart", [raw], condition=condition)

    def _h__fieldend(self, args, raw):
        condition = args[0] if args else None
        if condition and "Terrain" in condition:
            self.field.terrain = None
        elif condition and condition in self.field.pseudo_weather:
            self.field.pseudo_weather.remove(condition)
        self._record_event("fieldend", [raw], condition=condition)

    # -- handlers: volatile statuses (confusion, substitute, etc.) ----------

    def _h__start(self, args, raw):
        ident = args[0]
        volatile = args[1] if len(args) > 1 else None
        slot, side, nickname = parse_ident(ident)
        poke = self._pokemon_at_slot(slot)
        if poke is not None and volatile and volatile not in poke.volatile:
            poke.volatile.append(volatile)
        self._record_event("start", [raw], slot=slot, side=side, pokemon=nickname, volatile=volatile)

    def _h__end(self, args, raw):
        ident = args[0]
        volatile = args[1] if len(args) > 1 else None
        slot, side, nickname = parse_ident(ident)
        poke = self._pokemon_at_slot(slot)
        if poke is not None and volatile and volatile in poke.volatile:
            poke.volatile.remove(volatile)
        self._record_event("end", [raw], slot=slot, side=side, pokemon=nickname, volatile=volatile)

    # -- generic catch-alls for common cosmetic/info messages ----------------
    # These are recorded as events (so they show up in the time series) but
    # don't change the tracked state fields above.

    def _generic(self, args, raw, etype):
        self._record_event(etype, [raw], args=args)

    def _h__crit(self, args, raw):
        self._generic(args, raw, "crit")

    def _h__supereffective(self, args, raw):
        self._generic(args, raw, "supereffective")

    def _h__resisted(self, args, raw):
        self._generic(args, raw, "resisted")

    def _h__immune(self, args, raw):
        self._generic(args, raw, "immune")

    def _h__miss(self, args, raw):
        self._generic(args, raw, "miss")

    def _h__fail(self, args, raw):
        self._generic(args, raw, "fail")

    def _h__activate(self, args, raw):
        self._generic(args, raw, "activate")

    def _h__singleturn(self, args, raw):
        self._generic(args, raw, "singleturn")

    def _h__singlemove(self, args, raw):
        self._generic(args, raw, "singlemove")

    def _h__prepare(self, args, raw):
        self._generic(args, raw, "prepare")

    def _h__mustrecharge(self, args, raw):
        self._generic(args, raw, "mustrecharge")

    def _h__hitcount(self, args, raw):
        self._generic(args, raw, "hitcount")

    def _h__center(self, args, raw):
        self._generic(args, raw, "center")

    def _h__message(self, args, raw):
        self._generic(args, raw, "message")

    def _h__transform(self, args, raw):
        self._generic(args, raw, "transform")

    def _h__formechange(self, args, raw):
        ident = args[0] if args else None
        species = args[1] if len(args) > 1 else None
        slot, side, nickname = parse_ident(ident) if ident else (None, None, None)
        poke = self._pokemon_at_slot(slot) if slot else None
        if poke is not None and species:
            poke.species = species
        self._generic(args, raw, "formechange")

    def _h_inactive(self, args, raw):
        self._generic(args, raw, "inactive")

    def _h_raw(self, args, raw):
        self._generic(args, raw, "raw")

    def _h_c(self, args, raw):
        self._generic(args, raw, "chat")

    def _h_j(self, args, raw):
        pass  # join, ignore

    def _h_l(self, args, raw):
        pass  # leave, ignore

    def _h_t_(self, args, raw):
        pass  # timestamp, ignore

    def _h_gametype(self, args, raw):
        pass

    def _h_rule(self, args, raw):
        pass

    def _h_rated(self, args, raw):
        pass

    def _h_teamsize(self, args, raw):
        pass

    def _h_start(self, args, raw):
        # battle start marker (not to be confused with -start)
        self._generic(args, raw, "battlestart")


def parse_log(text: str) -> BattleState:
    parser = BattleLogParser()
    return parser.parse(text)


# ---------------------------------------------------------------------------
# Tabular ("time series") exports
# ---------------------------------------------------------------------------

def pokemon_timeseries(battle: BattleState):
    """
    Returns a pandas DataFrame with one row per (turn, pokemon) snapshot.
    Columns: turn, side, pokemon, species, is_active, hp_cur, hp_max, hp_pct,
             fainted, status, boost_atk, boost_def, boost_spa, boost_spd,
             boost_spe, boost_accuracy, boost_evasion, ability, item,
             terastallized, tera_type, volatile (semicolon-joined string).
    """
    import pandas as pd

    rows = []
    for snap in battle.turns:
        for key, p in snap.pokemon.items():
            row = {
                "turn": snap.turn,
                "side": p.side,
                "pokemon": p.name,
                "species": p.species,
                "level": p.level,
                "is_active": p.is_active,
                "hp_cur": p.hp_cur,
                "hp_max": p.hp_max,
                "hp_pct": p.hp_pct,
                "fainted": p.fainted,
                "status": p.status,
                "ability": p.ability,
                "item": p.item,
                "terastallized": p.terastallized,
                "tera_type": p.tera_type,
                "volatile": ";".join(p.volatile) if p.volatile else "",
            }
            for stat in STAT_KEYS:
                row[f"boost_{stat}"] = p.boosts.get(stat, 0)
            rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["turn", "side", "pokemon"]).reset_index(drop=True)
    return df


def side_timeseries(battle: BattleState):
    """
    Returns a pandas DataFrame with one row per (turn, side) snapshot,
    capturing hazards/side conditions present at that point.
    Columns: turn, side, username, then one column per observed side
    condition (e.g. 'Spikes', 'Stealth Rock', 'Reflect', ...) holding the
    layer/presence count (0 if absent).
    """
    import pandas as pd

    # First pass: discover all condition names ever seen, for stable columns
    all_conditions = set()
    for snap in battle.turns:
        for side in snap.sides.values():
            all_conditions.update(side.side_conditions.keys())
    all_conditions = sorted(all_conditions)

    rows = []
    for snap in battle.turns:
        for side_key, side in snap.sides.items():
            row = {
                "turn": snap.turn,
                "side": side_key,
                "username": side.username,
            }
            for cond in all_conditions:
                row[cond] = side.side_conditions.get(cond, 0)
            rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["turn", "side"]).reset_index(drop=True)
    return df


def field_timeseries(battle: BattleState):
    """
    Returns a pandas DataFrame with one row per turn capturing field-wide
    state: weather, terrain, and active pseudo-weather (e.g. Trick Room),
    plus the winner once decided.
    Columns: turn, weather, terrain, pseudo_weather (semicolon-joined), winner.
    """
    import pandas as pd

    rows = []
    for snap in battle.turns:
        rows.append({
            "turn": snap.turn,
            "weather": snap.field.weather,
            "terrain": snap.field.terrain,
            "pseudo_weather": ";".join(snap.field.pseudo_weather) if snap.field.pseudo_weather else "",
            "winner": snap.winner,
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("turn").reset_index(drop=True)
    return df


def events_timeseries(battle: BattleState):
    """
    Returns a pandas DataFrame with one row per individual event, in order,
    tagged with the turn it occurred in. Useful for a finer-grained
    "what actually happened" log than the per-turn snapshots provide.
    Columns vary by event type; missing fields are NaN. Always includes
    'turn', 'type', and 'raw'.
    """
    import pandas as pd

    rows = []
    for snap in battle.turns:
        for e in snap.events:
            row = {"turn": snap.turn}
            row.update(e)
            rows.append(row)
    df = pd.DataFrame(rows)
    return df


def parse_log_to_dataframes(text: str):
    """
    Convenience all-in-one: parse a raw log string and return a dict of
    DataFrames: {'pokemon': ..., 'sides': ..., 'field': ..., 'events': ...}
    plus the underlying BattleState under the 'battle' key (in case you
    want to drill into anything not exposed in the tables).
    """
    battle = parse_log(text)
    return {
        "battle": battle,
        "pokemon": pokemon_timeseries(battle),
        "sides": side_timeseries(battle),
        "field": field_timeseries(battle),
        "events": events_timeseries(battle),
    }