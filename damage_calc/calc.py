from typing import Optional
from .pokemon import Pokemon
from .move import Move
from .field import Field
from .result import Result
from .calc_gen9 import calculate_gen9
from .calc_gen1 import calculate_gen1

def calculate(
    gen: int,
    attacker: Pokemon,
    defender: Pokemon,
    move: Move,
    field: Optional[Field] = None
) -> Result:
    """
    Main entry point for calculating damage between two Pokémon.
    
    :param gen: Generation number (1-9).
    :param attacker: Attacking Pokémon instance.
    :param defender: Defending Pokémon instance.
    :param move: Move being executed.
    :param field: Field/environmental conditions (optional).
    :return: A Result instance containing the 16 damage rolls and percentage calculation methods.
    """
    if field is None:
        field = Field()
        
    if gen == 9:
        return calculate_gen9(attacker, defender, move, field)
    elif gen == 1:
        return calculate_gen1(attacker, defender, move, field)
    elif 1 <= gen <= 9:
        # Placeholder for remaining generations (Gens 2–8 can route here as they are added)
        raise NotImplementedError(f"Generation {gen} engine logic is not yet implemented.")
    else:
        raise ValueError(f"Invalid generation specified: {gen}. Must be between 1 and 9.")