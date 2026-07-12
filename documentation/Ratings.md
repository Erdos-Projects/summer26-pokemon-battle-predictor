# Bradley-Terry; Elo
**Idea:** Players $A$ and $B$ will compete, and exactly one will Win; "Draw" is not allowed for simplicity. The *ratings* $R_A$ and $R_B$ should determine win probabilities according to
```math
    P(\text{$A$ Wins}) = \frac{R_{A}}{R_{A} + R_{B}}
    \qquad\text{and}\qquad
    P(\text{$B$ Wins}) = \frac{R_{B}}{R_{A} + R_{B}}.
```
If $R_{A} = e^{r_{A}}$, $R_{B} = e^{r_{B}}$, then
```math
    P(\text{$A$ Wins}) = \frac{e^{r_A}}{e^{r_{A}} + e^{r_{B}}} = \frac{1}{1 + \exp[-(r_{A}-r_{B})]} 
```
The standard <u>sigmoid</u> function is $S(x) := 1/(1 + e^{-x})$, and lets us compactly say that
```math
   P(\text{$A$ Wins}) = S(r_{A} - r_{B}), 
   \qquad\text{and}\qquad
   P(\text{$B$ Wins}) = S(r_{B} - r_{A})
```
It is interesting to note that $S' = \frac{e^{-x}}{(1+e^{-x})^2} = S(1-S)$.



## Elo

The **Elo** rating system (designed by Arpad Elo&mdash;I think before B-T system?) is essentially the Bradley-Terry system with ratings scaled so that
```math
    P(\text{$A$ Wins}) 
    = S\left((r_A - r_{B})\frac{\log{10}}{400}\right)
    = \frac{1}{1 + 10^{-(r_A - r_B)/400}}.
```
```math
    P(\text{$B$ Wins}) 
    = S\left((r_B - r_{A})\frac{\log{10}}{400}\right)
    = \frac{1}{1 + 10^{-(r_B - r_A)/400}}.
```


### Updates in Elo; "$K$-scaling"

*Suppose everyone has ratings (or is seeded with some rating, maybe 1000?)*. We update ratings after matches as follows: 

1. **(Win Probabilities):** When $A$ and $B$ will play, they can <u>score</u> $ s_A, s_B \in \{0, 1\} = \{\text{Win, Lose}\} $ [$s = \frac{1}{2}$ can be used for $\text{Draw}$]. Because $0$, $1$ are the only possible outcomes, the "*expected scores*" are
    ```math
    E[s_A] = P_A := P(\text{$A$ Wins}) \qquad\text{and}\qquad E[s_B] = P_B := P(\text{$B$ Wins})
    ```
2. **(Simple Ante):** For the match (or larger league/tier), an integer $K > 0$ is fixed, and, *roughly speaking*:
    ```math
       \text{\emph{$A,B$ both ``ante'' points based on their respective win-probabilities; namely they ante $KP_A$, and $KP_B$.}}
    ```
   The winner of the match then "takes the pot" of $K(P_A + P_B) = K$ rating points and adds it to their rating.
3. **(Rating Update):** A convenient way to state/write the above is: "*after a match, a player's rating changes relative to how much they "beat the odds"/"pulled-off an upset"/"choked", scaled by $K$*". Precisely, one takes
    ```math
    \begin{align}
        r_A' &\hspace{0.4em}\leftarrow\hspace{0.4em} r_A + K(s_A - P_A), \\
        r_B' &\hspace{0.4em}\leftarrow\hspace{0.4em} r_B + K(s_B - P_B).
    \end{align}
    ```
4. **(General Ante):** In practice (`PokemonShowdown`: [see here](https://pokemonshowdown.com/pages/ladderhelp.md); `FIDE` (Int'l. Chess Fed.) [see here](https://ratings.fide.com/calc.phtml?page=change)), players use *separate* $K$-values $K_A$ and $K_B$ determined according to some scheme&mdash;usually a piecewise linear/step function or something similarly simple.



# Glicko-1

1. **(Stats):** Players now have two stats, **rating** $r$ and **rating deviation** $d$ (usually written $\mathrm{RD}$ in the literature), with "seed" values of $r=1500$ and $d=350$. Moreover, for brevity let
```math
q := \frac{\log{10}}{400}, \qquad\text{so that}\qquad P_{\text{Elo}}(\text{$A$ Wins}) = S\big({(r_A-r_B)q}\big) = \Big\{1 + \exp\!\big({-(r_A-r_B)q}\big) \Big\}^{-1}.
```

2. **(Probabilities):** Win probabilities for $A$ and $B$ (with $(r_A, d_A)$ and $(r_B, d_B)$) are similar to the $\text{Elo}$ method, but now with the 'deviation' $d$ baked-in. Specifically, 
```math
    P_{\text{Gko}}(\text{$A$ wins}) = S\!\left((r_A - r_B)q \cdot g\!\left((d_A^2+d_B^2)^{\frac{1}{2}}\right) \right),
```
where

```math
    g(x) := \frac{1}{\sqrt{1 + 3q^{2}x^2/\pi^{2}}} \qquad\text{and}\qquad q = \frac{\log 10}{400}.
```

3. **(Rating Update):** Glicko-1 scores are updated for large 'batches' of players and matches, specifically based on all matches within some determined period (`PokemonShowdown` uses 24-hr periods beginning and ending at `9:00 AM GMT+0`). The updating algorithm is akin to a regression/gradient descent, applied to the large "vector" of player scores, but it is somewhat technical, so I'm omitting it here. Outline of Glicko-1 can be found [here](https://glicko.net/glicko/glicko.pdf).


### Misc notes/cautions
* My notes are based on Mark Glickman's brief overview of the Glicko system, posted on his site. This overview is for 'general consumption', so it (and thus my notes) may have some imprecise parts. The 'true source' is a Statistics paper he published in ~1993-1995, but digging into that would be a large time-sink. 
* The brief overview of `Glicko` does <span style="color:red">not</span> say a player's 'true rating' is normal distributed a-la $r_{\text{true}} \sim N(r,D)$; what he *does* say is that:
```math
    \text{ \textit{a $95\%$ confidence interval for  $r_{\text{true}}$ is}} \quad(r - 1.96\mathrm{D}, \,\, r + 1.96\mathrm{D}).
```
On the other hand, the use of $\pm 1.96\mathrm{D}$ is 'suspicious' because that's exactly what you would get for a 95% confidence interval using $N(r,\mathrm{D})$.



# GXE

* "X-Act" was allegedly a mathematician active in Smogon forums long ago (~2008+) who suggested the "*Glicko-X-Act-Rating-Estimate*", shortened to GLIXARE and now **GXE**.
* These notes are based on this [thread](https://www.smogon.com/forums/threads/gxe-glixare-a-much-better-way-of-estimating-a-players-overall-rating-than-shoddys-cre.51169/), in which X-Act outlines the method, and updates the original post after a little discussion. Thus, for completeness the Showdown! source code should be checked against this.
* <span style="color:red">Note:</span> GXE is **not** its own rating system&mdash;it a user-friendly "wrapper" for Glicko-1.

1. **(Idea&mdash;Original):** The GXE rating should be "*the average probability (or %-chance) of beating a randomly-selected opponent (from all users)*". That is, that
```math
\mathrm{GXE}(A) = \frac{1}{\#(\text{Players})} \sum_{B \neq A} P_{\mathrm{Gko}}(\text{$A$ wins over $B$}) \qquad \text{(or divide by $\#(Players)-1$)}.
```
2. **(Actual System):** Let $A$ be a player with stats $(A.r, A.d)$.
    - If $A.d > 100$  then $\mathrm{GXE}(A) := 0$, since uncertainty is too high.
    - If $A.d \leq 100$, the GXE is the percentage-scale $P_{\mathrm{Gko}}$ against the ""average"" player, which is <u>assumed</u> [no comment] to have $(r,d) = (1500, 350)$, i.e., $(r,d)_{\text{seed}}$. Thus we take
    ```math
     P_{\mathrm{GXE}}(A) := S\!\left((r_A - 1500)q \cdot g\!\left((d_A^2+350^2)^{\frac{1}{2}}\right) \right)
    ```
    and then (*per X-Act's description*)
    ```math
    \mathrm{GXE}(A) := \tfrac{1}{100} \texttt{Round}\big({10,\!000 \cdot\! P_{\mathrm{GXE}}(A)}\big)
    ```


# Smogon weighted-usage-stats tiering scheme

<span style="color:orange">Caution:</span> These are based on a 2013/4 [post](https://www.smogon.com/forums/threads/everything-you-ever-wanted-to-know-about-ratings.3487422/) by user `anter`. At present, I have not seen any indication that these weighted-tiering schemes were changed, but it is possible some details might have. Also, I think that while there may have been a time where `Glicko-2` was used by `PS`, they reverted to `Glicko-1` at some point.

**Setup:**
At the end of a period/month, you have:
* Match win/loss data for a bunch of players, who each have `Glicko-1` ratings/stats $(r_{i}, D_{i})$;
* Team compositions (and more) for both players in each match; thus, in reality we have data points $(r_{i}, D_{i}, \mathrm{tm}_{i})$.
* <span style="color:red">Note:</span> Data for both players in a match are listed separately, and are counted "with multiplicity": that is, if player $A$ played 10 matches in a period using the same $\mathrm{tm}_{A}$, then $(r_{A}, D_{A}, \mathrm{tm}_{A})$ is recorded 10 times in the "master list" $\{ (r_{i}, D_{i}, \mathrm{tm}_{i}) : i = 1,\ldots,N\}$. 
**Computation:**
1. Assign "weights" to every player/match (again, including "multiplicity") according to the formula
```math
W_i := W\Big[(r_i, D_i, \mathrm{tm}_{i})\Big] := \frac{1}{2}\left\{ 1 + \mathrm{erf}\left(\frac{r_i - 1500}{\sqrt{2}D_{i}}\right) \right\} \qquad
\text{(so, $\mathrm{tm}_{i}$ isn't actually used here)},
```
thus obtaining some list of weights $\{W_{i} : i=1,\ldots,N\}$.
2. For a Pokemon $\texttt{P}$, the **weighted usage statistic** for $\texttt{P}$, **for the current (ending) period**, call it $T_{0}$, is
```math 
U(\texttt{P};T_{0}) := \frac{\sum_{\,i : \texttt{P} \in \mathrm{tm}_{i}} W_{i} }{ \sum_{i : \text{all}} W_{i} }.
```
5. The "final" weighted usage statistic $U(\texttt{P})$ takes a weighted average over the most recent 3 periods, say $T_{0}$ (current) and $T_{-1}, T_{-2}$:
```math
U(\texttt{P}) := \tfrac{20}{24}U(\texttt{P};T_0) + \tfrac{3}{24}U(\texttt{P};T_{-1}) + \tfrac{1}{24}U(\texttt{P};T_{-2}).
```
4. Per the Smogon post, if a Pokemon was `OU` at period start, and then at period end the weighted usage stat $U(\texttt{P})$ exceeds a threshold percentage, roughly $3.4064\%$, then said Pokemon remains `OU` (presumably else it is demoted to `UU`). One also does this same schema for Pokemon in the `UU` tier (some may be demoted to `RU`, etc...)


#### Caveats:

1. Assumes pre-existing tiers (from older, unweighted/uniformly-weighted usage stats).
2. Unclear how "promotion" can happen, but I think [i'm hitting saturation ATM as I'm writing this], per the text
    > in short, a Pokemon is OU if, in playing 20 battles, there's at least a 50% chance of you encountering that Pokemon at least once

one starts by determining the `OU` tier, then works down.    


# Ladder help 

**<span style="color:green">Note:</span>** The following is a cleaned version of the content pasted from PokemonShowdown (`PS`) page [`ladderhelp.md`](`https://pokemonshowdown.com/pages/ladderhelp.md`)
Our ladder displays three ratings: Elo, GXE, and Glicko-1.

**Elo** is the main ladder rating. It's a pretty normal ladder rating: goes up when you win and down when you lose.

**GXE** (Glicko X-Act Estimate) is an estimate of your win chance against an average ladder player.

**Glicko-1** is a different rating system. It has rating and deviation values.

Note that win/loss should not be used to estimate skill, since who you play against is much more important than how many times you win or lose. Our other stats like Elo and GXE are much better for estimating skill.
## PS Elo and decay
Your rating starts at 1000.

Our Elo implementation uses K-scaling. The $K$ factor is:

* $K = 50$ if Elo is in $[1100, 1299]$
* $K = 40$ if Elo is $ \geq 1300$

We have a rating floor of 1000 (If your rating would fall below 1000, it is set to 1000). This makes it unnecessary to create new accounts to "fix" your rating.

**For Elo in $[1000,1100)$**

If Elo is 1000, $K=80$ for the winner and $K=20$ for the loser. Between 1001 to 1099, K scales linearly from 80 to 50 for the winner and from 20 to 50 for the loser. This helps spread out low ladder people between 1000 and 1100 instead of causing the rating floor to cluster them all at 1000.
### `PS` Elo Rating decay
Above 1400, we have <u>rating decay</u>. Every day at 9 AM GMT+0:

* If you played over 5 games, there is no decay
* If you played 1-5 games, you lose 1 point for every 100 points above 1500 you are
* If you played 0 games, you lose 1 point for every 50 points above 1400 you are

Say you played $g$ games in a day's period (which begin at `9 AM GMT+0` each day).
```math
    δ = \begin{cases}
        0 & g > 5, \\
        \lfloor\frac{r-1500}{100}\rfloor & 1 ≤ g < 5, \\
        \lfloor\frac{r-1400}{50}\rfloor & g=0
    \end{cases}
```

<span style="color:red">Note:</span> Ratings of less popular formats (e.g. not `current gen OU` or `random battles`) decay slightly slower: you lose 2 points less per day due to rating decay in these formats.

Note that there's no "official" Elo standard. K-scaling and rating floors are common, rating decay somewhat common, and our dynamic K scaling seems to be unique.

## PS Glicko-1
Your rating starts at R = 1500, RD = 130.

We use a rating period of 24 hours and an RD range of 25 to 130, with a system constant of 6.6775026092. [Is this $\sigma$?]

**[Personal Note]:** Glicko-1 ratings $\mathrm{R}$ and $\mathrm{RD}$ are stored for `PS`'s users as `rpr` and `rprd`, respectively; namely, one has `user.rpr` and `user.rprd`