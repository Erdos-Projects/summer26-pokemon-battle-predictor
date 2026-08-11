
------------------------------------------------------------

## 1. Making and using a custom team-generation server

#### 1.1. Clone Smogon's `pokemon-showdown` (server) repository:
```
git clone https://github.com/smogon/pokemon-showdown/
```
#### 1.2. In `pokemon-showdown/` edit the files `package.json` and `pokemon-showdown` as indicated in [team-gen-api.patch](team-gen-api.patch). 

#### 1.3. Still in the root directory, run 
```
npm run start-team-generator
``` 
You should then see output including `Server running at http://localhost:3000/`

#### 1.4. Feed player 'seeds' to the server from Step 1.3. For example:
```python 
import json, requests

def team_from_seed(seed: str) -> list[dict]:
    params = urlencode({
            "format": 'gen9randombattle', 
            "seed": seed
        }) 
    url = f"http://localhost:3000?{params}"
    
    response = requests.get(url)
    team = json.loads(response.content.decode())
        
    return team

team_from_seed("sodium,17c4af16a0263f1fdf4d9174706fc5eb")
```

Example output:
```
[{'name': 'Braviary',
  'species': 'Braviary',
  ... ...
  'role': 'Fast Bulky Setup'},
 {'name': 'Dodrio',
  'species': 'Dodrio',
  ...}
  ...
 ]
```

> [!IMPORTANT]
> For accurate Battle information, the files  
> &emsp;&emsp; `pokemon-showdown/data/randombattles/gen9/teams.ts`,  
> &emsp;&emsp; `pokemon-showdown/data/randombattles/gen9/sets.json`,  
> (as well as any other relevant Pokédex files) must be the versions that were current 
> *when the match to be parsed was played*.

------------------------------------------------------------

## 2. Getting the Pokédex for `gen9-randombattles`

#### 2.1. Make the changes to `pokemon-showdown/data/randombattles/gen9/teams.ts` shown in [write-dex.patch](write-dex.patch). <span style="color:gold">Note:</span> Change `<PATH>` to a valid directory in `teams.ts`

#### 2.2. In `pokemon-showdown/`, run
```
npm run build
```
and then
```
./pokemon-showdown generate-team gen9randombattle 
```
The lines inserted into `teams.ts` are run during this process.

> [!WARNING]
> #### 2.3. Now comment-out your added lines in `teams.ts`, and then <u>again run</u> 
> ```
> npm run build
> ``` 
> or else the large writing is done every time a team is generated (which will severely impede the `Battle` parser.)

#### 2.4. (Optional, but recommended): "Key" the Pokédex
```python
import json

with open('./../data/pokedex.json','r') as file:
    POKEDEX_raw = json.load(file)

# Pokedex is originally like a list-of-dicts, 
# but bookended with `{ }` not `[ ]`.
POKEDEX = { item['id'] : {key:item.get(key) for key in item.keys()} for item in POKEDEX_raw }

# saving to file
with open('./../data/pokedex.json', 'w') as file:
    json.dump(POKEDEX, file)
```


