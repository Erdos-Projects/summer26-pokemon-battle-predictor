from dataclasses import dataclass, field
from typing import Optional, Literal, Tuple
from enum import Enum
from .types import Format

@dataclass
class Side:
    # Hazards
    spikes: int = 0
    stealth_rock: bool = False
    sticky_web: bool = False
    toxic_debris: bool = False
    
    # Screens
    reflect: bool = False
    light_screen: bool = False
    aurora_veil: bool = False
    
    # Modifiers
    tailwind: bool = False
    friendship: int = 255  # For moves like Return/Frustration

@dataclass
class Field:
    battle_format: Format = "Singles"
    weather: Optional[str] = None
    terrain: Optional[str] = None
    
    # Room conditions
    is_gravity: bool = False
    is_magic_room: bool = False
    is_wonder_room: bool = False
    is_trick_room: bool = False
    
    attacker_side: Side = field(default_factory=Side)
    defender_side: Side = field(default_factory=Side)