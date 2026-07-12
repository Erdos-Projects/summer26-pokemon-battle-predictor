# Getting the Pokedex for `gen9-randombattles`

1. Use `git clone` to clone PokemonShowdown!'s [`server` repository](https://github.com/smogon/pokemon-showdown/) to a local directory; for example we clone it into local directory `~/psserver` via
```
git clone https://github.com/smogon/pokemon-showdown/ ~/psserver
```

2. Make the following changes to `/data/randombattles/gen9/teams.ts` as shown in the `.patch` file [write-dex](/tools/write-dex.patch). 
    * <span style="color:red">Note:</span> don't forget to change `<PATH>` to a valid directory in `teams.ts`. 

3. Assuming you have installed `npm` (using homebrew or other means), run (in `.../psserver`)
```
psserver % npm run build
```

4. Generate a random `gen9randombattle` team; the lines inserted into `teams.ts` are run during this process:
```
psserver % ./pokemon-showdown generate-team gen9randombattle 
```

5. Comment-out your added lines in `teams.ts`, **<u>and then again run</u>** 
```
psserver % npm run build
``` 
or else the large writing is done every time a team is generated (which will severely impede the computation of teams using player seeds)

6. Note: the Pokedex JSON written to file is just a list-of-dicts, so you may wish to run through the list and make a Pokedex dictionary with keys such as `name` or `speciesId`.