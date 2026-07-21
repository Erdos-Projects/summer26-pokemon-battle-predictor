from dataclasses import dataclass
from typing import List
from .pokemon import Pokemon
from .move import Move
from .field import Field

@dataclass
class Result:
    gen: int
    attacker: Pokemon
    defender: Pokemon
    move: Move
    field: Field
    
    # Typically a list of 16 integers representing the 16 possible random damage rolls (RNG).
    # Multi-hit moves might structure this differently, but a flat list is the standard.
    damage: List[int] 
    
    def get_max_damage(self) -> int:
        return max(self.damage) if self.damage else 0
        
    def get_min_damage(self) -> int:
        return min(self.damage) if self.damage else 0

    def get_percentage_range(self) -> str:
        """Returns the damage range as a percentage of the defender's max HP."""
        if self.defender.max_hp == 0 or not self.damage:
            return "0.0% - 0.0%"
            
        min_pct = (self.get_min_damage() / self.defender.max_hp) * 100
        max_pct = (self.get_max_damage() / self.defender.max_hp) * 100
        
        return f"{min_pct:.1f}% - {max_pct:.1f}%"