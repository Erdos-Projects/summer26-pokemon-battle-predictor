# Balancing Random Pokémon Battles

<u>Contributors:</u> Taylor Daniels, Xiaoyu Huang, Greg Knapp, Mohammed Mannan, Marz Newman 

**[Project Summary](./docs/ExecutiveSummary.pdf)** | **[Presentation Slides](./docs/Slides.pdf)**

------------------------------------------------------------
## Overview

#### Directory Structure
```
summer26-pokemon-battle-predictor/
├─ data/
│  └─ replays/
├─ docs/ # extra documentation and write-ups
├─ modeling/
├─ misc/
├─ parallel_computation/ # for computing "advantage" at-scale.
└─ tools/ 
```

#### Models and Results: 
See [Final_EDA_Summary.ipynb](modeling/Final_EDA_Summary.ipynb) and [Final_Modeling_Summary.ipynb](modeling/Final_Modeling_Summary.ipynb).

### Table of Contents
1. [Summary](#summary)
2. [Data Collection and Processing](#data-collection-and-processing)
3. [Feature Engineering](#feature-engineering)
4. [Model Selection](#model-selection)
5. [Conclusions](#conclusions)

------------------------------------------------------------
### Summary
If you had to build two teams of Pokémon to battle, how do you give both teams a fair chance? 
With over 1,000 Pokémon to choose from, each with types, abilities, move-sets, and 
individual stats, the number of possible teams is astronomical. What if you had to do this *randomly*? 
This is exactly the issue that the developers of [Pokémon Showdown](http://play.pokemonshowdown.com) (“Showdown”) grapple with in curating
their most popular game format: the *Gen-9 Random Battle*. 

Ideally, random teams should be balanced so that both players have even chances of winning at match start. 
Our work in this project tries to analyze just how "well-balanced" (at least, roughly!) these random teams are, by seeing if we can predict a battle’s winner just using the matchup data at battle start.

------------------------------------------------------------
### Data Collection and Processing

For our analyses, we collected, parsed, and cleaned the text logs for about 18,000 random battles, sourced from Showdown's replay database. 
A walkthrough of our workflow for this is written-up in [DataProcessingNotes](./docs/DataProcessingNotes.md).

<img style="display: block; margin-left: auto; margin-right: auto; margin-top: 0; margin-bottom: 0;scale: 60%; border: 5px solid #365687; max-width: 800px; max-height:600px"  src='./misc/hurdle.png'/>

One notable difficulty in this cleaning was the following: in each random battle, players' Pokémon are not logged until they are individually fielded. In order to "complete" our information about the random battles, we had to interface with Showdown's source code to re-generate the complete team rosters for each battle; this process is detailed in [GettingFullTeams.md](./tools/GettingFullTeams.md).

------------------------------------------------------------
### Feature Engineering

There are a large number of features to consider in modeling teams of six Pokémon. 
In addition to Pokémon's *base stats* (like HP or Attack) and players’ *Elo ratings* 
(See either [Ratings](./docs/Ratings.md) or 
[Wikipedia](https://en.wikipedia.org/wiki/Elo_rating_system)), 
and other team-based statistics, we introduced the *Advantage* statistic for 1v1 Pokémon encounters, and included the aggregate *Team Advantage* statistic for our model training. 
The Advantage statistic is detailed in [AdvantageStat](./docs/AdvantageStat.md).
    
While Team Advantage was our most impactful feature, it has known drawbacks, such as failing to consider the specific moves or abilities for each Pokémon. 
In an attempt to address some of these drawbacks, we also considered the <i>Stat-Booster Differential</i>&mdash; the difference in the numbers of Pokémon on each team having "stat-boosting" moves or abilities. 

Moreover, newer versions of the Advantage stat that incorporate more of Showdown's battle source code have been developed (and are continuing to be developed). 

------------------------------------------------------------
### Model Selection

For a “baseline” model, it was sensible to use a single-feature predictor based on players’ Elo differences, as the Elo system maps this difference to (estimated) probabilities of each player winning.
In addition, we considered Logistic Regression models both with and without intercept terms (the "biased" and "unbiased" models, respectively), the standard Decision Tree and Random Forest models, 
and the "boosted" models HGBoost and XGBoost.

We trained our models on the features which optimized their cross-validation accuracy: for the unbiased logistic regression, these were Elo differential, team advantage, and stat-booster 
differential. 
The remaining models trained on all of those features, plus the type-diversity and total-stat differentials.

Accuracy was chosen over other metrics for its ease of interpretation and because our application does not require precautions against false positives and negatives (as one might have in, e.g., medical diagnoses). 
Additionally, we wanted to select a model that was <i>well-calibrated</i>&hairsp;: since Player 1 lost in 52% of the matches, we wanted a model which would predict that Player 1 would lose approximately 52% of the time.

On our training data, the baseline- and unbiased Logistic Regression models were 52.1% and 53.1% accurate, and both were well-calibrated. The remaining models had accuracies all close to the former two, but were poorly calibrated, leading us to select the unbiased logistic regression as our final model.

------------------------------------------------------------
### Conclusions

After testing several supervised learning models, including Logistic Regression, Random Forest, and XGBoost, on our dataset of battle replays, an unbiased Logistic Regression model was our model of choice. 
After training on data from about 13,000 random battles, said model only achieved a test-data accuracy of 53.6%. 
As this is not much better than a coin flip's accuracy of 50%, we conclude that the level and move-set scaling performed by Pokémon Showdown for Gen-9 random battles is sufficiently balanced to maintain interesting and unpredictable gameplay.

------------------------------------------------------------
> [!NOTE]
> This project work was part of the Erdős Institute's Summer 2026 Data Science Boot Camp.