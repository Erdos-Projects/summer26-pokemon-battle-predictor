# Notes on computing pokemon stats

**<u>Basic Stats:</u>**
1. HP
2. Attack ($A$)
3. Defense ($D$)
4. Speed ($S$)
5. Special Attack ($S_A$)
6. Special Defense ($S_D$)

**<u>Stat Parameters</u>**  
Computing the value of any of the above stats requires additional parameters. These differ for each Pokemon *and each stat* $X$:
1. $B=B_{X} \in [0..255]$ is the *Base Value* (BV); these are immutable, fixed by Nintendo for each pokemon in each game.
2. $E=E_X \in [0..255]$ is the *Effort Value* (EV); to be given by Team Generator
3. $I=I_X \in [0..31]$ is the *Individual Value* (IV); to be given by Team Generator
4. $N=N_X \in \{0.9,1.,1.1\}$ is the *Nature Multiplier* (my term); more on that in a bit.

**<u>Computing actual stat values</u>**  
Fix a Pokemon $P$, let $L$ be its **Level**, and let $N$ be its **Nature**. For each stat $X$, let 
    $$ Q = Q_X := \Big({2B+I+\lfloor \tfrac{E}{4} \rfloor}\Big)\frac{L}{100} \qquad (B=B_X,\,\text{etc.})$$
Then $\mathrm{HP}$ is computed via
    $$ \mathrm{Value}(\mathrm{HP}) = \lfloor Q \rfloor + L + 10, $$
and the remaining five stats (Attack, Defense, etc.) are computed via
    $$ \mathrm{Value}(X) = \big\lfloor (Q_{X}+5)N_{X} \big\rfloor. $$

**<u>Nature Multipliers</u>**
<span style="color:red">Update/Note:</span> Ostensibly the `Nature` attribute does not feature in `gen9randombattle`?  
Natures are just "categories/types" (e.g. *Adamant*, *Hardy*) that *raise* one non-HP stat $10\%$ and *lower* one non-HP stat $10\%$; some actually "do nothing" because they both "raise and lower" the same stat. Thus, we have the following table of multipliers for each Nature;  

(For easier reading, "." means $1$) 

| (Nat\Stat) | Atk | Def | SpA | SpD | Spe |
|---|:---:|:---:|:---:|:---:|:---:|
| Adamant | 1.1 | . | 0.9 | . | . |
| Bashful | . | . | . | . | . |
| Bold | 0.9 | 1.1 | . | . | . |
| Brave | 1.1 | . | . | . | 0.9 |
| Calm | 0.9 | . | . | 1.1 | . |
| Careful | . | . | 0.9 | 1.1 | . |
| Docile | . | . | . | . | . |
| Gentle | . | 0.9 | . | 1.1 | . | 
| Hardy | . | . | . | . | . |
| Hasty | . | 0.9 | . | . | 1.1 | 
| Impish | . | 1.1 | 0.9 | . | . | 
| Jolly | . | . | 0.9 | . | 1.1 | 
| Lax | . | 1.1 | . | 0.9 | . | 
| Lonely | 1.1 | 0.9 | . | . | . |
| Mild | . | 0.9 | 1.1 | . | . | 
| Modest | 0.9 | . | 1.1 | . | . | 
| Naive | . | . | . | 0.9 | 1.1 |
| Naughty | 1.1 | . | . | 0.9 | . | 
| Quiet | . | . | 1.1 | . | 0.9 | 
| Quirky | . | . | . | . | . |
| Rash | . | . | 1.1 | 0.9 | . | 
| Relaxed | . | 1.1 | . | . | 0.9 | 
| Sassy | . | . | . | 1.1 | 0.9 | 
| Serious | . | . | . | . | . |
| Timid | 0.9 | . | . | . | 1.1 | 

----

```python
NAT_MULTS = {
    "Adamant": [1.1, 1., 0.9, 1., 1.],
    "Bashful": [1., 1., 1., 1., 1.],
    "Bold":    [0.9, 1.1, 1., 1., 1.],
    "Brave":   [1.1, 1., 1., 1., 0.9],
    "Calm":    [0.9, 1., 1., 1.1, 1.],
    "Careful": [1., 1., 0.9, 1.1, 1.],
    "Docile":  [1., 1., 1., 1., 1.],
    "Gentle":  [1., 0.9, 1., 1.1, 1.],
    "Hardy":   [1., 1., 1., 1., 1.],
    "Hasty":   [1., 0.9, 1., 1., 1.1],
    "Impish":  [1., 1.1, 0.9, 1., 1.],
    "Jolly":   [1., 1., 0.9, 1., 1.1],
    "Lax":     [1., 1.1, 1., 0.9, 1.],
    "Lonely":  [1.1, 0.9, 1., 1., 1.],
    "Mild":    [1., 0.9, 1.1, 1., 1.],
    "Modest":  [0.9, 1., 1.1, 1., 1.],
    "Naive":   [1., 1., 1., 0.9, 1.1],
    "Naughty": [1.1, 1., 1., 0.9, 1.],
    "Quiet":   [1., 1., 1.1, 1., 0.9],
    "Quirky":  [1., 1., 1., 1., 1.],
    "Rash":    [1., 1., 1.1, 0.9, 1.],
    "Relaxed": [1., 1.1, 1., 1., 0.9],
    "Sassy":   [1., 1., 1., 1.1, 0.9],
    "Serious": [1., 1., 1., 1., 1.],
    "Timid":   [0.9, 1., 1., 1., 1.1],
}
```