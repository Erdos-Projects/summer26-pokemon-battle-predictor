# Getting the Pokedex for `gen9-randombattles`

1. Clone Pokemon Showdown's `server` repository: 
```
git clone https://github.com/smogon/pokemon-showdown/
```

2. Make the changes to `/data/randombattles/gen9/teams.ts` shown in [write-dex.patch](write-dex.patch). 
    * <span style="color:red">Note:</span> don't forget to change `<PATH>` to a valid directory in `teams.ts`. 

3. Assuming you have installed `npm`, in the repository's root directory run
```
npm run build
```

4. Generate a random `gen9randombattle` team
```
./pokemon-showdown generate-team gen9randombattle 
```
(The lines inserted into `teams.ts` are run during this process.)

5. Comment-out your added lines in `teams.ts`, **<u>and then again run</u>** 
```
npm run build
``` 
or else the large writing is done every time a team is generated (which will severely impede the computation of teams using player seeds)

> [!NOTE]
> The Pokédex JSON written to file is a large list of dictionaries, so you may wish to run through the list and make a Pokedex dictionary with keys such as `name` or `speciesId`.