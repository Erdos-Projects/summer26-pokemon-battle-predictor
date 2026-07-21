from dataclasses import dataclass, field
from typing import Optional, Union, List
from .types import Category
from . import data

@dataclass
class Move:
    gen: int
    name: str
    
    # Optional user overrides
    bp_override: Optional[int] = None
    type_override: Optional[str] = None
    category_override: Optional[Category] = None
    hits_override: Optional[int] = None
    
    # State tracking
    times_used: int = 1
    times_used_with_metronome: int = 0
    is_crit: bool = False
    
    # Mechanic flags
    is_z: bool = False
    is_max: bool = False
    
    # Auto-populated from JSON data
    base_power: int = field(init=False)
    type: str = field(init=False)
    category: Category = field(init=False)
    priority: int = field(init=False)
    hits: int = field(init=False)
    target: str = field(init=False)
    flags: dict = field(init=False)
    
    def __post_init__(self):
        # 1. Fetch move data from JSON
        move_data = data.get_move(self.gen, self.name)
        if not move_data:
            raise ValueError(f"Move '{self.name}' not found in Generation {self.gen} data.")
            
        # 2. Populate Base Power
        if self.bp_override is not None:
            self.base_power = self.bp_override
        else:
            self.base_power = move_data.get("basePower", move_data.get("bp", 0))
            
        # 3. Populate Type
        if self.type_override is not None:
            self.type = self.type_override
        else:
            self.type = move_data.get("type", "Normal")
            
        # 4. Populate Category
        if self.category_override is not None:
            self.category = self.category_override
        else:
            self.category = move_data.get("category", "Status")
            
        # 5. Populate Priority
        self.priority = move_data.get("priority", 0)
        
        # 6. Populate Target (Critical for spread move damage reduction later)
        self.target = move_data.get("target", "any")
        
        # 7. Populate Flags (e.g., contact, protect, punch, bite)
        self.flags = move_data.get("flags", {})
        
        # 8. Populate Hits (handling multihit moves)
        # JSON 'multihit' can be an integer (e.g., 2) or a list (e.g., [2, 5]).
        if self.hits_override is not None:
            self.hits = self.hits_override
        else:
            multihit = move_data.get("multihit", 1)
            if isinstance(multihit, list):
                # Defaulting to max hits for ranges like [2, 5], 
                # though the calc engine will adjust this later if Skill Link isn't active.
                self.hits = multihit[1]
            else:
                self.hits = multihit