import math
from typing import List
from .pokemon import Pokemon
from .move import Move
from .field import Field
from .result import Result
from .util import poke_round, chain_mods, get_type_effectiveness

def calculate_base_power(attacker: Pokemon, defender: Pokemon, move: Move, field: Field) -> int:
    """Calculates the effective base power of a move after all modifiers."""
    bp = move.base_power
    bp_mods: List[int] = []
    
    # 1. Move-Specific Overrides (e.g., Facade, Knock Off, Brine)
    if move.name == "Facade" and attacker.status in ["brn", "par", "psn", "tox"]:
        bp *= 2
    elif move.name == "Brine" and defender.cur_hp <= defender.max_hp / 2:
        bp *= 2
    elif move.name == "Knock Off" and defender.item is not None:
        bp = math.floor(bp * 1.5)
        
    # 2. Attacker Abilities
    if attacker.ability == "Technician" and bp <= 60:
        bp_mods.append(0x1800)  # 1.5x
    elif attacker.ability == "Strong Jaw" and move.flags.get("bite"):
        bp_mods.append(0x1800)  # 1.5x
    elif attacker.ability == "Iron Fist" and move.flags.get("punch"):
        bp_mods.append(0x1333)  # 1.2x
    elif attacker.ability == "Sharpness" and move.flags.get("slicing"):
        bp_mods.append(0x1800)  # 1.5x
    elif attacker.ability == "Punk Rock" and move.flags.get("sound"):
        bp_mods.append(0x14CD)  # 1.3x
        
    # 3. Defender Abilities
    if defender.ability == "Heatproof" and move.type == "Fire":
        bp_mods.append(0x800)   # 0.5x
    elif defender.ability == "Dry Skin" and move.type == "Fire":
        bp_mods.append(0x1400)  # 1.25x
        
    # 4. Attacker Items
    type_enhancing_items = {
        "Charcoal": "Fire", "Mystic Water": "Water", "Magnet": "Electric",
        "Miracle Seed": "Grass", "Never-Melt Ice": "Ice", "Black Belt": "Fighting",
        "Poison Barb": "Poison", "Soft Sand": "Ground", "Sharp Beak": "Flying",
        "Twisted Spoon": "Psychic", "Silver Powder": "Bug", "Hard Stone": "Rock",
        "Spell Tag": "Ghost", "Dragon Fang": "Dragon", "Black Glasses": "Dark",
        "Metal Coat": "Steel", "Silk Scarf": "Normal", "Fairy Feather": "Fairy"
    }
    
    if attacker.item == "Muscle Band" and move.category == "Physical":
        bp_mods.append(0x1199)  # 1.1x
    elif attacker.item == "Wise Glasses" and move.category == "Special":
        bp_mods.append(0x1199)  # 1.1x
    elif attacker.item == "Punching Glove" and move.flags.get("punch"):
        bp_mods.append(0x1199)  # 1.1x
    elif attacker.item in type_enhancing_items and move.type == type_enhancing_items[attacker.item]:
        bp_mods.append(0x1333)  # 1.2x
        
    # 5. Field and Terrain 
    # (Assuming grounded targets for simplicity, but we can expand this to check Flying types/Levitate later)
    if field.terrain == "Electric" and move.type == "Electric":
        bp_mods.append(0x14CD)  # 1.3x
    elif field.terrain == "Grassy" and move.type == "Grass":
        bp_mods.append(0x14CD)  # 1.3x
    elif field.terrain == "Psychic" and move.type == "Psychic":
        bp_mods.append(0x14CD)  # 1.3x
    elif field.terrain == "Misty" and move.type == "Dragon":
        bp_mods.append(0x800)   # 0.5x
        
    # Calculate the final modified base power using the 4096-chain
    final_bp = poke_round((bp * chain_mods(bp_mods)) / 4096)
    
    # A move's Base Power cannot drop below 1 in Generation 9
    return max(1, final_bp)





def calculate_effective_attack(attacker: Pokemon, defender: Pokemon, move: Move, field: Field, use_physical: bool) -> int:
    """Calculates effective attack stat including stage boosts, items, and abilities."""
    raw_atk = attacker.raw_stats.atk if use_physical else attacker.raw_stats.spa
    atk_boost = attacker.boosts.atk if use_physical else attacker.boosts.spa
    
    # Critical hits ignore negative attack drops
    if move.is_crit and atk_boost < 0:
        atk_boost = 0
        
    # Apply stage boost
    stat = poke_round(raw_atk * get_stat_boost_multiplier(atk_boost))
    
    atk_mods: List[int] = []
    
    # 1. Attacker Abilities
    if use_physical:
        if attacker.ability in ["Huge Power", "Pure Power"]:
            atk_mods.append(0x2000)  # 2.0x
        elif attacker.ability == "Hustle":
            atk_mods.append(0x1800)  # 1.5x
        elif attacker.ability == "Guts" and attacker.status:
            atk_mods.append(0x1800)  # 1.5x
    else:
        # Special Attack abilities
        if attacker.ability == "Solar Power" and field.weather == "Sun":
            atk_mods.append(0x1800)  # 1.5x
            
    # Generation 9: Protosynthesis / Quark Drive (Assuming the stat is the highest for simplicity)
    if attacker.ability == "Protosynthesis" and field.weather == "Sun":
        atk_mods.append(0x14CD)  # 1.3x
    elif attacker.ability == "Quark Drive" and field.terrain == "Electric":
        atk_mods.append(0x14CD)  # 1.3x

    # 2. Defender Abilities (Generation 9 Ruin Abilities debuff the attacker)
    if defender.ability == "Tablets of Ruin" and use_physical and attacker.ability != "Tablets of Ruin":
        atk_mods.append(0x0C00)  # 0.75x
    elif defender.ability == "Vessel of Ruin" and not use_physical and attacker.ability != "Vessel of Ruin":
        atk_mods.append(0x0C00)  # 0.75x

    # 3. Attacker Items
    if attacker.item == "Choice Band" and use_physical:
        atk_mods.append(0x1800)  # 1.5x
    elif attacker.item == "Choice Specs" and not use_physical:
        atk_mods.append(0x1800)  # 1.5x
    elif attacker.item == "Light Ball" and attacker.name == "Pikachu":
        atk_mods.append(0x2000)  # 2.0x
    elif attacker.item == "Thick Club" and attacker.name in ["Cubone", "Marowak", "Marowak-Alola"] and use_physical:
        atk_mods.append(0x2000)  # 2.0x
        
    final_atk = max(1, poke_round((stat * chain_mods(atk_mods)) / 4096))
    return final_atk





def calculate_effective_defense(attacker: Pokemon, defender: Pokemon, move: Move, field: Field, defends_physically: bool) -> int:
    """Calculates effective defense stat including stage boosts, items, weather, and abilities."""
    raw_def = defender.raw_stats.def_ if defends_physically else defender.raw_stats.spd
    def_boost = defender.boosts.def_ if defends_physically else defender.boosts.spd
    
    # Critical hits ignore positive defense boosts
    if move.is_crit and def_boost > 0:
        def_boost = 0
        
    # Apply stage boost
    stat = poke_round(raw_def * get_stat_boost_multiplier(def_boost))
    
    def_mods: List[int] = []
    
    # 1. Weather Buffs
    if field.weather == "Sandstorm" and not defends_physically and "Rock" in defender.types:
        def_mods.append(0x1800)  # 1.5x
    elif field.weather == "Snow" and defends_physically and "Ice" in defender.types:
        def_mods.append(0x1800)  # 1.5x
        
    # 2. Defender Abilities
    if defends_physically:
        if defender.ability == "Fur Coat":
            def_mods.append(0x2000)  # 2.0x
        elif defender.ability == "Marvel Scale" and defender.status:
            def_mods.append(0x1800)  # 1.5x
            
    # 3. Attacker Abilities (Generation 9 Ruin Abilities debuff the defender)
    if attacker.ability == "Sword of Ruin" and defends_physically and defender.ability != "Sword of Ruin":
        def_mods.append(0x0C00)  # 0.75x
    elif attacker.ability == "Beads of Ruin" and not defends_physically and defender.ability != "Beads of Ruin":
        def_mods.append(0x0C00)  # 0.75x

    # 4. Defender Items
    if defender.item == "Eviolite": 
        # (Note: Strictly speaking, Eviolite requires a NFE check, but we apply it blindly here if held)
        def_mods.append(0x1800)  # 1.5x
    elif defender.item == "Assault Vest" and not defends_physically:
        def_mods.append(0x1800)  # 1.5x
        
    final_def = max(1, poke_round((stat * chain_mods(def_mods)) / 4096))
    return final_def





def calculate_final_mods(attacker: Pokemon, defender: Pokemon, move: Move, field: Field, type_mod: float) -> List[int]:
    """Calculates final damage multipliers like Life Orb, Screens, and Multiscale."""
    mods: List[int] = []
    use_physical = (move.category == "Physical")
    
    # 1. Screens (Bypassed by Critical Hits and Infiltrator)
    if not move.is_crit and attacker.ability != "Infiltrator":
        # Screens reduce damage by 50% in Singles, or ~33% in Doubles (0xAAC is 2732/4096)
        screen_mod = 0xAAC if field.battle_format == "Doubles" else 0x800
        
        if use_physical and field.defender_side.reflect:
            mods.append(screen_mod)
        elif not use_physical and field.defender_side.light_screen:
            mods.append(screen_mod)
        elif field.defender_side.aurora_veil:
            mods.append(screen_mod)
            
    # 2. Attacker Abilities
    if attacker.ability == "Sniper" and move.is_crit:
        mods.append(0x1800)  # 1.5x damage on crits
    elif attacker.ability == "Tinted Lens" and type_mod < 1.0:
        mods.append(0x2000)  # 2.0x damage on resisted hits
        
    # 3. Defender Abilities
    if defender.ability in ["Multiscale", "Shadow Shield"] and defender.cur_hp == defender.max_hp:
        mods.append(0x800)  # 0.5x damage at full HP
    elif defender.ability == "Fluffy":
        if move.flags.get("contact"):
            mods.append(0x800)   # 0.5x from contact moves
        if move.type == "Fire":
            mods.append(0x2000)  # 2.0x from Fire moves
    elif defender.ability in ["Solid Rock", "Filter", "Prism Armor"] and type_mod > 1.0:
        mods.append(0x0C00)  # 0.75x damage from Super Effective hits
        
    # 4. Attacker Items
    if attacker.item == "Life Orb":
        mods.append(0x14CC)  # 1.3x (Hex 14CC accurately represents the game's exact Life Orb multiplier)
    elif attacker.item == "Expert Belt" and type_mod > 1.0:
        mods.append(0x1333)  # 1.2x
        
    return mods




def get_stat_boost_multiplier(boost_level: int) -> float:
    """Returns the stat multiplier for a given boost level (-6 to +6)."""
    if boost_level > 0:
        return (2 + boost_level) / 2.0
    elif boost_level < 0:
        return 2.0 / (2 - boost_level)
    return 1.0





def calculate_gen9(attacker: Pokemon, defender: Pokemon, move: Move, field: Field) -> Result:
    # 0. Handle Fixed Damage (e.g., Seismic Toss, Night Shade)
    if move.name in ["Seismic Toss", "Night Shade"]:
        return Result(9, attacker, defender, move, field, [attacker.level] * 16)
        
    # Determine which stats to use
    use_physical = (move.category == "Physical")
    defends_physically = use_physical or move.name in ["Psyshock", "Psystrike", "Secret Sword"]
    
    # 1. Base Power Calculation
    base_power = calculate_base_power(attacker, defender, move, field)
    
    # 2. Effective Attack Calculation
    effective_atk = calculate_effective_attack(attacker, defender, move, field, use_physical)
    
    # 3. Effective Defense Calculation
    effective_def = calculate_effective_defense(attacker, defender, move, field, defends_physically)

    # 4. Base Damage Calculation
    level_calc = math.floor((2 * attacker.level) / 5) + 2
    base_damage = math.floor((level_calc * base_power * effective_atk) / effective_def)
    base_damage = math.floor(base_damage / 50) + 2
    
    # 5. Pre-Roll Modifiers
    if move.target == "allAdjacentFoes" and field.battle_format == "Doubles":
        base_damage = poke_round(base_damage * 0.75)
        
    if field.weather == "Sun":
        if move.type == "Fire":
            base_damage = poke_round(base_damage * 1.5)
        elif move.type == "Water":
            base_damage = poke_round(base_damage * 0.5)
    elif field.weather == "Rain":
        if move.type == "Water":
            base_damage = poke_round(base_damage * 1.5)
        elif move.type == "Fire":
            base_damage = poke_round(base_damage * 0.5)
            
    if move.is_crit:
        base_damage = poke_round(base_damage * 1.5)
        
    # 6. Type Effectiveness & STAB setup
    stab_mod = 1.0
    attacker_types = attacker.types
    if attacker.is_terastallized and attacker.tera_type:
        if move.type == attacker.tera_type and attacker.tera_type in attacker_types:
            stab_mod = 2.0
        elif move.type == attacker.tera_type or move.type in attacker_types:
            stab_mod = 1.5
    elif move.type in attacker_types:
        stab_mod = 1.5
        
    type_mod = 1.0
    defender_types = [defender.tera_type] if defender.is_terastallized and defender.tera_type else defender.types
    for def_type in defender_types:
        type_mod *= get_type_effectiveness(9, move.type, def_type)
        
    # 7. Final Modifiers Setup
    final_mods = calculate_final_mods(attacker, defender, move, field, type_mod)
    final_mod_multiplier = chain_mods(final_mods)
        
    # 8. The 16 Random Rolls
    damage_rolls: List[int] = []
    
    for r in range(85, 101):
        # Apply the random factor (0.85 to 1.00)
        roll_damage = math.floor((base_damage * r) / 100)
        
        # Apply STAB
        if stab_mod != 1.0:
            roll_damage = poke_round(roll_damage * stab_mod)
            
        # Apply Type Effectiveness
        roll_damage = math.floor(roll_damage * type_mod)
        
        # Apply Burn Penalty
        if attacker.status == "brn" and use_physical and attacker.ability != "Guts" and move.name != "Facade":
            roll_damage = math.floor(roll_damage * 0.5)
            
        # Apply Final Modifiers (Life Orb, Screens, etc.)
        if final_mod_multiplier != 0x1000:
            roll_damage = poke_round((roll_damage * final_mod_multiplier) / 4096)
            
        # Ensure minimum 1 damage (unless immune)
        if roll_damage == 0 and type_mod > 0:
            roll_damage = 1
            
        damage_rolls.append(roll_damage)
        
    return Result(9, attacker, defender, move, field, damage_rolls)