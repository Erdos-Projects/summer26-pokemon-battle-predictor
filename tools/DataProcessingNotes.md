# Gathering and cleaning data

<span style="color:green">FYI a Jupyter notebook version of this document is available: [DataProcessingNotes.ipynb](DataProcessingNotes.ipynb)</span> 

------

## (1) Scraping Replays from PokemonShowdown! (PS)

<span style="color:green">For simplicity, here we assume that `pwd` is the repo base directory.</span>  

To scrape `gen9-randombattle` replay JSONs into a directory, say `data/replays`, one may simply run 
```zsh
% python tools/scraper.py data/replays 
```

or equivalently
```zsh
% chmod +x ./tools/scraper.py
% ./tools/scraper.py data/replays
```

To scrape replays of format `FMT` one can use
```zsh
% python tools/scraper.py -fmt "FMT" data/replays
```
#### Extra

By default, the script prints progress messages like
```
Now working on page 3.
    Done; taking a 2 second break.
Now working on page 4.
```
which can be suppresed by adding the flags `-q` or `--quiet`.

Other options and usage details can be found by using 
```zsh
% python tools/scraper.py -h
```

## (2) Computing the random teams and their stats

<u>(2a) Save Pokedex</u>: Follow the steps in [GettingDex.md](GettingDex.md) to save the Pokedex; 
* We assume it is written in `/data/pokedex_raw.json`. 

<u>(2b) "Key" Pokedex</u>:

```python
# 'keying' POKEDEX_raw entries by `id`
import json

with open('./../data/pokedex_raw.json','r') as file:
    POKEDEX_raw = json.load(file)

POKEDEX = { item['id'] : {key:item.get(key) for key in item.keys()} for item in POKEDEX_raw }

# saving to file
with open('./../data/pokedex_for_test.json', 'w') as file:
    json.dump(POKEDEX, file)
```

<u>(2c) Setup `team-generator-sever`</u>: Follow the guide [ComputingTeams.md](ComputingTeams.md) to set up the "server" which accepts player `seed` and returns a full Pokemon team;  
* <span style="color:orange">Note:</span> the following (in particular the function `get_teams_full`) assumes&mdash;indeed, *requires*&mdash;that the server is running/listening on port `localhost:3000`. Later, we can update said function to accept other ports if desired.

```python  
# setup
import json
from pathlib import Path
from team_compute import get_player_dets, get_teams_full, append_team_stats

replay_dir = Path("../data/test_data_replays/")

with open('../data/POKEDEX_for_test.json','r') as file:
    DEX = json.load(file)
```

```python
# this cell runs the actual computations and writings

errs = []

for replay in replay_dir.glob("*.json"): 
    try:
        with replay.open() as file:
            battle_json = json.load(file)

        battle_json['player_dets'] = get_player_dets(battle_json)
        
        TEAMS = get_teams_full(battle_json)
        try :
            for team in TEAMS:
                append_team_stats(DEX, team, battle_json['id']) # `id` is included just for debugging purposes
        except : 
            errs.append(replay.name)
            continue
        battle_json['teams_full'] = TEAMS
        
        replay.write_text(json.dumps(battle_json), encoding='utf-8')
    
    except:
        print("Error parsing file: %s" % replay.name)
        errs.append(replay.name)
        continue

errs # to list files that didn't work properly.
```

## (3) Parsing battles into `pandas.DataFrame` and removing custom-rule battles

Naturally, the following can be modified and run in different directories.

<u>(3a) Compiling battle data</u>: 

```python
from battle import *
from bat_to_list import battle_to_list

replay_dir = Path("../data/test_data_replays/")

# ===========================
DATA = []
customs = []
errs = []

for file in replay_dir.glob("*.json") : 
    try : 
        bat = Battle(file, parse=True)
        
        if not bat.custom_ruleQ : 
            DATA.append(battle_to_list(bat))
        else : 
            customs.append(file.name)
    except : 
        print(f"error with {file.name}")
        errs.append(file.name)
        continue

print(customs)
print(errs)
```

<u>(3b) Delete any replays having custom rules</u>: 

```python
import os
for replay in customs : 
    os.remove(replay_dir / file.name)
```

<u>(3c) Make `DATA` into `pandas.DataFrame` and save</u>: 

```python
import pandas as pd 

with open('../data/data_col_names.txt','r') as file:
    col_names = eval(file.read())

df = pd.DataFrame(DATA, columns=col_names)
df.info()
```

```python
with open('./../data/test_data_cleaned.csv','w') as file:
    file.write(df.to_csv(index=False))
```

<u>(3d) Testing read-in</u>:

```python
df = pd.read_csv("./../data/test_data_cleaned.csv")
df.info() # testing
```