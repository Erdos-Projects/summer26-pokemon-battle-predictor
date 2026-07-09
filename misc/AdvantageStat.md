# Damage approximator `dmg` and Advantage stat `adv`

## Motivation: trying to quantify "advantange"

Rather than giving the model a bunch of basic information (types, stats, known moves) and hoping that the model learns the stuff we already know (Fire > Grass > Water > Fire), let's tell the model the stuff that we already know.  But how do you feed in the type chart and whatnot into the model?  Seems hard.

Instead, let's bake all of our knowledge into a set of offensive and defensive stats (we'll call these "advantage" stats) that are derived for each specific battle.  Then, we'll replace the basic stats with these "advantage" stats.

We will start off by neglecting the movepool.  We could try to map each move to its category, type, and base power, but that could be a lot of work.  It's something to explore in the future.


## Damage Approximator

$\newcommand{\M}{\mathrm{M}}$
$\newcommand{\Atk}{\mathrm{Atk}}$
$\newcommand{\Defen}{\mathrm{Def}}$
$\newcommand{\SpAtk}{\mathrm{SpAtk}}$
$\newcommand{\SpDef}{\mathrm{SpDef}}$
The advantage stat starts with an approximation of damage. Given Pokemon $\M_1$ and $\M_2$ from Team 1 and Team 2, respectively, we approximate the <u>expected damage</u> $\mathrm{dmg}(\M_1,\M_2)$, a fraction of $H_2$ (the hit points of $\M_2$), that $\M_1$ does to $\M_2$ by selecting its best STAB move[^1]. Although different moves have different base *Power*s, we set $\mathrm{Power}=80$ for all moves for simplicity.

[^1]: Or a not-very-effective coverage move in the event that is better--this could be updated if we get data suggesting that in the event that a mon's best move is a coverage move, the coverage move is often neutral or better.

In addition, we define the <u>Effective</u> Attacking and Defending Stats $A_i$ and $D_i$ of $\M_i$ as follows: if $i \in \{1,2\}$, let $i'$ be the "complementary" element of $\{1,2\}$, so that $\{i,i'\} = \{1,2\}$. Then
$$ 
    A_i := \max\{\Atk_i, \SpAtk_i\} 
    \qquad\text{and}\qquad
    D_{i'} := \begin{cases}
        \Defen_{i}, & A_{i} = \Atk_i, \\
        \SpDef_{i}, & A_{i} = \SpAtk_{i},
    \end{cases}
$$
and *vice-versa* for $A_{i'}$ and $D_{i}$. Letting $L_i$ and $H_i$ be the Level and HP of $\M_i$, we set
$$
    \mathrm{dmg}(\M_{1},\M_{2}) := \frac{0.925}{H_2} \left(\frac{ 80\left(\tfrac{2}{5} L_{1} + 2\right) \cdot \frac{A_1}{D_2}}{50} + 2\right) \cdot E(\M_{1}, \M_{2}),
$$
where the <u>Effectiveness Multiplier</u>
$$ 
    E(\M_{1}, \M_{2}) := \max\left\{
        \frac{1}{2},\,\,
        1.5 \cdot \max_{T_1 \in \mathrm{Types}(\M_{1})} \mathrm{eff}(T_1, T_2)\mathrm{eff}(T_1, T_2'),
        \right\} 
$$

with $\text{eff}(T_1, T_2)$ being determined by the Type Chart, so that, e.g., 
$$ 
    \text{eff}(\text{water},\text{fire}) = 2, \qquad\text{and}\qquad \text{eff}(\text{fire},\text{water}) = \frac{1}{2}.
$$

Some notes:
- We allow $\mathrm{dmg}$ to exceed 1, as the amount by which it exceeds 1 may actually matter (think: reflect/light screen/aurora veil or resistance berries).
- The definition of $\mathrm{dmg}$ above uses a simplified version of the damage formula found [here](https://bulbapedia.bulbagarden.net/wiki/Damage#Generation_V_onward)
- For simplicity, we have set the base Powers of the moves used to be all be 80, which is the source of that factor in the formula.
- The factor $0.925$ is the mean of a $\mathrm{Unif}(0.85,1)$ random variable.

Notes for $E$:
- $E$ is meant to approximate the product of $\mathrm{STAB}$ and Type.
- The formula for $E$ inherently assumes that $M_1$ is only using STAB moves (this is the factor of $1.5$ present there); this could be updated to account for coverage moves in a future iteration on this stat.
- The $\max\{\frac{1}{2}, \cdot\}$ in $E(\M_1,\M_2)$ is to prevent $E$ from having value 0. It is very rare (though it does happen) that $M_1$ will be unable to damage $M_2$. The factor of $\frac{1}{2}$ is used because that is a multiplier for a "not-very-effective" coverage move. This could be resolved by replacing the maximum over $T_1$ by a maximum over $M_1$'s move types.

More Notes:
- Damage or speed-boosting items are not be accounted for. This could be resolved in an ad-hoc way by checking for common boosting items (choice items, life orb), or resolved in a systemic way using the Smogon damage calculator to replace the offensive advantage stat.
- Damage/stat-modifying abilities like Levitate, Thick Fat, or Sword of Ruin are not accounted for. This could 'only' be resolved by using the Smogon damage calculator to replace this offensive advantage stat.
- Type chart modifying moves like Freeze-Dry are not accounted for.


## Advantage

The only (relevant) thing that doesn't go into the damage approximator is speed. Speed is difficult to incorporate into advantage. There are a few reasons for this:
  1. The only important feature of speed differential (meaning $S_{1} - S_{2}$) is its sign; magnitude is meaningless here, so multiplying $\mathrm{dmg}$ by speed differential would be a bad idea.
  2. The impact of speed differential can be large or small.  If you consider a hypothetical Weavile versus Iron Boulder matchup, each has a super-effective STAB on the other (meaning it has a type-multiplier equal to 3)!  In that situation, Weavile has the advantage because it goes first.  However, if you consider a Weavile versus Swampert matchup (where each has a type-multiplier of 1.5), the Swampert has the advantage in spite of its speed disadvantage due to its overall bulk.  My initial thought is that speed matters a lot when both pokemon are doing about the same amount of damage to one another, but doesn't matter very much when the pokemon are doing very different amounts of damage.  So 'having a speed advantage' should not correspond to a constant factor.

Also worth noting is that advantage depends not just on how much damage you're doing to your opponent, but how much damage your opponent is doing to you!

$\newcommand{\Mon}{\mathrm{Mon}}$

Maybe try computing 'turns to KO' for each mon and look at differential.  Let's set
$$
    \mathrm{ttko}(\M_{1},\M_{2}) = \left\lceil \frac{1}{\mathrm{dmg}(\M_{1},\M_{2})} \right\rceil
$$
So we get something like
$$ 
    \Delta_{\mathrm{ttko}{}}(\M_{1},\M_{2}) = \mathrm{ttko}(\M_1,\M_2) - \mathrm{ttko}(\M_1,\M_2).
$$

Here, bigger is better for $\M_{1}$.

Properties that I want for $\mathrm{adv}$:
- There should be a nice relationship between $\mathrm{adv}(\M_1,\M_2)$ and $\mathrm{adv}(\M_2,\M_1)$, ($a+b=1$ with $0 < a,b < 1$?  $ab = 1$?)
- If $\Delta_{\mathrm{ttko}} \approx 0$ and both $\mathrm{ttko} \approx 1$, the faster Mon should have a large $\mathrm{adv}$, as the faster Mon just OHKOs the slower Mon with no cost.
- If $\Delta_{\mathrm{ttko}} \approx 0$ but both $\mathrm{ttko} \gg 1$, then the faster Mon should one have a small advantage, as here the faster Mon eventually KOs the slower Mon, but both inflict comparable damage on each other.
- If $\Delta_{\mathrm{ttko}} \gg 1$, the Mon with the smaller $\mathrm{ttko}$ should have a big advantage, as here one Mon clearly overpowers the other.



So maybe $\mathrm{adv}$ should represent something like: expected total damage dealt to opponent in a 1v1 matchup? If we let $n$ denote the round number <u>in which the KO occurs</u>, then the faster Mon gets to go $n$ times and the slower Mon gets to go $n$ or $n-1$ times depending on who wins. 

Then

$$
    \mathrm{toko}(\M_{1},\M_{2}) = \min\Big\{\mathrm{ttko}(\M_{1},M_{2}), \mathrm{ttko}(\M_{2},\M_{1})\Big\}
$$
So

$$
\mathrm{dmg}_{\mathrm{ovo}}(\M_{1},\M_{2}) =
\begin{cases}
    \mathrm{dmg}(\M_{1},\M_{2})\cdot \big({\mathrm{toko}(\M_{1},\M_{2}) - 1}\big)  &\text{if $S_1 < S_2$ and $\M_2$ KOs $\M_1$},\\
    \mathrm{dmg}(\M_{1},\M_{2})\cdot \mathrm{toko}(\M_{1},\M_{2})         &\text{else.}
\end{cases}
$$

Then we can do something like set 
$$
    \mathrm{adv}(\M_{1},\M_{2}) := \mathrm{dmg}_{\mathrm{ovo}}(\M_{1},\M_{2})
$$
or we can do something fancy and make it symmetric like 
$$
    \mathrm{adv}(\M_{1},M_{2}) := \mathrm{dmg}_{\mathrm{ovo}}(\M_{1},\M_{2}) - \mathrm{dmg}_{\mathrm{ovo}}(\M_{2},\M_{1}).
$$

Regardless, this should be enough to get started.



## Potential problems with advantage stats

Some pokemon are not good because of their stats.  Take Sableye for example.  It has atrocious stats, but can win a match on the strength of its ability, Prankster.  These advantage stats won't account for that.  (On the other hand, neither will training on 12-dimensional info above.)

Other pokemon don't rely on their offensive stats for damage (think Toxapex).

Yet more pokemon rely heavily on priority moves.
# Testing

In order to test the FullPokemon class, we need:

Testing Effectiveness multiplier $E(\M_1,\M_2)$:
  - $\M_{1}$ has a $4\times$ effective STAB ($\M_{1}$ = Weavile, $\M_{2}$ = Salamence)
  - $\M_{1}$ has a $2\times$ effective STAB ($\M_{1}$ = Weavile, $\M_{2}$ = Haxorus)
  - $\M_{1}$'s best STAB is neutral ($1\times$) ($\M_{1}$ = Weavile, $\M_{2}$ = Corviknight)
  - $\M_{1}$'s best STAB is $\frac{1}{2}\times$ effective ($\M_{1}$ = Weavile, $\M_{2}$ = Chien-Pao)
  - $\M_{1}$'s best STAB is $\frac{1}{4}\times$ effective ($\M_{1}$ = Conkeldurr, $\M_{2}$ = Fezandipiti)
  - $\M_{1}$'s best STAB is $0\times$ effective ($\M_{1}$ = Banette, $\M_{2}$ = Wigglytuff)  

Testing $\mathrm{dmg}$:
  - already tested manually by comparing physical and special attackers on the calcs at calc.pokemonshowdown.com

Testing $\mathrm{dmg}_{\mathrm{ovo}}$:
  - $\M_{1}$ is faster than $\M_{2}$ and KOs $\M_{2}$ ($\M_{1}$ = Weavile, $\M_{2}$ = Salamence)
  - $\M_{2}$ is faster than $\M_{1}$ and KOs $\M_{1}$ ($\M_{1}$ = Sinistcha?, $\M_{2}$ = Weavile)
  - $\M_{1}$ is faster than $\M_{2}$ yet is KOd by $\M_{2}$ ($\M_{1}$ = Weavile, $\M_{2}$ = Conkeldurr)
  - $\M_{2}$ is faster than $\M_{1}$ yet is KOd by $\M_{1}$ ($\M_{1}$ = Swampert, $\M_{2}$ = Corviknight?)
  - $\M_{1}$ and $\M_{2}$ have a speed tie ($\M_{1}$ = Lanturn, $\M_{2}$ = Toxtricity)