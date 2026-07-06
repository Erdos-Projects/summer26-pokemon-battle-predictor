# Reading data into `pandas.DataFrame`

A list of column names is included in `data_cleaned.csv` as the first line; `data_col_names.txt` has a standalone copy. Although `pandas` should be able to recognize the `dtypes` of the different columns when reading-in `data_cleaned.csv` (using `pandas.read_csv`), a mapping/dictionary of `{col} : {type}` is included in `data_col_types.txt` 

Assuming that `pwd`/`cwd` contains the unzipped `data_cleaned.csv`: 
```python
import pandas as pd
df = pd.read_csv("./data_cleaned.csv")
```
```
df.info()
>>> <class 'pandas.core.frame.DataFrame'>
    RangeIndex: 12778 entries, 0 to 12777
    Columns: 299 entries, format to M26_off
    dtypes: bool(13), float64(1), int64(126), object(159)
    memory usage: 28.0+ MB
```

# Info about `data_cleaned.csv`

`data_cleaned.csv` contains observations of $\approx 12700$ battles pulled from [pokemonshowdown.com](PokemonShowdown!), with each battle having $299$ features, as documented below. Note: many of the features are easily understood by their name alone, so we only describe a select few in detail. 

**<u>Battle metadata and 'macro-data'</u>**  
Columns 1&ndash;23 (indices `[0,23)`) contain:
1. `format: str`; the gametype, e.g. `gen9randombattle`
2. `id: int`; the game number. Battles are generally stored online as `{fmt}-{id}`, so here we store only the number.
4. `p1_win: int` flag $\{0,1\}$
5. `ratedQ: bool` Has value `True` if and only if the match affected players' Elo ratings.
6. `n_turns: int`
7. `start_time: int`
8. `end_time: int`
9. `duration: int` Equal to `end_time - start_time`;

(9&ndash;12) are `p1name`, `p1side`, `p1elo0`, `p1elo1`, where `elo0` and `elo1` are the pre- and post-battle Elos, respectively.  
(13&ndash;16) are the same with `p2___`  
Note: Here 'side' refers to whether the player was logged as 'player1' or 'player2'; these are redundant with the labels `p1____`, `p2____` but we include them just for completeness.

17. `type_diversity_diff: int` Equal to #(types on Team1) &ndash; #(types on Team2)
18. `num_boosting_abilities_diff: int` Equal to the differential in the number of distinct Pokemon with "situational boosting abilities" (i.e. abilities that sometimes--but not always--boost damage or stats and hence, are difficult to account for in the advantage stat).
19. `num_move_boosters_diff: int` Equal to the differential in the number of distinct Pokemon which have moves that are capable of boosting their own stats.  Again, these are difficult to account for in the advantage stat.
20. `total_stat_diff: int` Equal to the differential in the sum of the (relevant) statistics of all Pokemon on each team.  Letting `M{i}{j}` be the pokemon in the jth position of team i, it takes the sum of `M{1}{j}_{stat}` where j ranges from 1 to 6 and stat ranges across HP, max(atk, spa), def, spd, spe.  Then it subtracts the corresponding sum of `M{2}{j}_{stat}`.
21. `p1_total_adv: float` Equal to the sum of all `FullPokemon.advantage(M{1}{j},M{2}{k})` as j and k range from 1 to 6.
22. `p1_revealed_team_size: int` Number of distinct Pokemon fielded on team1 in battle.
23. `p2_revealed_team_size: int` "    "

**<u>Individual Pokemon Data</u>**  
The remaining $276 = 12\cdot23$ columns (beginning at index `23`) have names `M{i}{j}_{field}`, where: 
* `i=1,2` is the Team;
* `1 ≤ j ≤ 6` is the ordering of Pokemon on Team-`i`;
* The 23 fields for each `M{i}{j}` are as follows:

1. `name: str`
2. `speciesId: str`
3. `used: int` {0,1}-flag; indicates if Pokemon was seen in Battle.
4. `gender: str`
6. `shinyQ: bool`
7. `level: int`
5. `ability: str`
8. `item: str`
9. `teraType: str`
10. `role: str`

(11&ndash;14): `str`; moves `mv1`, `mv2`, `mv3`, and `mv4`  
(15&ndash;16): `str`; types `type1` and `type2`. <span style="color:orange">Note:</span> For uniformity, Pokemon with only one Type have `type2 = "N/A"`  
(17&ndash;23): `int`; stats `hp`, `atk`, `def`, `spa`, `spd`, `spe`, `off`; the latter is `= max(atk,spa)`.