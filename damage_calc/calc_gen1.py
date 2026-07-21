import math
from typing import List
from .pokemon import Pokemon
from .move import Move
from .field import Field
from .result import Result
from .util import get_type_effectiveness

# In Gen 1-3, category is strictly determined by the move's typing.
SPECIAL_TYPES = ["Fire", "Water", "Grass", "Electric", "Ice", "Psychic", "Dragon"]

def calculate_gen1(attacker: Pokemon, defender: Pokemon, move: Move, field: Field) -> Result:
    # 0. Fixed Damage
    if move.name in ["Seismic Toss", "Night Shade"]:
        return Result(1, attacker, defender, move, field, [attacker.level] * 39)
        
    # Determine Category based on Gen 1 Type rules
    is_special = move.type in SPECIAL_TYPES
    
    # 1. Base Power & Stats
    base_power = move.base_power
    
    # In Gen 1, SpA and SpD are identical (represented by 'spa' in our normalized data)
    atk_stat = attacker.raw_stats.spa if is_special else attacker.raw_stats.atk
    def_stat = defender.raw_stats.spa if is_special else defender.raw_stats.def_
    
    # Apply boosts (Gen 1 doesn't chain mods, it just modifies the raw stat directly)
    atk_boost = attacker.boosts.spa if is_special else attacker.boosts.atk
    def_boost = defender.boosts.spa if is_special else defender.boosts.def_
    
    # Gen 1 Critical hits ignore all stat modifications
    if move.is_crit:
        atk_boost = 0
        def_boost = 0
        # Crits double the attacker's level in the formula
        effective_level = attacker.level * 2
    else:
        effective_level = attacker.level
        
    def get_gen1_boost(stat: int, boost: int) -> int:
        if boost >= 0:
            return math.floor(stat * ((2 + boost) / 2))
        return math.floor(stat * (2 / (2 - boost)))
        
    effective_atk = get_gen1_boost(atk_stat, atk_boost)
    effective_def = get_gen1_boost(def_stat, def_boost)
    
    # Gen 1 stat cap
    effective_atk = min(effective_atk, 999)
    effective_def = min(effective_def, 999)

    # 2. Base Damage Calculation
    # If defense is 0 (due to overflow glitches in the original games), default to 1
    effective_def = max(1, effective_def)
    
    level_calc = math.floor((2 * effective_level) / 5) + 2
    base_damage = math.floor((level_calc * base_power * effective_atk) / effective_def)
    base_damage = math.floor(base_damage / 50) + 2
    
    # 3. STAB & Type Effectiveness
    if move.type in attacker.types:
        base_damage = math.floor(base_damage * 1.5)
        
    type_mod = 1.0
    for def_type in defender.types:
        type_mod *= get_type_effectiveness(1, move.type, def_type)
        
    base_damage = math.floor(base_damage * type_mod)
    
    # 4. The 39 Damage Rolls (Gen 1 uses math.floor(Damage * R / 255) where R is 217 to 255)
    damage_rolls: List[int] = []
    
    if type_mod > 0:
        for r in range(217, 256):
            roll_damage = math.floor((base_damage * r) / 255)
            # Gen 1 has a quirk where damage cannot be 0 if the move lands and is not immune
            damage_rolls.append(max(1, roll_damage))
    
    return Result(1, attacker, defender, move, field, damage_rolls)