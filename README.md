# summer26-pokemon-battle-predictor
Team project: summer26-pokemon-battle-predictor
Team members: Taylor Daniels, Xiaoyu Huang, Greg Knapp, Mohammad Mannan, Marz Newman

## Project Summary
Pokémon battles are turn-based games in which two players compete with teams of 6 Pokémon. These matches are played both casually and competitively, and the large number of different Pokémon and unique game rulesets allows for enormous variability in gameplay and strategy.

One popular game format on [Pokémon Showdown](play.pokemonshowdown.com) (“Showdown”) is the “random battle”, where players compete with teams of six Pokémon randomly generated at the start of each match. Ideally, generated teams should be evenly balanced, so that, going into a battle, both players have nearly equal chances of winning, and thus the winner is indeed “random”. There are a number of factors and methods to consider in designing this balanced gameplay; some primary features that Showdown considers in trying to create this balance are Pokémon's statistics (e.g., HP, Attack, Defense) and types (e.g., Fire, Psychic, Ground), and players’ [Elo ratings](https://en.wikipedia.org/wiki/Elo_rating_system) (within Showdown’s system).  We consider the distributions of the teams’ Pokémon’s statistics, types, and relative “advantage” over one another  to see if these features are well balanced across opposing teams.  If Showdown’s team construction algorithm is balanced, then we expect that comparison of said features should not strongly indicate a player's chance of winning.

### Data Collection

Showdown logs a large amount of information about each match played on the site, including player Elo ratings and turn-by-turn records of player moves, allowing for a full, turn-by-turn reconstruction of each match from its publicly available “replay” JSON files. Examples of a replay and its JSON are 
[here](https://replay.pokemonshowdown.com/gen9randombattle-2646780843) 
and 
[here](https://replay.pokemonshowdown.com/gen9randombattle-2646780843.json), respectively.

Using a simple web-scraper making API requests (`tools/scraper.py`), we saved ≈16k Showdown match replays, and then used a custom-made text parser (`<class Battle>` from `/tools/battle.py`) to compile data about each match, such as match length, Pokémon used, player Elo ratings before-and-after the match, to name a couple.

In each random battle, players can see their own Pokémon but cannot see their opponent’s Pokémon until they are individually fielded; additionally, spectators (and hence, the replay logs) cannot see any not-yet-fielded Pokémon, even past the match’s end. In order to learn the “complete” teams of six in each match, it was necessary to locate the pseudorandom strings used as “seeds” in generating players’ random teams, and then feed this string into Showdown’s server source code to re-generate the complete random teams. These steps are detailed in [ComputingTeams.md](./tools/ComputingTeams.md).

In addition, the level-scaled stats of each Pokémon in the matches were computed using the formulas from the Pokémon game mechanics, as summarized in [Stats.md](./tools/Stats.md), and using Pokémon base stats pulled from the Pokedex obtained as in [GettingDex.md](./tools/GettingDex.md). Lastly, matches involving custom rules (on top of the random battle format) were removed from the data.


### Key Performance Indicators

In order to evaluate the performance of our model, we will assess its success on a new set of data using standard metrics for probability prediction models, like accuracy, precision, recall, log-loss, and AUC-ROC. In addition, we will be able to quantify how well different Decision Models predict match outcomes, and how “information completeness” (or lack-thereof) affects this performance.