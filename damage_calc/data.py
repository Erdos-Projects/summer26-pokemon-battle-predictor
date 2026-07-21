import json
import os
from functools import lru_cache
from typing import Dict, Any

# Points to the json_data folder in your project directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "json_data")

@lru_cache(maxsize=None)
def load_data(gen: int, data_type: str) -> Dict[str, Any]:
    """
    Loads JSON data for a specific generation and type.
    Caches the result in memory so it's only read from disk once.
    """
    file_path = os.path.join(DATA_DIR, f"gen{gen}", f"{data_type}.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def get_species(gen: int, name: str) -> Dict[str, Any]:
    return load_data(gen, "species").get(name, {})

def get_move(gen: int, name: str) -> Dict[str, Any]:
    return load_data(gen, "moves").get(name, {})

def get_item(gen: int, name: str) -> Dict[str, Any]:
    return load_data(gen, "items").get(name, {})

def get_nature(gen: int, name: str) -> Dict[str, Any]:
    return load_data(gen, "natures").get(name, {})