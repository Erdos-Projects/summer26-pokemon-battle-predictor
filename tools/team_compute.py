import json, re, copy
import requests

import numpy as np

from pathlib import Path
from urllib.parse import urlencode





# ===============================================
# Macro functions
# ===============================================
def get_teams_full(battle_json):
    '''
    Intake a replay json, compute its full teams and stats.
    '''
    
    # (1) Add 'player_dets' entry
    battle_json['player_dets'] = get_player_dets(battle_json) # [[1]]

    # (2)-(3) Get `seed`s and pass these to "server" to receive full team list.
    _temp_array = []
    
    for player in battle_json['player_dets']:
        seed = player['seed'] 
        _temp_array.append(team_from_seed(seed)) # [[2]]

    # Now we convert _temp_array -> teams_full: 
    # _temp_array[i] = [{poke_i1}, ..., {poke_i6}]
    #     |-> teams_full[i] = ['poke_i1':{poke_i1}, ..., 'poke_i6':{poke_i6}]
    teams_full = []
    for team in _temp_array:
        team_D = dict()
        for poke in team:
            team_D[poke['name']] = copy.deepcopy(poke)
        teams_full.append(team_D)

    return teams_full

# helper functions

# [[1]]
# -----------------------------------------------
def get_player_dets(battle_json):
    try:
        match1 = re.search(r'\>player p1 ({.*?})$', battle_json['inputlog'], re.M)
        p1_json = json.loads(match1.group(1))
        assert p1_json['name'] == battle_json['players'][0] # just to be certain
    except:
        print(f"Couldn't get p1 info. ({battle_json.id})")
        return None

    try:
        match2 = re.search(r'\>player p2 ({.*?})$', battle_json['inputlog'], re.M)
        p2_json = json.loads(match2.group(1))
        assert p2_json['name'] == battle_json['players'][1] # just to be certain
    except:
        print(f"Couldn't get p2 info. ({battle_json.id})")
        return None
    
    return [p1_json, p2_json]

# [[2]]
# -----------------------------------------------
def team_from_seed(seed):
    params = urlencode({
            "format": 'gen9randombattle', 
            "seed": seed
        }) 
    url = f"http://localhost:3000?{params}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestsException as e: 
        print("Could not get team: %s", e)
        return []
    
    try: 
        team = json.loads(response.content.decode())
    except json.JSONDecodeError as e:
        print("failed to parse team: %s", e)
        return []
        
    return team



# ===============================================
# add the BVs and computed Stats to each Pokemon 
def append_team_stats(DEX: dict, team_D: dict, battle_id = ''):
    '''
    Input poke dict, compute total stats for each Pokemon in it, append to Pokemon, and return team.
    '''
    for name in team_D.keys():
        poke = team_D[name] # get the `dict`

        # (4)-(5)
        species = poke['speciesId']
        try: 
            poke['bvs'] = copy.deepcopy(DEX[species]['baseStats']) # deepcopy for safety
            poke['stats'] = compute_stats(poke) # [[3]]
            poke['types'] = copy.deepcopy(DEX[species].get('types'))
        except: 
            print("error with pokemon %s (%s)" % (species,battle_id))
            continue
        
    return None

# -----------------------------------------------
# [[3]]
def compute_stats(poke: dict) :
    '''
    `poke` should have dictionaries `BV`, `EV`, `IV`, and entry `level`
    example output: {'hp': 263, 'atk': 120, 'def': 169, 'spa': 240, 'spd': 216, 'spe': 223}
    '''
    _stat_D = {}

    BV = poke['bvs']
    EV = poke['evs']
    IV = poke['ivs']
    lvl = poke['level']

    for k in BV.keys():
        Q_k = (2*BV[k] + IV[k] + np.floor(EV[k]/4))*(lvl/100)
        nat_k = 1.0 # in case we want to incorporate `nature`s later
        
        if k == 'hp':
            _stat_D[k] = int(np.floor(Q_k) + lvl + 10)
        else:
            _stat_D[k] = int(np.floor((Q_k+5)*nat_k))

    return _stat_D