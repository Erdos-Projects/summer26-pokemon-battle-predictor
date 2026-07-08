# How to "post-compute" random teams using player seeds

<u><span style="color:red">Note before beginning:</span></u> When following the steps below to compute random teams using a seed from a match replay, `/data/randombattles/gen9/teams.ts` and `/data/randombattles/gen9/sets.json` (and any other relevant Pokedex files) must be the versions that were then-current when the match was played. If this isn't the case, your computed teams will be inaccurate&mdash;they may actually be "close" to the correct teams, but with one or two incorrect Pokemon.

1. Use `git clone` to clone PokemonShowdown!'s [`server` repository](https://github.com/smogon/pokemon-showdown/) to a local directory; for example we clone it into local directory `~/psserver` via
```
git clone https://github.com/smogon/pokemon-showdown/ ~/psserver
```

2. Make the following changes as described in the `.patch` file [team-gen-api](./team-gen-api.patch). There is one line insertion in `psserver/package.json`, and there are two sets of line insertions within `psserver/pokemon-showdown`.

3. Run `psserver % npm run start-team-generator`  
You should then see something like
```
> pokemon-showdown@0.11.10 start-team-generator
> node pokemon-showdown team-generator-server
Server running at http://localhost:3000/
```

4. Now you can you use a python script (or Jupyter notebook) with the following function
```python 
import json, requests

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
```
Example: 
```python 
>>>team_from_seed("sodium,17c4af16a0263f1fdf4d9174706fc5eb")
```
```text
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