# Notes on computing Pokémon stats

---

### Stats and Parameters
All Pokémon have a $\text{Level} \in [1..100]$, and the six integer-valued *Stats*:  
$$
\text{HP,  Attack,  Defense,  Special Attack,  Special Defense},\,\,\text{and}\,\,\text{ Speed},
$$
The actual *values* of these stats depend on several parameters which differ both for each Pokémon and for each stat $X$. For fixed Pokémon $P$ and a fixed stat 
$X$, they are:
1. $B=B_{X} \in [0..255]$, the *Base Value* (BV). Base Values are immutable, set by Nintendo for each Pokémon in each generation/game.
2. $E=E_X \in [0..255]$, the *Effort Value* (EV). Set during team generation.
3. $I=I_X \in [0..31]$, the *Individual Value* (IV). Set during team generation.
4. $N=N_X \in \{0.9,1.0,1.1\}$, the *Nature Multiplier* (my term). This is explained in a subsequent section.

### Computing actual stat values  
Fix a Pokémon $P$, let $L$ be its Level, and let $N$ be its **Nature**. For each stat $X$, let 

```math
    Q = Q_X := \Big({2B+I+\lfloor \tfrac{E}{4} \rfloor}\Big)\frac{L}{100} \qquad (B=B_X,\,\text{etc.})
```

Then $\mathrm{HP}$ is computed via
    $$ \mathrm{Value}(\mathrm{HP}) = \lfloor Q \rfloor + L + 10, $$
and the remaining five stats (Attack, Defense, etc.) are computed via
    $$ \mathrm{Value}(X) = \big\lfloor (Q_{X}+5)N_{X} \big\rfloor. $$

### Nature Multipliers

<span style="color:red">Note:</span> The `Nature` attribute does not feature in `gen9randombattle`. 

Natures are "categories/types" (e.g. *Adamant*, *Hardy*) that *raise* one non-HP stat $10\%$ and *lower* one non-HP stat $10\%$; some actually "do nothing" because they both "raise and lower" the same stat. Thus, we have the following table of multipliers for each Nature;  

<div style="text-align:center">
(For easier reading, "." means $1$) 

| (Nat\Stat) | Atk | Def | SpA | SpD | Spe |
|------------|:---:|:---:|:---:|:---:|:---:|
| Adamant    | 1.1 |  .  | 0.9 |  .  |  .  |
| Bashful    |  .  |  .  |  .  |  .  |  .  |
| Bold       | 0.9 | 1.1 |  .  |  .  |  .  |
| Brave      | 1.1 |  .  |  .  |  .  | 0.9 |
| Calm       | 0.9 |  .  |  .  | 1.1 |  .  |
| Careful    |  .  |  .  | 0.9 | 1.1 |  .  |
| Docile     |  .  |  .  |  .  |  .  |  .  |
| Gentle     |  .  | 0.9 |  .  | 1.1 |  .  | 
| Hardy      |  .  |  .  |  .  |  .  |  .  |
| Hasty      |  .  | 0.9 |  .  |  .  | 1.1 | 
| Impish     |  .  | 1.1 | 0.9 |  .  |  .  | 
| Jolly      |  .  |  .  | 0.9 |  .  | 1.1 | 
| Lax        |  .  | 1.1 |  .  | 0.9 |  .  | 
| Lonely     | 1.1 | 0.9 |  .  |  .  |  .  |
| Mild       |  .  | 0.9 | 1.1 |  .  |  .  | 
| Modest     | 0.9 |  .  | 1.1 |  .  |  .  | 
| Naive      |  .  |  .  |  .  | 0.9 | 1.1 |
| Naughty    | 1.1 |  .  |  .  | 0.9 |  .  | 
| Quiet      |  .  |  .  | 1.1 |  .  | 0.9 | 
| Quirky     |  .  |  .  |  .  |  .  |  .  |
| Rash       |  .  |  .  | 1.1 | 0.9 |  .  | 
| Relaxed    |  .  | 1.1 |  .  |  .  | 0.9 | 
| Sassy      |  .  |  .  |  .  | 1.1 | 0.9 | 
| Serious    |  .  |  .  |  .  |  .  |  .  |
| Timid      | 0.9 |  .  |  .  |  .  | 1.1 |

</div>
