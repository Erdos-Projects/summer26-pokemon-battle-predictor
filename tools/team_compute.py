import copy, json, re, time
import itertools, requests

import numpy as np

from pathlib import Path
from urllib.parse import urlencode, urljoin

from battle import *

# First, get 'teams_full' array: [<dict1>, <dict2>], with <dict#> = { <pokename> : <dict_of_info> }
# ===========================
REPLAY_DIR = Path('./../data/replays/gen9-randombattle')

with open('./../data/POKEDEX.json', 'r') as file:
    POKEDEX = json.load(file)

def pull_by_num(num):
    return Battle(f'./../data/replays/gen9-randombattle/gen9randombattle-{num}.json')