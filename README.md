# Pokémon Random Battle Predictor

<u>Contributors:</u> Taylor Daniels, Xiaoyu Huang, Greg Knapp, Mohammed Mannan, Marz Newman 

**[Project Summary](./documentation/ExecutiveSummary.pdf)** | **[Presentation Slides](./documentation/PokemonBattlePredictorSlides.pdf)**


## Overview

#### <u>Directories:</u>

* `/data` contains both our model-training data, and details of our collection and cleaning processes.
* `/documentation` contains a number of detailed write-ups on theoretical tools and motivations for parts of our work.
* `/misc` contains assorted tools and tests for odds-and-ends.
* `/tools` contains the core Python files used in our data collection and feature engineering.

#### <u>Models and Results:</u> 
See [Final_EDA_Summary.ipynb](./Final_EDA_Summary.ipynb) and [Final_Modeling_Summary.ipynb](./Final_Modeling_Summary.ipynb).


## Summary
On the Pokémon battle emulator [Pokémon Showdown](http://play.pokemonshowdown.com) (“Showdown”), the *Generation-9 Random Battle*, where players compete with teams of six randomly selected Pokémon, is currently the most popular game format. Ideally, the Pokémon on these randomly generated teams should be "evenly balanced"  so that, on average, both players have nearly equal chances of winning.

From the Showdown developers’ perspective, there are a number of factors and methods to consider in designing this balanced gameplay. Some primary features to consider are Pokémon's <i>stats</i> (e.g., HP, Attack, Defense) and <i>types</i> (e.g., Fire, Psychic, Ground), and players’ *Elo ratings* (See either [Ratings.md](./documentation/Ratings.md) or [Wikipedia](https://en.wikipedia.org/wiki/Elo_rating_system) for details).  We aim to investigate whether or not the team generation procedure is balanced. If Showdown’s team construction algorithm is balanced, then we expect that comparison of said features should not strongly indicate a player's chance of winning.

---
### Data Collection

Our models were trained and tested on cleaned battle logs for about 18,000 random battles sourced from Showdown's replay database. Our process for collecting, parsing, and cleaning 
these battle logs is detailed in [DataProcessingNotes.md](./documentation/DataProcessingNotes.md).

<img style="display: block; margin-left: auto; margin-right: auto; margin-top: 0; margin-bottom: 0;scale: 70%; border: 5px solid #365687;" src="./misc/hurdle.png"/>

One notable difficulty in this cleaning was the following: in each random battle, players' Pokémon are neither visible (nor even logged) until they are individually fielded.
Our method for interfacing with Showdown's source code in order to re-generate the complete team rosters in each battle is outlined in [ComputingTeams.md](./documentation/ComputingTeams.md).

---
### Feature Engineering

There are a large number of potential features to consider in modeling teams of six Pokémon. In addition to Pokémon's *base stats* (HP, Attack, Defense, etc.), our models also incorporate:
    <ul>
        <li><strong>Type Diversity&hairsp;:</strong> The number of unique Pokémon types on a team;</li>
        <li><strong>Pokémon <i>Advantage</i>&hairsp;:</strong> A custom statistic approximating the expected difference in total damage that two opposing Pokémon would exchange in a one-on-one 
match; see [AdvantageStat.md](./documentation/AdvantageStat.md) for details.</li>
        <li><strong>Team Advantage&hairsp;:</strong> The cumulative sum of the Advantages for all 36 possible pairs of opposing Pokémon from each team.</li>
    </ul>
    While Team Advantage was our most impactful feature, it has known drawbacks, such as failing to consider the specific moves or abilities for each Pokémon. In an attempt to address this we 
introduced the <i>Stat-Booster Differential</i>, which records the difference in the number of Pokémon on each team that have stat-boosting moves or abilities.


---
### Model Selection

For a “baseline” model, it was sensible to use a single-feature predictor based on players’ Elo rating differences, as the Elo system maps this difference to estimated probabilities of each player winning.
In addition, we considered Logistic Regression models both with and without intercept terms (the "biased" and "unbiased" models, respectively), the standard Decision Tree and Random Forest models, 
and the "boosted" models HGBoost and XGBoost.

We trained our models on the features which optimized their cross-validation accuracy: for the unbiased logistic regression, these were Elo differential, team advantage, and stat-booster 
differential. 
The remaining models trained on all of those features, plus the type-diversity and total-stat differentials.

Accuracy was chosen over other metrics for its ease of interpretation and because our application does not require precautions against false positives and negatives 
(as one might have in, e.g., medical diagnoses). 
Additionally, we wanted to select a model that was <i>well-calibrated</i>&hairsp;: since Player 1 lost in 52% of the matches, we wanted a model which would predict that Player 1 would lose approximately 52% of the time.

On our training data, the baseline- and unbiased Logistic Regression models were 52.1% and 53.1% accurate, and both were well-calibrated. The remaining models had accuracies all close to the former two, but were poorly calibrated, leading us to select the unbiased logistic regression as our final model.

---
### Conclusions

After testing several supervised learning models, including Logistic Regression, Random Forest, and XGBoost, on our dataset of battle replays, an unbiased Logistic Regression model was our model 
of choice. After training on data from about 13,000 random battles, said model only achieved a test-data accuracy of 53.6%. 
As this is not much better than a coin flip's accuracy of 50%, we conclude that the level and move-set scaling performed by Pokémon Showdown for Gen-9 random battles is sufficiently balanced to maintain interesting and unpredictable gameplay.

---
> [!NOTE]
> This project work was part of the Erdős Institute's Summer 2026 Data Science Boot Camp.