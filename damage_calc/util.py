import math
from typing import List
from . import data

def poke_round(num: float) -> int:
    """
    Standard Pokémon rounding rule:
    If the fractional part is exactly 0.5, it rounds DOWN.
    Otherwise, it rounds to the nearest integer.
    """
    return math.ceil(num) if (num % 1) > 0.5 else math.floor(num)

def chain_mods(mods: List[int]) -> int:
    """
    Chains a list of 4096-based multipliers.
    The game uses base-4096 math to avoid floating point errors.
    """
    m = 0x1000  # 4096 in hex (represents 1.0)
    for mod in mods:
        if mod != 0x1000:
            # Shift right by 12 is equivalent to floor division by 4096
            m = (m * mod + 0x800) >> 12
    return m

def get_type_effectiveness(gen: int, attack_type: str, defense_type: str) -> float:
    """
    Queries the JSON type chart to get the effectiveness multiplier (0.0, 0.5, 1.0, 2.0).
    Handles @smogon/calc's 'effectiveness' map and case-insensitivity cleanly.
    """
    if not attack_type or not defense_type or attack_type == "None" or defense_type == "None":
        return 1.0
        
    type_data = data.load_data(gen, "types")
    if not type_data:
        return 1.0

    # Case-insensitive helper function
    def find_key(d: dict, key: str):
        if key in d:
            return d[key]
        for k, v in d.items():
            if k.lower() == key.lower():
                return v
        return None

    atk_obj = find_key(type_data, attack_type)
    def_obj = find_key(type_data, defense_type)

    # 1. Check Attacker's 'effectiveness' map (Standard @smogon/calc structure)
    # Example: types["Fairy"]["effectiveness"]["Dark"] -> 2
    if isinstance(atk_obj, dict):
        eff_map = atk_obj.get("effectiveness")
        if isinstance(eff_map, dict):
            val = find_key(eff_map, defense_type)
            if val is not None:
                return float(val)

    # 2. Check Defender's 'effectiveness' map (Reverse lookup fallback)
    if isinstance(def_obj, dict):
        eff_map = def_obj.get("effectiveness")
        if isinstance(eff_map, dict):
            val = find_key(eff_map, attack_type)
            if val is not None:
                return float(val)

    # 3. Check Defender's 'damageTaken' map (Showdown code fallback: 1=2x, 2=0.5x, 3=0x)
    if isinstance(def_obj, dict):
        dt_map = def_obj.get("damageTaken")
        if isinstance(dt_map, dict):
            code = find_key(dt_map, attack_type)
            if code == 1:
                return 2.0
            elif code == 2:
                return 0.5
            elif code == 3:
                return 0.0

    return 1.0