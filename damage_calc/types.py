from dataclasses import dataclass, field
from typing import Optional, Literal, Tuple
from enum import Enum

class Stat(str, Enum):
    HP = "hp"
    ATK = "atk"
    DEF = "def"  # 'def' is a reserved keyword in Python
    SPA = "spa"
    SPD = "spd"
    SPE = "spe"

class Status(str, Enum):
    BRN = "brn"  # Burn
    FRZ = "frz"  # Freeze
    PAR = "par"  # Paralyze
    PSN = "psn"  # Poison
    TOX = "tox"  # Toxic (Badly Poisoned)
    SLP = "slp"  # Sleep

Category = Literal["Physical", "Special", "Status"]
Gender = Literal["M", "F", "N"]
Format = Literal["Singles", "Doubles"]









