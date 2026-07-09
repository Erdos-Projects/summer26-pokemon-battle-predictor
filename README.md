# summer26-pokemon-battle-predictor
Team project: summer26-pokemon-battle-predictor
Team members: Taylor Daniels, Xiaoyu Huang, Greg Knapp, Mohammad Mannan, Marz Newman

## Project Summary

### Problem Statement

Pokemon battles are turn-based games in which two players compete with teams of 1-6 Pokemon of various types, abilities, and attributes, and the winner is the first to “knock-out” all of their opponent’s Pokemon—that is, reduce their respective Hit Points (HP) to zero. These matches are played in both casual and “ranked” (or tournament) settings, and the large number of individual Pokemon and different rulesets (“formats”) allows for enormous variability in gameplay and strategy.

One popular format on [PokemonShowdown!](play.pokemonshowdown.com) is the “random battle”, where players compete with teams of six Pokemon randomly generated at the start of each match. Ideally, generated matches and teams should be evenly-balanced so that, going in to a battle, both players have nearly equal chances of winning, and thus the winner is indeed "random". There are a number of factors and methods to consider in designing this balanced gameplay; some primary features that PokemonShowdown! considers in trying to create this balance are Pokemons' statistics (e.g., `hp`, `atk`, `def`) and types (e.g. `fire`, `psychic`, `ground`), and players' [Elo ratings] we consider are the distributions of the teams' (and individual Pokemons') statistics, types, and relative "advantange" over one another. In particular, if these features are well balanced across opposing teams, then we expect that comparison of said features should not strongly indicate a player's chance of winning.

### Stakeholders

The primary stakeholders include the players and developers of Pokemon Showdown. A player may want to know if they beat the odds during their matchup. Meanwhile, the developers can use win probability metrics to balance their team construction algorithm and the movesets and statistics of the “random” Pokemon which are eligible to be put on a team.

### Key Performance Indicators

In order to evaluate the performance of our model, we will assess its success on a new set of data using standard metrics for probability prediction models, like accuracy, precision, recall, log-loss, and AUC-ROC. In addition, we will be able to quantify how well different Decision Models predict match outcomes, and how “information completeness” (or lack-thereof) affects this performance.

### Data Set

We plan to collect “replays”, that is, turn-by-turn logs of matches, from matches which occur under the “[Gen 9] Random Battle” format on Pokemon Showdown (an example replay can be seen [here](https://replay.pokemonshowdown.com/gen8doublesubers-2555545993)).  These logs are available in easily parsed HTML formats, and contain complete turn-by-turn updates to the respective game states. From this data, we plan to attempt to gather the relevant features of team composition (e.g. species and move set of each Pokemon).  From the species information, we can use the [Pokemon Showdown Git Hub](https://github.com/smogon/pokemon-showdown) page to determine the statistics of each Pokemon, which could also be used as a feature for our model.