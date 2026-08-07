# Damage `dmg` and Advantage `adv`

---

### Motivation: trying to quantify "advantage"

Given the large number of attributes, types, moves, etc. that Pokémon can have, for machine learning purposes it is desirable encode these Pokémon's relative strengths and weaknesses in a 
numerical way.

## Damage Approximator

Our first step is to approximate the damage different Pokémon's attacks can inflict. 
Given Pokémon $M_1$ and $M_2$ from Team 1 and Team 2, respectively, we approximate the <u>expected damage</u> 
$\mathrm{dmg}(M_1,
M_2)$, a 
fraction of $H_2$ (the 
hit points of $M_2$), that $M_1$ does to $M_2$ by selecting its best STAB[^1]. Although different moves have different base *Power*s, we set $\mathrm{Power}=80$ for all moves for simplicity.

[^1]: A Pokémon gains a "Same Type Attack Bonus" (STAB) on moves that match the Pokémon's type(s). 
For example, Thunder has a STAB when used by an Electric-type Pokémon, but not when used by a Normal-type Pokémon.  

In addition, we define the <u>Effective</u> Attacking and Defending Stats $A_i$ and $D_i$ of $M_i$ as follows: if $i \in \{1,2\}$, let $i'$ be the "complementary" element of $\{1,2\}$, so that $\{i,i'\} = \{1,2\}$. Then
```math 
A_i := \max\{\mathrm{Atk}_i, \mathrm{SpAtk}_i\} 
\qquad\text{and}\qquad
D_{i'} := \begin{cases}
    \mathrm{Defen}_{i}, & A_{i} = \mathrm{Atk}_i, \\
    \mathrm{SpDef}_{i}, & A_{i} = \mathrm{SpAtk}_{i},
\end{cases}
```
and *vice versa* for $A_{i'}$ and $D_{i}$. Letting $L_i$ and $H_i$ be the Level and HP of $M_i$, we set
```math
\mathrm{dmg}(M_{1},M_{2}) := \frac{0.925}{H_2} \left(\frac{ 80\left(\tfrac{2}{5} L_{1} + 2\right) \cdot \frac{A_1}{D_2}}{50} + 2\right) \cdot E(M_{1}, M_{2}),
```
where the <u>Effectiveness Multiplier</u>
```math
E(M_{1}, M_{2}) := \max\left\{
    \frac{1}{2},\,\,
    1.5 \cdot \max_{T_1 \in \mathrm{Types}(M_{1})} \mathrm{eff}(T_1, T_2)\mathrm{eff}(T_1, T_2'),
    \right\} 
```

with $\text{eff}(T_1, T_2)$ being determined by the Type Chart, so that, e.g., 
```math
\text{eff}(\text{water},\text{fire}) = 2, \qquad\text{and}\qquad \text{eff}(\text{fire},\text{water}) = \frac{1}{2}.
```

Some notes:
- We allow $\mathrm{dmg}$ to exceed 1, as the amount by which it exceeds 1 may actually matter (think: reflect/light screen/aurora veil or resistance berries).
- The definition of $\mathrm{dmg}$ above uses a simplified version of the damage formula found [here](https://bulbapedia.bulbagarden.net/wiki/Damage#Generation_V_onward).
- For simplicity, we have set the base Powers of the moves used to be all be 80, which is the source of that factor in the formula.
- The factor $0.925$ is the mean of a $\mathrm{Unif}(0.85,1)$ random variable.

Notes for $E$:
- $E$ is meant to approximate the product of $\mathrm{STAB}$ and Type.
- The formula for $E$ inherently assumes that $M_1$ is only using STAB moves (this is the factor of $1.5$ present there); this could be updated to account for coverage moves in a future iteration on this stat.
- The $\max (\frac{1}{2}, \cdot)$ in $E(M_1,M_2)$ is to prevent $E$ from having value 0. It is very rare (though it does happen) that $M_1$ will be unable to damage $M_2$. The factor of $\frac{1}{2}$ is used because that is a multiplier for a "not-very-effective" coverage move. This could be resolved by replacing the maximum over $T_1$ by a maximum over $M_1$'s move types.

More Notes:
- Damage or speed-boosting items are not be accounted for. This could be resolved in an ad-hoc way by checking for common boosting items (choice items, life orb), or resolved in a systemic way using the Smogon damage calculator to replace the offensive advantage stat.
- Damage/stat-modifying abilities like Levitate, Thick Fat, or Sword of Ruin are not accounted for. This could 'only' be resolved by using the Smogon damage calculator to replace this offensive advantage stat.
- Type chart modifying moves like Freeze-Dry are not accounted for.


## Advantage

The only (relevant) thing that doesn't go into the damage approximator is speed. Speed is difficult to incorporate into advantage. There are a few reasons for this:
  1. The only important feature of speed differential (meaning $S_{1} - S_{2}$) is its sign; magnitude is meaningless here, so multiplying $\mathrm{dmg}$ by speed differential would be a bad idea.
  2. The impact of speed differential can be large or small.  If you consider a hypothetical Weavile versus Iron Boulder matchup, each has a super-effective STAB on the other (meaning it has a type-multiplier equal to 3)!  In that situation, Weavile has the advantage because it goes first.  However, if you consider a Weavile versus Swampert matchup (where each has a type-multiplier of 1.5), the Swampert has the advantage in spite of its speed disadvantage due to its overall bulk.  My initial thought is that speed matters a lot when both Pokémon are doing about the same amount of damage to one another, but doesn't matter very much when the Pokémon are doing very different amounts of damage.  So 'having a speed advantage' should not correspond to a constant factor.

Also worth noting is that advantage depends not just on how much damage you're doing to your opponent, but how much damage your opponent is doing to you!

Maybe try computing 'turns to KO' for each mon and look at differential.  Let's set
```math
\mathrm{ttko}(M_{1},M_{2}) = \left\lceil \frac{1}{\mathrm{dmg}(M_{1},M_{2})} \right\rceil
```
So we get something like
```math
\Delta_{\mathrm{ttko}{}}(M_{1},M_{2}) = \mathrm{ttko}(M_1,M_2) - \mathrm{ttko}(M_1,M_2).
```

Here, bigger is better for $M_{1}$.

Reasonable properties for defining $\mathrm{adv}$:
- There should be an intuitive relationship between $\mathrm{adv}(M_1,M_2)$ and $\mathrm{adv}(M_2,M_1)$;
- If $\Delta_{\mathrm{ttko}} \approx 0$ and both $\mathrm{ttko} \approx 1$, the faster Mon should have a large $\mathrm{adv}$, as the faster Mon just OHKOs the slower Mon with no cost.
- If $\Delta_{\mathrm{ttko}} \approx 0$ but both $\mathrm{ttko} \gg 1$, then the faster Mon should one have a small advantage, as here the faster Mon eventually KOs the slower Mon, but both inflict comparable damage on each other.
- If $\Delta_{\mathrm{ttko}} \gg 1$, the Mon with the smaller $\mathrm{ttko}$ should have a big advantage, as here one Mon clearly overpowers the other.



So maybe $\mathrm{adv}$ should represent something like: expected total damage dealt to opponent in a 1v1 matchup? If we let $n$ denote the round number <u>in which the KO occurs</u>, then the faster Mon gets to go $n$ times and the slower Mon gets to go $n$ or $n-1$ times depending on who wins. 

Then

```math
\mathrm{toko}(M_{1},M_{2}) = \min\Big\{\mathrm{ttko}(M_{1},M_{2}), \mathrm{ttko}(M_{2},M_{1})\Big\}
```
So

```math
\mathrm{dmg}_{\mathrm{ovo}}(M_{1}, M_{2}) =
\begin{cases}
\mathrm{dmg}(M_{1},M_{2}) \cdot \big({\mathrm{toko}(M_{1},M_{2}) - 1}\big)  & \text{if } S_{1} < S_2 \text{ and } M_2 \text{ KOs } M_1, \\
\mathrm{dmg}(M_{1},M_{2}) \cdot \mathrm{toko}(M_{1},M_{2})         &\text{else.}
\end{cases}
```

Then we can do something like set 
```math
\mathrm{adv}(M_{1},M_{2}) := \mathrm{dmg}_{\mathrm{ovo}}(M_{1},M_{2})
```
or we can do something fancy and make it symmetric like 
```math
\mathrm{adv}(M_{1},M_{2}) := \mathrm{dmg}_{\mathrm{ovo}}(M_{1},M_{2}) - \mathrm{dmg}_{\mathrm{ovo}}(M_{2},M_{1}).
```

## Potential problems with advantage stats

Some Pokémon are not good because of their stats. Take Sableye for example. It has atrocious stats, but can win a match on the strength of its ability, Prankster.  These advantage stats won't account for that.  (On the other hand, neither will training on 12-dimensional info above.)

Other Pokémon don't rely on their offensive stats for damage (think Toxapex).

Yet more Pokémon rely heavily on priority moves.
