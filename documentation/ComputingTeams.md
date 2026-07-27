# How to "post-compute" random teams using player seeds

> [!WARNING]
> When recomputing random teams from player seeds as detailed below, the files `teams.ts` and 
> `sets.json` in `/data/randombattles/gen9/`
> (as well as any other relevant Pokédex files) must be the versions that were current 
> *when the match was played*. If this isn't the case, then the computed teams will be inaccurate.

1. Clone Pokemon Showdown's [`server` repository](https://github.com/smogon/pokemon-showdown/) 
   to a local directory.
```
git clone https://github.com/smogon/pokemon-showdown/
```

2. Within the root directory of this cloned repository, make the changes to the files `/package.json` and `/pokemon-showdown` as described in [team-gen-api.patch](team-gen-api.patch). 

3. Still in this root directory, run `npm run start-team-generator`; you should then see something like
```
> pokemon-showdown@0.11.10 start-team-generator
> node pokemon-showdown team-generator-server
Server running at http://localhost:3000/
```

4. You can now recompute the random teams from their seeds using a Python script or Jupyter notebook with the following function
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

####  Example usage and output:
```python 
>>> team_from_seed("sodium,17c4af16a0263f1fdf4d9174706fc5eb")
>>> [{'name': 'Braviary',
      'species': 'Braviary',
      ... ...
      'role': 'Fast Bulky Setup'},
     {'name': 'Dodrio',
      'species': 'Dodrio',
      ...}
      ...
     ]
```