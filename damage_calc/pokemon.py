import math
from dataclasses import dataclass, field
from typing import Optional, Tuple, List
from .types import Gender, Status
from .stats import StatsTable, BoostsTable
from . import data  # Import our new data loader

def get_nature_multiplier(gen: int, nature_name: str, stat_name: str) -> float:
    """Calculates the 1.1x or 0.9x stat multiplier based on Nature."""
    if gen < 3:
        return 1.0  # Natures don't exist in Gens 1 and 2
    
    nature_data = data.get_nature(gen, nature_name)
    if not nature_data:
        return 1.0
        
    if nature_data.get("plus") == stat_name:
        return 1.1
    if nature_data.get("minus") == stat_name:
        return 0.9
    return 1.0

def calc_stat(gen: int, stat_name: str, base: int, iv: int, ev: int, level: int, nature_name: str) -> int:
    """Calculates the raw stat value based on generation formulas."""
    nature_mult = get_nature_multiplier(gen, nature_name, stat_name)
    
    if stat_name == "hp":
        if base == 1:  # Shedinja mechanic
            return 1
        return math.floor((2 * base + iv + math.floor(ev / 4)) * level / 100) + level + 10
    else:
        core_stat = math.floor((2 * base + iv + math.floor(ev / 4)) * level / 100) + 5
        return math.floor(core_stat * nature_mult)

@dataclass
class Pokemon:
    gen: int
    name: str
    level: int = 100
    item: Optional[str] = None
    ability: Optional[str] = None
    ability_on: bool = False
    nature: str = "Serious"
    gender: Gender = "N"
    status: Optional[Status] = None
    toxic_counter: int = 0
    
    # Generation mechanics flags
    is_dynamaxed: bool = False
    is_terastallized: bool = False
    tera_type: Optional[str] = None
    
    # Stat inputs
    ivs: StatsTable = field(default_factory=lambda: StatsTable(31, 31, 31, 31, 31, 31))
    evs: StatsTable = field(default_factory=lambda: StatsTable(0, 0, 0, 0, 0, 0))
    boosts: BoostsTable = field(default_factory=BoostsTable)
    
    # Auto-populated from JSON data
    types: List[str] = field(init=False)
    base_stats: StatsTable = field(init=False)
    raw_stats: StatsTable = field(init=False)
    max_hp: int = field(init=False)
    cur_hp: int = field(init=False)

    def __post_init__(self):
        # 1. Fetch species data from JSON
        species_data = data.get_species(self.gen, self.name)
        if not species_data:
            raise ValueError(f"Pokemon '{self.name}' not found in Generation {self.gen} data.")
            
        # Auto-populate primary ability if not specified
        if self.ability is None:
            abilities = species_data.get("abilities", {})
            if isinstance(abilities, dict):
                self.ability = abilities.get("0") or abilities.get("H")
            elif isinstance(abilities, list) and len(abilities) > 0:
                self.ability = abilities[0]
            
        # 2. Populate Types
        self.types = species_data.get("types", ["Normal"])
        
        # 3. Populate Base Stats
        bs = species_data.get("baseStats", {})
        self.base_stats = StatsTable(
            hp=bs.get("hp", 0),
            atk=bs.get("atk", 0),
            def_=bs.get("def", 0), # Map 'def' to 'def_'
            spa=bs.get("spa", 0),
            spd=bs.get("spd", 0),
            spe=bs.get("spe", 0)
        )
        
        # 4. Calculate Raw Stats dynamically
        self.raw_stats = StatsTable(
            hp=calc_stat(self.gen, "hp", self.base_stats.hp, self.ivs.hp, self.evs.hp, self.level, self.nature),
            atk=calc_stat(self.gen, "atk", self.base_stats.atk, self.ivs.atk, self.evs.atk, self.level, self.nature),
            def_=calc_stat(self.gen, "def", self.base_stats.def_, self.ivs.def_, self.evs.def_, self.level, self.nature),
            spa=calc_stat(self.gen, "spa", self.base_stats.spa, self.ivs.spa, self.evs.spa, self.level, self.nature),
            spd=calc_stat(self.gen, "spd", self.base_stats.spd, self.ivs.spd, self.evs.spd, self.level, self.nature),
            spe=calc_stat(self.gen, "spe", self.base_stats.spe, self.ivs.spe, self.evs.spe, self.level, self.nature),
        )
        
        # 5. Set HP values
        self.max_hp = self.raw_stats.hp
        if self.is_dynamaxed:
            self.max_hp *= 2
            
        self.cur_hp = self.max_hp