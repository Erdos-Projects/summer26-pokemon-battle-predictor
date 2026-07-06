'''
Overview of battle.py 
#################################################

(for brevity, anything of the form `.x` means `self.x`)

`Player` class: 
---------------------------------------
    * .name: str
    * .side: int # 1 or 2
    * .elo0: int # Elo at match start
    * .elo1: int # Elo after match

The dataclasses `Team` and `Pokemon` seen below are fairly self-explanatory.
    * The `Pokemon.base` is the "base form" of the pokemon, possibly different from `Pokemon.forme`. 
        (Ex: `base` = `Tauros` and `forme` = `Tauros-Paldea-Aqua`)
    

`Battle` class (quick facts): 
---------------------------------------
    * `.id` (ex: `gen9randombattle-2631360263`)
    * `.format` (ex: `[Gen 9] Random Battle`)
    
    * `.player1`: <Player> 
    * `.player2`: <Player>
    
    * `.start_time`: game start time (in seconds since the 'Epoch')
    * `.end_time`: (technically the time at the start of the final turn)
    
    * `.winner`: <Player>
    * `.loser`: <Player>
    
    * `.lead_pokemon`: array `[ <lead1>, <lead2> ]` 
    * `.teams`: array `[ <teamDict1>, <teamDict2> ]`
        - Only contains the pokemon appearing 'during' the match (as read by parser)
    * `.teams_full`: `[<teamDict1>, <teamDict2>]`
    Logs
    ---------------------------------------
    * `.log`: the main text log
    * `.inputlog`: extra thing that contains the team seeds etc.
    
    * `.head`: everything before '|start'
    * `.bat`: everything in range `['|start', '|win|')`
    * `.tail` everything after `.bat`
    
    States
    ---------------------------------------
    * `.TURNS`: Array of turn-strings from splitting `.bat`. 
        * `.TURNS[i]` gives the raw string for Turn `i`
        * Note 'turn0' = fielding leading pokemon
    * `.STATES`: List of BattleStates (incl State_0).

`BattleState`:
---------------------------------------
    * `.time` : 'absolute' time turn occured at (seconds since *Epoch*)
    * `.turn`
    
    * `.team1`, 
    * `.team2`
    * `.time_elapsed` : seconds passed since `Battle.start_time`
    
    * `.battle_id` : copy of `Battle.id`; useful for printing errors.
    * `.print()` gives a nice printed summary.
'''


import json, copy, time
import re # regex

from copy import deepcopy
from dataclasses import dataclass
from math import prod, ceil


#################################################
# Dataclasses (Player, Team, Pokemon)
#################################################

# a `dataclass` is just a Class that only has attributes and no methods
# writing @dataclass lets you skip writing `__init__(...) : self.x = x` a bunch
@dataclass
class Player: 
    name: str
    side: int
    elo0: int # old
    elo1: int # new

class Team:
    def __init__(self, side: int, active: str, D: dict):
        self.side = side
        self.active = active
        self.D = D # team dictionary

    def __repr__(self):
        _out = "{" + f"side: {self.side}, active: {self.active}, D: <dict>" + "}"
        return _out

class Pokemon:
    def __init__(self, base, spec, lvl, hp, hp_max):
        self.base = base
        self.spec = spec
        self.lvl = int(lvl)
        self.hp = int(hp)
        self.hp_max = int(hp_max)

    def __repr__(self):
        _out = "{" + f"spec: {self.spec}, lvl: {self.lvl}, hp/max: {self.hp}/{self.hp_max}" + "}"
        return _out
    

class FullPokemon:
    """
    A class for storing all data (item, ability, moves, stats) about an individual Pokemon in a specific battle.

    Attributes
    -----------
    name : str
        The informal name of the pokemon.  Does not contain forme information
    speciesId: str
        The formal name of the pokemon, all lower case, no spaces or special characters.  Contains forme information.
    level : int
        The level of the pokemon
    moves : list[str]
        A list of strings (all lower case, no spaces or special characters) corresponding to the moves the Pokemon knows.
    ability : str
        The ability of the Pokemon.
    stats : dict of str : int
        A dictionary whose keys are hp, atk, def, spa, spd, spe, off and whose values are the corresponding stat for the Pokemon.
    types : list[str]
        A list of the one or two types the Pokemon has.
    item : str
        The item the pokemon is holding.
    """

    # An ordered list of Pokemon types.
    TYPE_ARRAY = [
        "NORMAL",
        "FIRE",
        "WATER",
        "ELECTRIC",
        "GRASS",
        "ICE",
        "FIGHTING",
        "POISON",
        "GROUND",
        "FLYING",
        "PSYCHIC",
        "BUG",
        "ROCK",
        "GHOST",
        "DRAGON",
        "DARK",
        "STEEL",
        "FAIRY",
        ]

    # An list of lists indicating the effectiveness of the offensive type (axis = 0) against the defensive type (axis = 1)
    TYPE_CHART = [
    # Normal
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.5, 0, 1, 1, 0.5, 1],
    # Fire
    [1, 0.5, 0.5, 1, 2, 2, 1, 1, 1, 1, 1, 2, 0.5, 1, 0.5, 1, 2, 1],
    # Water
    [1, 2, 0.5, 1, 0.5, 1, 1, 1, 2, 1, 1, 1, 2, 1, 0.5, 1, 1, 1],
    # Electric
    [1, 1, 2, 0.5, 0.5, 1, 1, 1, 0, 2, 1, 1, 1, 1, 0.5, 1, 1, 1],
    # Grass
    [1, 0.5, 2, 1, 0.5, 1, 1, 0.5, 2, 0.5, 1, 0.5, 2, 1, 0.5, 1, 0.5, 1],
    # Ice
    [1, 0.5, 0.5, 1, 2, 0.5, 1, 1, 2, 2, 1, 1, 1, 1, 2, 1, 0.5, 1],
    # Fighting
    [2, 1, 1, 1, 1, 2, 1, 0.5, 1, 0.5, 0.5, 0.5, 2, 0, 1, 2, 2, 0.5],
    # Poison
    [1, 1, 1, 1, 2, 1, 1, 0.5, 0.5, 1, 1, 1, 0.5, 0.5, 1, 1, 0, 2],
    # Ground
    [1, 2, 1, 2, 0.5, 1, 1, 2, 1, 0, 1, 0.5, 2, 1, 1, 1, 2, 1],
    # Flying
    [1, 1, 1, 0.5, 2, 1, 2, 1, 1, 1, 1, 2, 0.5, 1, 1, 1, 0.5, 1],
    # Psychic
    [1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 0.5, 1, 1, 1, 1, 0, 0.5, 1],
    # Bug
    [1, 0.5, 1, 1, 2, 1, 0.5, 0.5, 1, 0.5, 2, 1, 1, 0.5, 1, 2, 0.5, 0.5],
    # Rock
    [1, 2, 1, 1, 1, 2, 0.5, 1, 0.5, 2, 1, 2, 1, 1, 1, 1, 0.5, 1],
    # Ghost
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 2, 1, 0.5, 1, 1],
    # Dragon
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 0.5, 0],
    # Dark
    [1, 1, 1, 1, 1, 1, 0.5, 1, 1, 1, 2, 1, 1, 2, 1, 0.5, 1, 0.5],
    # Steel
    [1, 0.5, 0.5, 0.5, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 0.5, 2],
    # Fairy
    [1, 0.5, 1, 1, 1, 1, 2, 0.5, 1, 1, 1, 1, 1, 1, 2, 2, 0.5, 1],
    ]

    def __init__(self,info_dict : dict):
        """
        Parameters
        ----------
        info_dict : dict
            A dictionary formatted like the teams_full field in the files of the form battle_id.json.
        """

        self.name = info_dict["name"]
        self.speciesId = info_dict["speciesId"]
        self.level = int(info_dict["level"])
        self.moves = info_dict["moves"]
        self.ability = info_dict["ability"]
        self.stats = info_dict["stats"]
        self.types = info_dict["types"]
        self.item = info_dict["item"]
        self.correct_stats()
        self.stats["off"] = max(self.stats["atk"],self.stats["spa"]) # useful for comparing team total statistics

    def correct_stats(self) -> None:
        """Corrects stats for Palafin and Terapagos.  Should never be called outside of __init__."""

        # Uses Palafin-Hero's stats
        if self.name == "Palafin":
            self.stats = {
                "hp" : 281,
                "atk" : 291,
                "def" : 194,
                "spa" : 208,
                "spd" : 179,
                "spe" : 199
            }
        # Uses Terapagos-Terastal's stats
        elif self.name == "Terapagos":
            self.stats = {
                "hp" : 273,
                "atk" : 191,
                "def" : 214,
                "spa" : 206,
                "spd" : 214,
                "spe" : 175
            }

    @staticmethod
    def get_type_index(type:str) -> int:
        """Given a type represented by a string, returns the index of that type in TYPE_ARRAY.
        
        Parameters
        ----------
        type: str
            A string representation of the type you want the index of.  Can satisfy any capitalization convention.
            
        Returns
        -------
        int
            The index of the argument in TYPE_ARRAY."""
        
        return FullPokemon.TYPE_ARRAY.index(type.upper())

    @staticmethod
    def eff(t1: str, t2: str) -> float:
        """Is used to represtent the type chart.  Returns the damage multiplier if an attack of type t1 is used against a (monotype) Pokemon of type t2.
        
        Parameters
        ----------
        t1 : str
            A string representation of the type of the attack.
        t2 : str
            A string representation of the type of the Pokemon being attacked.
            
        Returns
        -------
        float
            The damage multiplier if an attack of type t1 is used against a (monotype) Pokemon of type t2."""
        
        return FullPokemon.TYPE_CHART[FullPokemon.get_type_index(t1)][FullPokemon.get_type_index(t2)]

    @staticmethod
    def type_multiplier(m1: "FullPokemon", m2: "FullPokemon") -> float:
        """Is used to approximate STAB * Type in the damage calculation where m1 uses its best (assumed) attack against m2.
        
        This method assumes that m1 is using its best STAB against m2.  In the case that m1's best STAB is at most 1/4 effective against m2,
        the method allows m1 to have a not-very-effective coverage move against m2.
        
        Parameters
        ----------
        m1: FullPokemon
            The attacking Pokemon.
        m2 : FullPokemon
            The defending Pokemon.
            
        Returns
        -------
        float
            An approximation of the STAB * Type multiplier for m1's best attack against m2."""
        
        stab_multiplier = 1.5
        if m1.ability == "Adaptability":
            stab_multiplier = 2
        if m1.ability == "Dragon's Maw":
            stab_multiplier *= 1.5
        if m1.ability == "Pixilate":
            stab_multiplier *=1.2
        if m1.ability == "Transistor":
            stab_multiplier *= 1.3
        if m1.ability == "Steely Spirit":
            stab_multiplier *= 1.5
        toReturn = stab_multiplier * max(prod(FullPokemon.eff(t1,t2) for t2 in m2.types) for t1 in m1.types)
        return max(1/2,toReturn)
    
    
    def stat_multiplier(self,stat:str) -> float:
        """Returns the multiplier to stat that self gets from its ability and held item.

        Note that this is *different* than a damage multiplier (e.g. from a Life Orb).

        Parameters
        ----------
        stat : str
            The string representation of the stat being multiplied.

        Returns
        -------
        float
            The multiplier that self gets to stat from its ability and held item.
        """

        return self.item_stat_multiplier(stat) * self.mon_stat_multiplier(stat)
    
    
    def mon_stat_multiplier(self,stat:str) -> float:
        """Returns the multiplier that this Pokemon gets to stat due to its ability.
        
        Parameters
        ----------
        stat : str
            The string representation of the stat being multiplied.
            
        Returns
        -------
        float
            The multiplier that self gets to stat from its ability."""
        
        if self.name == "Chien-Pao" and stat == 'atk': # This is coming from its ability Sword of Ruin.  I just would rather type Chien-Pao than Sword of Ruin (ditto for the other Ruin pokemon)
            return 4/3
        elif self.name == "Chi-Yu" and stat == 'spa':
            return 4/3
        elif self.name == "Wo-Chien" and stat == 'def':
            return 4/3
        elif self.name == "Ting-Lu" and stat == 'spd':
            return 4/3
        elif self.name == "Regigigas" and stat in ['atk','spe']:
            return 1/2
        elif self.ability == "Fur Coat" and stat == 'def':
            return 2
        elif self.ability in ["Huge Power", "Pure Power"] and stat == 'atk':
            return 2
        elif self.ability == "Hustle" and stat == 'atk':
            return 1.5 * 0.8
        elif self.ability in ["Guts","Toxic Boost"] and stat == 'atk':
            return 1.5
        else:
            return 1

    
    def item_stat_multiplier(self,stat:str) -> float:
        """Returns the multiplier that self gets to stat coming from its item.
        
        Does not include Life Orb because that is a damage multiplier, not a stat multiplier.
        
        Parameters
        ----------
        stat : str
            The string representation of the stat being multiplied.
        
        Returns
        -------
        float
            The multiplier that self gets to stat from its item."""
        
        if self.item == "Choice Band" and stat == 'atk':
            return 1.5
        elif self.item == "Choice Specs" and stat == 'spa':
            return 1.5
        elif self.item == "Choice Scarf" and stat == 'spe':
            return 1.5
        elif self.item == "Eviolite" and stat in ['def','spd']:
            return 1.5
        elif self.item == "Assault Vest" and stat == 'spd':
            return 1.5
        elif self.item == "Light Ball" and stat in ['atk','spa']:
            return 2
        else:
            return 1
        

    def damage_multiplier(self) -> float:
        """Returns the multiplier that self gets to the damage that it deals coming from its item.
        
        Returns
        -------
        float
            The multiplier that self gets to the damage that it deals coming from its item.
        """

        if self.item == "Life Orb":
            return 5324/4096
        elif self.item in ["Soul Dew","Adamant Orb","Griseous Orb","Lustrous Orb", "Hearthflame Mask", "Wellspring Mask", "Cornerstone Mask"]:
            return 4915/4096
        else:
            return 1
        
    
    @staticmethod
    def ditto_transform(m1: "FullPokemon", m2 : "FullPokemon") -> tuple["FullPokemon","FullPokemon"]:
        """Transforms Ditto into its opposing Pokemon.
        
        Note: I'm not sure the stats are quite right here.  Ditto definitely keeps its HP stat, but does it copy its opponent's stats, or does it copy
        its opponent's EVs/IVs?  I think it's the former, but am not certain.  I also think Ditto keeps its own level, but am least certain of this.
        
        Parameters
        ----------
        m1 : FullPokemon
            A pokemon that may be a Ditto.
        m2 : FullPokemon
            A pokemon that may be a Ditto.
            
        Returns
        -------
        tuple[FullPokemon,FullPokemon]
            A pair of FullPokemon where if mi is not a Ditto, then mi is returned unchanged in position i.  However, if mi is a Ditto, this returns 
            a copy of mj in place of mi, but with Ditto's level, HP stat, and item.
        """
        
        if m1.name == "Ditto":
            m1 = copy.deepcopy(m2)
            m1.stats["hp"] = 225
            m1.item = "Choice Scarf"
            m1.level = 87
        if m2.name == "Ditto":
            m2 = copy.deepcopy(m1)
            m2.stats["hp"] = 225
            m2.item = "Choice Scarf"
            m2.level = 87
        return m1,m2

    @staticmethod 
    def damage(m1 : "FullPokemon", m2 : "FullPokemon") -> float:
        """Returns an approximation of the average fraction of m2's maximum HP that m2 would lose if m1 used its best attack against m2.
        
        Here, 'best attack' means best 80 base power STAB attack in category self.stats['off'] with no secondary effects UNLESS such a STAB attack is no more
        than 1/4 effective against m2, in which case m1 uses a not-very-effective 80 base power coverage attack in category self.stats['off'].
        
        Makes assumptions that there are no weather effects nor abilities which alter damage other than those which directly affect statistics nor
        items which alter damage other than those documented in FullPokemon.damage_multiplier().
        
        Tends to run a bit large because the actual damage formula uses floor functions and this does not.
        
        Handles Ditto by first applying FullPokemon.ditto_transform(m1,m2).
        
        Parameters
        ----------
        m1 : FullPokemon
            The attacking Pokemon.
        m2 : FullPokemon
            The defending Pokemon.
            
        Returns
        -------
        float
            An approximation of the fraction of m2's maximum HP that m2 would lose if m1 used its best attack against m2.
        """

        # If we do turn-by-turn predictions, this can be modified to use m2's current HP rather than max HP
        # Transform Ditto into its opponent
        m1,m2 = FullPokemon.ditto_transform(m1,m2)
        # proceed as normal
        m1_off_stat = max(m1.stats['atk'],m1.stats['spa'])
        if m1_off_stat == m1.stats['atk']:
            m1_off_stat *= m1.stat_multiplier('atk')
            m2_def_stat = m2.stats['def'] * m2.stat_multiplier('def')
        else:
            m1_off_stat *= m1.stat_multiplier('spa')
            m2_def_stat = m2.stats['spd'] * m2.stat_multiplier('spd')
        type_mult = FullPokemon.type_multiplier(m1,m2)
        dam_mult = m1.damage_multiplier()
        return ((2*m1.level/5 + 2) * 80 * m1_off_stat / m2_def_stat / 50 + 2) * type_mult * dam_mult * 92.5 / 100 / m2.stats["hp"]
    
    @staticmethod
    def one_v_one_damage(m1: "FullPokemon", m2 : "FullPokemon") -> tuple[float,float]:
        """Returns a pair (d1,d2) where di is the fraction of mj's HP that it would lose in a one-on-one matchup against mi.

        Specifically, it assumes that each mon repeatedly uses its best attack (in the sense of FullPokemon.damage(m1,m2)) into the other 
        until there is a KO.

        Each di is a allowed to exceed 1 to indirectly account for things like screens and resistance berries.

        Parameters
        ----------
        m1 : FullPokemon
            A Pokemon
        m2 : FullPokemon
            A Pokemon
        
        Returns
        -------
        tuple[float,float]
            The pair (d1,d2) where di is the fraction of mj's HP that it would lose in a one-on-one matchup against mi.
        """

        # Transform Ditto into its opponent
        m1_ditto = (m1.name == "Ditto")
        m2_ditto = (m2.name == "Ditto")
        m1,m2 = FullPokemon.ditto_transform(m1,m2)

        # Compute one-turn damages
        m1_to_m2_damage = FullPokemon.damage(m1,m2)
        m2_to_m1_damage = FullPokemon.damage(m2,m1)

        # Compute the number of turns until there is a KO
        m1_ttko_m2 = ceil(1/min(1,m1_to_m2_damage))
        m2_ttko_m1 = ceil(1/min(1,m2_to_m1_damage))
        turn_of_ko = min(m1_ttko_m2,m2_ttko_m1)

        # Account for any stat changes to speed (only Choice Scarves for now)
        m1_spe = m1.stats["spe"] * m1.stat_multiplier("spe")
        m2_spe = m2.stats["spe"] * m2.stat_multiplier("spe")

        # handle the fact that Ditto only has 5 PP per move (and it is locked into one move because of the Scarf);
        # this is awkward, could be revisited
        if m1_ditto and turn_of_ko > 5:
            return (5 * m1_to_m2_damage, turn_of_ko * m2_to_m1_damage)
        elif m2_ditto and turn_of_ko > 5:
            return (turn_of_ko * m1_to_m2_damage, 5 * m2_to_m1_damage)
        
        # this is now the 'normal' case (when there either is no Ditto or toko <= 5)
        elif m1_spe > m2_spe and turn_of_ko == m1_ttko_m2: # if m1 is faster and KOs m2, m1 gets one more turn than m2
            return (turn_of_ko * m1_to_m2_damage,(turn_of_ko-1) * m2_to_m1_damage)
        elif m1_spe < m2_spe and turn_of_ko == m2_ttko_m1: # if m2 is faster and KOs m1, m2 gets one more turn than m1
            return ((turn_of_ko - 1) * m1_to_m2_damage, turn_of_ko * m2_to_m1_damage)
        else: # if the slower mon KOs the faster one, they take the same number of turns.  This also covers the case of a speed tie (could be revised).
            return (turn_of_ko * m1_to_m2_damage, turn_of_ko * m2_to_m1_damage)
    
    @staticmethod
    def advantage(m1: "FullPokemon", m2: "FullPokemon") -> float:
        """Returns the damage differential in a one-on-one matchup featuring m1 against m2.
        
        Symmetric about 0.  Additive.  Larger values indicate that m1 has a stronger advantage.
        
        Parameters
        ----------
        m1 : FullPokemon
            A Pokemon.
        m2 : FullPokemon
            A Pokemon.
            
        Returns
        -------
        float
            The damage differential in a one-v-one matchup featuring m1 against m2."""
        
        m1_to_m2_damage,m2_to_m1_damage = FullPokemon.one_v_one_damage(m1,m2)
        return m1_to_m2_damage - m2_to_m1_damage
    

    def is_trapper(self) -> bool:
        """Returns True if and only if self has an ability that prevents opponents from switching.
        
        Returns
        -------
        bool
            True if and only if self has an ability that prevents opponents from switching."""
        
        return self.ability in ["Arena Trap", "Shadow Tag", "Magnet Pull"]
    
    def is_type_changer(self) -> bool:
        """Returns True if and only if self has an ability that allows it to change types during battle.
        
        Returns
        -------
        bool
            True if and only if self has an ability that allows it to change types during battle."""
        
        return self.ability in ["Libero","Protean"]
    
    def is_weather_setter(self) -> bool:
        """Returns True if and only if self has an ability that sets a weather condition when it switches in.
        
        Returns
        -------
        bool
            True if and only if self has an ability that sets a weather condition when it switches in.
        """

        return self.ability in ["Drought", "Drizzle", "Snow Warning", "Sand Stream", "Orichalcum Pulse"]
    
    def is_terrain_setter(self) -> bool:
        """Returns True if and only if self has an ability that sets a terrain when it switches in.
        
        Returns
        -------
        bool    
            True if and only if self has an ability that sets a terrain when it switches in."""
        
        return self.ability in ["Electric Surge", "Grassy Surge", "Psychic Surge", "Misty Surge", "Hadron Engine", "Seed Sower"]
    
    def is_stat_drop_resistor(self) -> bool:
        """Returns True if self has one of the 'good' abilities that allows it to resist its stats being lowered by an opponent.
        
        Returns
        -------
        bool
            True if self has one of the 'good' abilities that allows it to resist its stats being lowered by an opponent."""
        
        return self.ability in ["Competitive", "Defiant", "Contrary",]#skipping only because these were not predictive: "Clear Body", "Hyper Cutter", "Inner Focus", "Oblivious", "Own Tempo", "Full Metal Body", "Guard Dog", "Scrappy"]
    
    def is_absorber(self) -> bool:
        """"Returns True if and only if self has an ability that grants self a benefit from being hit by attacks of a certain type.
        
        Returns
        -------
        bool
            True if and only if self has has an ability that grants self a benefit from being hit by attacks of a certain type."""
        
        return self.ability in ["Dry Skin", "Water Absorb", "Volt Absorb", "Earth Eater", "Flash Fire", "Lightning Rod", "Sap Sipper", "Storm Drain", "Well-Baked Body", "Motor Drive"]
    
    def has_extra_immunities(self) -> bool:
        """Returns True if and only if self has an ability that grants it an immunity to certain moves that it would not otherwise have.
        
        Returns
        -------
        bool
            True if and only if self has an ability that grants it an immunity to certain moves that it would not otherwise have."""
            
        return self.is_absorber() or self.ability in ["Levitate","Bulletproof","Soundproof","Wind Rider"]
    
    def is_status_resistor(self) -> bool:
        """Returns True if self has one of the 'good' abilities that allow it to resist status conditions or moves.
        
        Returns
        -------
        bool
            True if self has one of the 'good' abilities that allow it to resist status conditions or moves."""
        
        return self.ability in ["Good as Gold", "Purifying Salt", "Magic Bounce", "Poison Heal", "Guts", "Toxic Boost",]# skipping: "Comatose", "Insomnia", "Quick Feet", "Sweet Veil", "Vital Spirit", "Water Veil"
    
    def is_contact_punisher(self) -> bool:
        """Returns True if self has one of the 'good' abilities or items that allow it to punish opponents' contact moves.
        
        Returns
        -------
        bool
            True if self has one of the 'good' abilities or items that allow it to punish opponents' contact moves."""
        
        return self.ability in ["Flame Body", "Static", "Rough Skin", "Effect Spore", "Gooey"] or self.item in ["Rocky Helmet"] # skipping "Tangling Hair" as that's only on Dugtrio-A
    
    def is_ability_ignorer(self) -> bool:
        """Returns True if and only if self has an ability that allows it to ignore its opponent's ability in some capacity.
        
        Returns
        -------
        bool
            True if and only if self has an ability that allows it to ignore its opponent's ability in some capacity."""
        
        return self.ability in ["Mold Breaker", "Teravolt", "Turboblaze", "Neutralizing Gas"]
    
    def is_weather_booster(self) -> bool:
        """Returns True if and only if self has an ability that boosts its stats in weather.
        
        Returns
        -------
        bool
            True if and only if self has an ability that boosts its stats in weather."""
        return self.ability in ["Chlorophyll","Slush Rush","Swift Swim","Sand Rush","Solar Power"]
    
    def has_boosting_ability(self) -> bool:
        """Returns True if and only if self has an ability that allow it to boost its stats or damage dealt under certain circumstances.
        
        These are generally abilities that are hard to bake into the advantage stat, so we treat them categorically instead.
        
        Returns
        -------
        bool
            True if and only if self has an ability that allow it to boost its stats or damage dealt under certain circumstances."""
        
        return self.ability in [
            "Galvanize",
            "Ice Scales",
            "Compound Eyes",
            "Speed Boost",
            "Quick Feet",
            "Sheer Force",
            "Sharpness",
            "Strong Jaw",
            "Tough Claws",
            "Iron Fist",
            "Mega Launcher",
            "Punk Rock",
            "Reckless",
            "Rocky Payload",
            "Technician",
            "Thick Fat",
            "Tinted Lens",
            "Weak Armor",
            "Unburden",
            "Protosynthesis",
            "Quark Drive",
            "Analytic",
            "Anger Shell",
            "Berserk",
            "As One",
            "Chilling Neigh",
            "Grim Neigh",
            "Moxie",
            "Battle Bond",
            "Blaze",
            "Torrent",
            "Overgrow",
            "Dauntless Shield",
            "Intrepid Sword",
            "Filter",
            "Prism Armor",
            "Rattled",
            "Shields Down",
            "Ice Face",
            "Solid Rock",
            "Soul-Heart",
            "Stamina",
            "Supreme Overlord",
            "Surge Surfer",
            "Thermal Exchange",
            "Well-Baked Body",
            "Wind Power",
            "Wind Rider"
        ] or self.is_weather_setter() or self.is_terrain_setter() or self.is_stat_drop_resistor() or self.is_weather_booster()
    
    def has_omni_boost(self) -> bool:
        """Returns True if and only if self has a move that boosts all of its stats.
        
        Returns
        -------
        bool
            True if and only if self has a move that boosts all of its stats."""
        
        return any(move in ["clangoroussoul","noretreat"] for move in self.moves)
    
    def has_off_def_spe_boost(self) -> bool:
        """Returns True if and only if self has a move that boosts its offensive stat, speed, and a defensive stat.
        
        Returns
        -------
        bool
            True if and only if self has a move that boosts its offensive stat, speed, and a defensive stat."""
        
        return any(move in ["quiverdance","victorydance"] for move in self.moves) or self.has_omni_boost()
    
    def has_off_spe_boost(self) -> bool:
        """Returns True if and only if self has a move that boosts its offensive stat and its speed.
        
        Returns
        -------
        bool
            True if and only if self has a move that boosts its offensive stat and its speed."""
        
        return any(move in ["dragondance", "tidyup", "shellsmash", "filletaway", "shiftgear"] for move in self.moves) or self.has_off_def_spe_boost()
    
    def has_off_def_boost(self) -> bool:
        """Returns True if and only if self has a move that boosts its offensive stat and a defensive stat.
        
        Returns
        -------
        bool
            True if and only if self has a move that boosts its offensive stat and a defensive stat."""
        
        return any(move in ["calmmind", "bulkup", "curse", "coil", "takeheart"] for move in self.moves) or self.has_off_def_spe_boost()
    
    def has_off_boost(self) -> bool:
        """Returns True if and only if self has a move that boosts its offensive stat.
        
        Returns
        -------
        bool
            True if and only if self has a move that boosts its offensive stat."""
        
        return any(move in ["swordsdance", "nastyplot", "bellydrum", "growth", "honeclaws", "howl", "workup", "tailglow", "torchsong"] for move in self.moves) or self.has_off_def_boost() or self.has_off_spe_boost()
    
    def has_spe_boost(self) -> bool:
        """Returns True if and only if self has a move that boosts its speed stat.
        
        Returns
        -------
        bool
            True if and only if self has a move that boosts its speed stat."""
        
        return any(move in ["agility", "rockpolish", "aquastep", "aurawheel", "esperwing", "flamecharge", "rapidspin", "scaleshot", "trailblaze"] for move in self.moves) or self.has_off_spe_boost()
    
    def has_def_boost(self) -> bool:
        """Returns True if and only if self has a move that boosts a defensive stat.
        
        Returns
        -------
        bool
            True if and only if self has a move that boosts a defensive stat."""
        
        return any(move in ["irondefense", "acidarmor", "cosmicpower"] for move in self.moves) or self.has_off_def_boost()
    
    def has_boost_move(self) -> bool:
        """Returns True if and only if self has a move that boosts one of its stats.
        
        Returns
        -------
        bool
            True if and only if self has a move that boosts one of its stats."""
        
        return self.has_off_boost() or self.has_spe_boost() or self.has_def_boost()

    




# -----------------------------
# Extra functions to help with printing teams

def team_str(team: dict):
    _out = ""
    for poke in team.keys():
        _out += f" > {poke}: {str(team[poke])}\n"
    return _out

def team_full_str(team_full: dict):
    _out = ""
    for poke in team_full.keys() :
        poke_entry = team_full[poke]
        dict_to_show = {key : poke_entry[key] for key in ['species', 'level']}
        dict_to_show['hp'] = poke_entry['stats']['hp']
        _out += f" > {poke}: {dict_to_show}\n"
    return _out
        



#################################################
# Battle
#################################################
class Battle:
    '''
    Battle(file_name, verbose=False)
    '''
    def __init__(self,file_name, parse=False, verbose=False):
        with open(file_name,"r") as battle_json:
            data = json.load(battle_json)
        # -----------------------------
        # Initializing metadata/attributes
        self.id = data.get('id', '')
        self.format = data.get('format', '')
        self.formatid = data.get('formatid', '')
        
        self.rating = data.get('rating', None)
        self.rated = (self.rating != None)
        
        # self.time_list = [] # times can be wrapped into different Turn/State classes
        self.start_time = data.get('start_time', 0)
        self.end_time = data.get('end_time', 0)
        self.match_time = data.get('match_time', 0)

        self.winner = data.get('winner', "")
        self.loser = data.get('loser', "")

        self.players = data.get('players', [])
        self.player_dets = data.get('player_dets', []) # more info about players... may be redudant with self.p1, self.p2
        self.teams_full = data.get('teams_full', []) # full teams including stats

        self.lead_pokemon = data.get('lead_pokemon', [])
        self.STATES = data.get('STATES', [])

        self.gametype = data.get('gametype', '')
        self.custom_ruleQ = data.get('custom_ruleQ', None)

        self.inputlog = data.get("inputlog")
        self.log = data.get("log")

        # -----------------------------
        if parse : 
            
            # log setup
            self.log = re.sub(r'\n\|\n', '\n', self.log) # delete any lines that are only `|`
    
            # `head` takes 'START'->'|start', `tail` takes '|win|'->'END', and `bat` is what's in-between.
            self.head, self.bat, self.tail = self._head_sep(self.log)
    
            # -----------------------------
            # processing `head`
            self.gametype = self._init_gametype(self.head)
            self.custom_ruleQ = (re.search(r'custom rule', self.head) != None)
            
            self.start_time = self._init_time(self.head)
            
            try:
                self.p1, self.p2 = self._init_players(self.head)
            except:
                print(f"error in parsing `players` of battle {self.id}")
    
            # -----------------------------
            # processing `bat`
            self.bat = re.sub(r'\|start\n', '|turn|0\n', self.bat)
            self.TURNS = re.split(r'\|turn\|', self.bat)[1:] # discard initial ''
            
            # initialize/parse starting state ("turn 0")
            
            # Need to allow for Zoroark weirdness:
            if 'Zoroark' in self.teams_full[0].keys() :
                poke = self.teams_full[0]['Zoroark']
                D0_0 = {poke['name'] : Pokemon(poke['name'], poke['species'], poke['level'], poke['stats']['hp'], poke['stats']['hp'])}
            else : D0_0 = {}
            if 'Zoroark' in self.teams_full[1].keys() :
                poke = self.teams_full[1]['Zoroark']
                D1_0 = {poke['name'] : Pokemon(poke['name'], poke['species'], poke['level'], poke['stats']['hp'], poke['stats']['hp'])}
            else : D1_0 = {}
            
            BS_0 = BattleState(
                Team(side=1, active='', D=D0_0),
                Team(side=2, active='', D=D1_0), 
                self.TURNS[0],
                battle_id = self.id
            )
            BS_0.time = self.start_time # turn 0 time is match start
            
            self.STATES = [BS_0]
            for i in range(len(self.TURNS)-1): # -1 b/c I use `i+1` below
                BS_i = self.STATES[i]
                BS_new = BattleState(
                    copy.deepcopy(BS_i.team1), # can't leave out the deepcopy!
                    copy.deepcopy(BS_i.team2), # can't leave out the deepcopy!
                    self.TURNS[i+1],
                    match_start_time = self.start_time,
                    battle_id = self.id
                )
                self.STATES.append(BS_new)
                if verbose : 
                    BS_new.print()
    
            # [<starter>]
            self.lead_pokemon = [
                BS_0.team1.active, 
                BS_0.team2.active
            ] 
    
            # -----------------------------
            # processing `tail`
            self.parse_tail(self.tail)
    
            self.end_time = self.STATES[-1].time
            if self.end_time == 0 : self.end_time = self.STATES[-2].time
            
            self.teams = [
                self.clean_team(self.STATES[-1].team1.D), 
                self.clean_team(self.STATES[-1].team2.D)
            ] # [<{team_set}>]

    # =================================
    # END __init__()


    # =================================
    def __repr__(self):
        to_return = f"%%%%%%%%%%   Battle {self.id}   %%%%%%%%%%\n"; 
        to_return += f"============================================================\n";
        
        if self.rated:
            to_return += f"This was a battle between {self.p1.name} (pre-match rating {self.p1.elo0}) "
            to_return += f"and {self.p2.name} (pre-match rating {self.p2.elo0}).\n\n"
        else:
            to_return += f"This was a battle between {self.p1.name} and {self.p2.name}.\n\n"
        
        to_return += f"{self.p1.name}'s lead pokemon was {self.lead_pokemon[0]}, "
        to_return += f"and their team (by `base`) was\n{team_full_str(self.teams_full[0])}\n"
        to_return += f"{self.p2.name}'s lead pokemon was {self.lead_pokemon[1]}, "
        to_return += f"and their team (by `base`) was\n{team_full_str(self.teams_full[1])}\n"
        
        to_return += f"{self.winner.name} won!\n"
        if self.rated:
            to_return += f"{self.winner.name}'s rating increased to {self.winner.elo1}.\n"
            to_return += f"{self.loser.name}'s rating fell to {self.loser.elo1}.\n"
        else:
            to_return += "This was an unrated match, so no one's rating changed.\n"
        
        to_return += f"%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\n"
        return to_return

        
    # These are meant to be run only in __init__
    # =================================
    def _head_sep(self, log): # separate log into 'header' and 'battle'
        head_end = log.index('|start\n')
        bat_end = log.index('\n|win|') + 1 # in case string `|win|` appears elsewhere
        return log[:head_end], log[head_end:bat_end], log[bat_end:]

    def _init_time(self, head):
        secs = re.search(r'\|t:\|(\d+)$', head, re.M).group(1)
        return int(secs) # returns a `time.tm` object
    
    def _init_gametype(self, head):
        return re.search(r'\|gametype\|(\w*)$', head, re.M).group(1)
    
    def _init_players(self, head):
        # test: |player|p1|kaisarian|lucas-gen4pt|
        # test: |player|p2|Flamesenpai557|101|
        player_pat = re.compile(r'\|player\|p(?P<side>\d)\|(?P<name>.*)\|(.*)\|(?P<elo>\d+)?\n'); # player line pattern

        p1 = player_pat.search(head)
        search_ind = p1.end() # advance the search beginning
        p2 = player_pat.search(head, pos=search_ind)

        # if battle unrated then elo is 'None'; we set to 0
        if p1.group('elo') == None : p1_elo = 0
        else : p1_elo = p1.group('elo') 
        
        if p2.group('elo') == None : p2_elo = 0
        else : p2_elo = p2.group('elo')
            
        player1 = Player(
            name = p1.group('name'), 
            side = int(p1.group('side')),
            elo0 = int(p1_elo),
            elo1 = int(p1_elo), # set equal for now
        )
        player2 = Player(
            name = p2.group('name'), 
            side = int(p2.group('side')),
            elo0 = int(p2_elo),
            elo1 = int(p2_elo), # set equal for now
        )
        
        return player1, player2

        
    # =================================
    def parse_tail(self, tail):
        match = re.match(r'\|win\|(.*)?\n', tail)

        try:
            win_name = match.group(1)
        except AttributeError as e:
            print("Error parsing |win| line.")
            return None
        
        if win_name == self.p1.name : 
            self.winner = self.p1
        else: 
            self.winner = self.p2

        if self.winner.side == 1 : 
            self.loser = self.p2
        else:
            self.loser = self.p1

        # parse Elo changes by finding deltas +/-, then applying
        if self.rated : 
            match_lose = re.search(r'\|raw\|(?:.*?)\([-+](?P<EloLoss>\d+) for losing\)\n', tail)
            match_win = re.search(r'\|raw\|(?:.*?)\([-\+](?P<EloGain>\d+) for winning\)\n', tail)
    
            try:
                elo_loss = int(match_lose.group('EloLoss'))
                self.loser.elo1 -= elo_loss # detract points
            except AttributeError as e:
                print("Error parsing Elo for loser "+f"(id:{self.id})")
            try: 
                elo_gain = int(match_win.group('EloGain'))
                self.winner.elo1 += elo_gain
            except AttributeError as e:
                print("Error parsing Elo for winner "+f"(id:{self.id})")

        return None

    
    # =================================
    # in essence this just resets all team HP's to max for printing purposes
    def clean_team(self, teamD: dict):
        if teamD == {} : 
            print("Need to pass a nonempty Team object.")
            return None
            
        _team = copy.deepcopy(teamD)
        for form in _team.keys():
            _team[form].hp = _team[form].hp_max
        return _team
        


#################################################
# BattleState class
#################################################

class BattleState:
    # feed current teams and turn string, plus optional battle start_time and id (for debugging)
    def __init__(self, team1, team2, turn: str, match_start_time = 0, battle_id = ''): 
        self.turn = int(re.match(r'(\d+)\n', turn).group(1)) # split turn-strings start with `#\n`
        
        # update self.time if a timestamp appears in `turn`
        self.time = 0
        t_match = re.search(r'\|t:\|(\d+)\n', turn)
        if t_match != None :
            self.time = int(t_match.group(1))
        
        self.team1 = team1 
        self.team2 = team2 
        
        self.elapsed_time = self.time - match_start_time
        self.battle_id = battle_id
        
        self.parse_turn(turn) # main builder

    # =================================
    def __repr__(self):
        return f"<BattleState;turn{self.turn}>"

    # =================================
    # Separating this from __repr__ makes looking at arrays of BattleStates easier
    def print(self):
        _out = ""
        _out += f"State at END of Turn {self.turn}: \n"
        _out += f"  Match time: {time.strftime('%M:%S',time.gmtime(self.elapsed_time))} (mm:ss)\n"
        _out += f"  Team: {self.team1}\n"
        _out += f"  Team: {self.team2}\n"
        print(_out)

    
    # =================================
    # Line Parsers 
    # =================================
    # These accept only single lines
    
    def parse_switch(self, s: str):
        # test string: '|switch|p1a: Delphox|Delphox, L84, F|263/263'
        match = re.match(r"\|switch\|p(?P<plr>\d)a?: (?P<base>[\w'\- ]+)\|(?P<forme>[\w'\- ]+), (?P<lvl>L\d+)?(?:.*?)\|(?P<hp>\d+)/(?P<hpmax>\d+)(?:.*?)$", s, re.M)
        D = match.groupdict() # dictionary of captured 'groups'; for brevity
        
        player = int(D['plr'])
        base = D['base']
        forme = D['forme']
        hp = int(D['hp'])
        hpmax = int(D['hpmax'])

        # level 100 pokemon do not have a listed `level` in the log
        if D['lvl'] == None : lvl = 100
        else : lvl = int(D['lvl'][1:])

        if player == 1:
            poke = Pokemon(base, forme, lvl, hp, hpmax)
            self.team1.D[base] = poke
            self.team1.active = forme
        else: 
            poke = Pokemon(base, forme, lvl, hp, hpmax)
            self.team2.D[base] = poke
            self.team2.active = forme
        return None

    # =================================
    def parse_drag(self, s: str):
        # test string: '|drag|p1a: Delphox|Delphox, L84, F|263/263'
        match = re.match(r"\|drag\|p(?P<plr>\d)a?: (?P<base>[\w\- ]+)\|(?P<forme>[\w'\- ]+), (?P<lvl>L\d+)?(?:.*?)\|(?P<hp>\d+)/(?P<hpmax>\d+)(?:.*?)$", s, re.M)
        D = match.groupdict() # dictionary of captured 'groups'; for brevity
        
        player = int(D['plr'])
        base = D['base']
        forme = D['forme']
        hp = int(D['hp'])
        hpmax = int(D['hpmax'])

        # level 100 pokemon do not have a listed `level` in the log
        if D['lvl'] == None : lvl = 100
        else : lvl = int(D['lvl'][1:]) # [1:] to map 'L##' |-> '##'
        
        if player == 1:
            poke = Pokemon(base, forme, lvl, hp, hpmax)
            self.team1.D[base] = poke
            self.team1.active = forme
        else: 
            poke = Pokemon(base, forme, lvl, hp, hpmax)
            self.team2.D[base] = poke
            self.team2.active = forme
        return None
    
    # =================================
    def parse_damage(self, s: str):
        # test strings
        # S1 = '|-damage|p2a: Snorlax|291/397|[from] item: Rocky Helmet|[of] p1a: Skarmory'
        # S2 = '|-damage|p1a: Wugtrio|0 fnt'
            
        # most damage lines look like this
        match = re.match(r"\|-damage\|p(?P<plr>\d)a?: (?P<base>[\w'\- ]+)\|(?P<hp>\d+)/(?P<hpmax>\d+).*$", s, re.M)
        if match == None :
            # could be a 'fainting line'
            match = re.match(r"\|-damage\|p(?P<plr>\d)a?: (?P<base>[\w'\- ]+)\|(?P<hp>\d+) fnt(?:.*?)$", s, re.M)
    
        # if neither work, stop
        if match == None : 
            print("Could not parse line:\n%s" % s)
            return None
            
        D = match.groupdict() # for brevity
        
        player = int(D['plr'])
        base = D['base']
        hp = int(D['hp'])
        
        if player == 1 : 
            poke = self.team1.D[base]
            poke.hp = hp
            if D.get('hpmax') != None : poke.hp_max = int(D['hpmax'])
        else:
            poke = self.team2.D[base]
            poke.hp = hp
            if D.get('hpmax') != None : poke.hp_max = int(D['hpmax'])
        return None

    # =================================
    def parse_heal(self, s: str):
        # test strings
        # S1 = '|-heal|p1a: Skarmory|169/235'
        # S2 = '|-heal|p2a: Wigglytuff|423/424|[from] item: Leftovers'
        
        match = re.match(r"\|-heal\|p(?P<plr>\d)a?:\s(?P<base>[\w'\- ]+)\|(?P<hp>\d+)/(?P<hpmax>\d+).*$", s, re.M)
        D = match.groupdict() # for brevity
        
        player = int(D['plr'])
        base = D['base']
        hp = D['hp']
        
        if player == 1 : 
            poke = self.team1.D[base]
            poke.hp = hp
            if D.get('hpmax') != None : poke.hp_max = int(D['hpmax'])
        else:
            poke = self.team2.D[base]
            poke.hp = hp
            if D.get('hpmax') != None : poke.hp_max = int(D['hpmax'])
        return None

    # =================================
    # Main Parser
    # =================================
    def parse_turn(self, turn: str):
        for line in turn.split('\n'): 
            try:
                if line.startswith('|switch|') : self.parse_switch(line)
                elif line.startswith('|drag|') : self.parse_drag(line)
                elif line.startswith('|-damage|') : self.parse_damage(line)
                elif line.startswith('|-heal|') : self.parse_heal(line)
            except:
                print("Could not parse turn %d, line: %s (id:%s)" % (self.turn, line, self.battle_id))
                continue