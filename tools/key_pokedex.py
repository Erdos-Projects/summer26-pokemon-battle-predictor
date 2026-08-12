#!/usr/bin/env python
import json
from pathlib import Path

# getting the project root
PROJECT_ROOT = Path.cwd()
while (PROJECT_ROOT.name != "summer26-pokemon-battle-predictor") and (PROJECT_ROOT.parent != PROJECT_ROOT):
    PROJECT_ROOT = PROJECT_ROOT.parent

with open(PROJECT_ROOT / "data/pokedex.json", 'r') as file:
    pokedex_raw = json.load(file)

pokedex = { mon['id'] : {key : mon[key] for key in mon.keys()} for mon in pokedex_raw }

with open(PROJECT_ROOT / 'data/pokedex.json', 'w') as file:
    json.dump(pokedex, file)