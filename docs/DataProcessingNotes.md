# Data Collection and Processing

> [!TIP] 
> A Jupyter notebook with everything below is available here: [DataProcessingNotes.ipynb](../misc/DataProcessingNotes.ipynb)

------------------------------------------------------------

## 1. Scraping Replays from Pokémon Showdown

<span style="color:white;background:darkgreen;padding:0px 3px;border-radius:2px">Note:</span> For simplicity, here we assume that `pwd` is the repo base directory "`/`".

To scrape `gen9-randombattle` replay JSONs into a directory, run 
```zsh
python tools/scraper.py [/your/dir] 
```

Other options and usage details can be found by using 
```zsh
python tools/scraper.py -h
```

------------------------------------------------------------

## 2. Computing the random teams and their stats

Follow the guide [GettingFullTeams](./../tools/GettingFullTeams.md)


------------------------------------------------------------

## 3. Parsing battles into `pandas.DataFrame` and removing custom-rule battles

Naturally, the following can be modified and run in different directories.

#### 3.1. Compiling battle data 

```python
from tools.battle import *
from tools.bat_to_list import battle_to_list

# NOTE: Unzip the folder(s) in /data/replays to run this, or change to your desired directory
replay_dir = Path("../data/replays/test_data_replays/") 

# ===========================
DATA = []
customs = []
errs = []

for replay in replay_dir.glob("*.json") : 
    try : 
        with replay.open() as file :
            replay_json = json.load(file)
        bat = Battle(replay_json, parse=True)
        
        if not bat.custom_ruleQ : 
            DATA.append(battle_to_list(bat))
        else : 
            customs.append(replay.name)
    except : 
        print(f"error with {replay.name}")
        errs.append(replay.name)
        continue

print(customs)
print(errs)
```

#### 3.2. Delete any replays having custom rules 
```python
import os
for replay in customs : 
    os.remove(replay_dir / file.name)
```

#### 3.3. Make `DATA` into `pandas.DataFrame` and save 

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

#### 3.4. Testing read-in

```python
df = pd.read_csv("./../data/test_data_cleaned.csv")
df.info() # testing
```