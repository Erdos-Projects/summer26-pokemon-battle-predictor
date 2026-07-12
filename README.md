# summer26-pokemon-battle-predictor
This repository holds the work done on a project as part of the Erdős Institute's Summer 2026 Data Science Boot Camp.

**Contributors:** Taylor Daniels, Xiaoyu Huang, Greg Knapp, Mohammad Mannan, Marz Newman

[Project Executive Summary](./documentation/ExecutiveSummary.pdf) (PDF)  
[Project Presentation Slides](./documentation/PokemonBattlePredictorSlides.pdf) (PDF)

## Summary
Pokémon battles are turn-based games in which two players compete with teams of 6 Pokémon. The large number of different Pokémon and different game rulesets allows for enormous variability in gameplay and strategy. One popular game format on battle emulator site [Pokémon Showdown](play.pokemonshowdown.com) (“Showdown”) is the “random battle”, where players compete with teams of six Pokémon randomly selected at battle start. Ideally, these randomly generated teams should be evenly balanced, so that, going into a battle, both players have nearly equal chances of winning, and thus the winner is indeed “random”.

From the Showdown developers’ perspective, there are a number of factors and methods to consider in designing this balanced gameplay. Some primary features to consider are Pokémon's <i>stats</i> (e.g., HP, Attack, Defense) and <i>types</i> (e.g., Fire, Psychic, Ground), and players’ [Elo ratings](https://en.wikipedia.org/wiki/Elo_rating_system) (within Showdown’s system).  We aim to investigate whether or not the team generation procedure is balanced. If Showdown’s team construction algorithm is balanced, then we expect that comparison of said features should not strongly indicate a player's chance of winning.

### Data Collection

Our process for collecting and processing battle-log JSON files from Showdown is detailed in [DataProcessingNotes.md](./documentation/DataProcessingNotes.md) (and the `ipynb` version [DataProcessingNotes.ipynb](./documentation/DataProcessingNotes.ipynb)).

In each random battle, players cannot see their opponent’s Pokémon until they are individually fielded; additionally, the replay logs do not record these not-yet-fielded Pokémon, even past the battle’s end. Our method interfacing with Showdown's source code in order to re-generate the complete team rosters in each battle&mdash;including those Pokémon not fielded&mdash;is outlined in [ComputingTeams.md](./documentation/ComputingTeams.md).

### Feature Engineering

Having two teams of 6 Pokémon, each with their own stats and characteristics, gave us many potential features to consider, for example: 
    <ul>
        <li><strong>Pokémon Attributes&hairsp;:</strong> Features such as a Pokémon's HP, Attack, Defense, and type(s).</li>
        <li><strong>Type Diversity&hairsp;:</strong> The number of unique Pokémon types on a team.</li>
        <li><strong>Pokémon <i>Advantage</i>&hairsp;:</strong> A custom statistic approximating the expected difference in total damage that two opposing Pokémon would exchange in a one-on-one match. See [Advantage.md](./documentation/Advantage.md) for details.</li>
        <li><strong>Team Advantage&hairsp;:</strong> The cumulative sum of the Advantages for all 36 possible pairs of opposing Pokémon from each team.</li>
    </ul>
    While Team Advantage was our most impactful feature, it has known drawbacks, such as failing to consider the specific moves or abilities for each Pokémon. In an attempt to address this we introduced the <i>Stat-Booster Differential</i>, which records the difference in the number of Pokémon on each team that know a stat-boosting move, or have a stat-boosting ability.

### Model Selection

For a “baseline” model, it was sensible to use a single-feature predictor based on players’ Elo rating differences, as the Elo system maps this difference to estimated probabilities of each player winning.
Beyond the baseline model, we considered Logistic Regression models both with and without intercept terms (the "biased" and "unbiased" models, respectively), the standard Decision Tree and Random Forest models decision-tree based models, and the boosting models HGBoost and XGBoost.

We trained these models on the features which optimized their cross-validation accuracy: for the unbiased logistic regression, those features were Elo differential, total advantage, differential in the number of move boosters, and differential in the number of ability boosters. 
The remaining models trained on all of those features plus type diversity differential and total stat differential.

Accuracy was chosen over other metrics for its ease of interpretation and because our application does not require special precautions against “false positives and negatives”, such as applications in, e.g., medical diagnosis. 
Additionally, we wanted to select a model that was <i>well-calibrated</i>&hairsp;: since Player 1 lost in 52% of the matches, we wanted a model which would predict that Player 1 would lose approximately 52% of the time.

On our training data, the baseline- and unbiased Logistic Regression models were 52.1% and 53.1% accurate, and both were well-calibrated. The remaining models had accuracies all close to the former two, but were poorly calibrated, leading us to select the unbiased logistic regression as our final model.


### Conclusions

After testing several supervised learning models, including Logistic Regression, Random Forest, and XGBoost, on our dataset of battle replays, an unbiased Logistic Regression model was our model of choice. After training on data from about 13,000 random battles, said model only acheived a test-data accuracy of 53.6%. 
As this is not much better than a coin flip's accuracy of 50%, we conclude that the level and move-set scaling performed by Pokémon Showdown for Gen-9 random battles is sufficiently balanced to maintain interesting and unpredictable gameplay.