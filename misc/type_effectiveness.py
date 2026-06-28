"""
Pokémon type effectiveness chart (Generation VI onward), as a nested dictionary.

Usage:
    multiplier = TYPE_CHART[attacking_type][defending_type]

For example:
    TYPE_CHART["Fire"]["Grass"]  # -> 2.0 (super effective)
    TYPE_CHART["Water"]["Fire"]  # -> 2.0 (super effective)
    TYPE_CHART["Electric"]["Ground"]  # -> 0.0 (no effect)

Source: https://bulbapedia.bulbagarden.net/wiki/Type#Type_effectiveness
"""

TYPE_CHART = {
    "Normal": {
        "Normal": 1.0, "Fighting": 1.0, "Flying": 1.0, "Poison": 1.0, "Ground": 1.0,
        "Rock": 0.5, "Bug": 1.0, "Ghost": 0.0, "Steel": 0.5, "Fire": 1.0, "Water": 1.0,
        "Grass": 1.0, "Electric": 1.0, "Psychic": 1.0, "Ice": 1.0, "Dragon": 1.0,
        "Dark": 1.0, "Fairy": 1.0,
    },
    "Fighting": {
        "Normal": 2.0, "Fighting": 1.0, "Flying": 0.5, "Poison": 0.5, "Ground": 1.0,
        "Rock": 2.0, "Bug": 0.5, "Ghost": 0.0, "Steel": 2.0, "Fire": 1.0, "Water": 1.0,
        "Grass": 1.0, "Electric": 1.0, "Psychic": 0.5, "Ice": 2.0, "Dragon": 1.0,
        "Dark": 2.0, "Fairy": 0.5,
    },
    "Flying": {
        "Normal": 1.0, "Fighting": 2.0, "Flying": 1.0, "Poison": 1.0, "Ground": 1.0,
        "Rock": 0.5, "Bug": 2.0, "Ghost": 1.0, "Steel": 0.5, "Fire": 1.0, "Water": 1.0,
        "Grass": 2.0, "Electric": 0.5, "Psychic": 1.0, "Ice": 1.0, "Dragon": 1.0,
        "Dark": 1.0, "Fairy": 1.0,
    },
    "Poison": {
        "Normal": 1.0, "Fighting": 1.0, "Flying": 1.0, "Poison": 0.5, "Ground": 0.5,
        "Rock": 0.5, "Bug": 1.0, "Ghost": 0.5, "Steel": 0.0, "Fire": 1.0, "Water": 1.0,
        "Grass": 2.0, "Electric": 1.0, "Psychic": 1.0, "Ice": 1.0, "Dragon": 1.0,
        "Dark": 1.0, "Fairy": 2.0,
    },
    "Ground": {
        "Normal": 1.0, "Fighting": 1.0, "Flying": 0.0, "Poison": 2.0, "Ground": 1.0,
        "Rock": 2.0, "Bug": 0.5, "Ghost": 1.0, "Steel": 2.0, "Fire": 2.0, "Water": 1.0,
        "Grass": 0.5, "Electric": 2.0, "Psychic": 1.0, "Ice": 1.0, "Dragon": 1.0,
        "Dark": 1.0, "Fairy": 1.0,
    },
    "Rock": {
        "Normal": 1.0, "Fighting": 0.5, "Flying": 2.0, "Poison": 1.0, "Ground": 0.5,
        "Rock": 1.0, "Bug": 2.0, "Ghost": 1.0, "Steel": 0.5, "Fire": 2.0, "Water": 1.0,
        "Grass": 1.0, "Electric": 1.0, "Psychic": 1.0, "Ice": 2.0, "Dragon": 1.0,
        "Dark": 1.0, "Fairy": 1.0,
    },
    "Bug": {
        "Normal": 1.0, "Fighting": 0.5, "Flying": 0.5, "Poison": 0.5, "Ground": 1.0,
        "Rock": 1.0, "Bug": 1.0, "Ghost": 0.5, "Steel": 0.5, "Fire": 0.5, "Water": 1.0,
        "Grass": 2.0, "Electric": 1.0, "Psychic": 2.0, "Ice": 1.0, "Dragon": 1.0,
        "Dark": 2.0, "Fairy": 0.5,
    },
    "Ghost": {
        "Normal": 0.0, "Fighting": 1.0, "Flying": 1.0, "Poison": 1.0, "Ground": 1.0,
        "Rock": 1.0, "Bug": 1.0, "Ghost": 2.0, "Steel": 1.0, "Fire": 1.0, "Water": 1.0,
        "Grass": 1.0, "Electric": 1.0, "Psychic": 2.0, "Ice": 1.0, "Dragon": 1.0,
        "Dark": 0.5, "Fairy": 1.0,
    },
    "Steel": {
        "Normal": 1.0, "Fighting": 1.0, "Flying": 1.0, "Poison": 1.0, "Ground": 1.0,
        "Rock": 2.0, "Bug": 1.0, "Ghost": 1.0, "Steel": 0.5, "Fire": 0.5, "Water": 0.5,
        "Grass": 1.0, "Electric": 0.5, "Psychic": 1.0, "Ice": 2.0, "Dragon": 1.0,
        "Dark": 1.0, "Fairy": 2.0,
    },
    "Fire": {
        "Normal": 1.0, "Fighting": 1.0, "Flying": 1.0, "Poison": 1.0, "Ground": 1.0,
        "Rock": 0.5, "Bug": 2.0, "Ghost": 1.0, "Steel": 2.0, "Fire": 0.5, "Water": 0.5,
        "Grass": 2.0, "Electric": 1.0, "Psychic": 1.0, "Ice": 2.0, "Dragon": 0.5,
        "Dark": 1.0, "Fairy": 1.0,
    },
    "Water": {
        "Normal": 1.0, "Fighting": 1.0, "Flying": 1.0, "Poison": 1.0, "Ground": 2.0,
        "Rock": 2.0, "Bug": 1.0, "Ghost": 1.0, "Steel": 1.0, "Fire": 2.0, "Water": 0.5,
        "Grass": 0.5, "Electric": 1.0, "Psychic": 1.0, "Ice": 1.0, "Dragon": 0.5,
        "Dark": 1.0, "Fairy": 1.0,
    },
    "Grass": {
        "Normal": 1.0, "Fighting": 1.0, "Flying": 0.5, "Poison": 0.5, "Ground": 2.0,
        "Rock": 2.0, "Bug": 0.5, "Ghost": 1.0, "Steel": 0.5, "Fire": 0.5, "Water": 2.0,
        "Grass": 0.5, "Electric": 1.0, "Psychic": 1.0, "Ice": 1.0, "Dragon": 0.5,
        "Dark": 1.0, "Fairy": 1.0,
    },
    "Electric": {
        "Normal": 1.0, "Fighting": 1.0, "Flying": 2.0, "Poison": 1.0, "Ground": 0.0,
        "Rock": 1.0, "Bug": 1.0, "Ghost": 1.0, "Steel": 1.0, "Fire": 1.0, "Water": 2.0,
        "Grass": 0.5, "Electric": 0.5, "Psychic": 1.0, "Ice": 1.0, "Dragon": 0.5,
        "Dark": 1.0, "Fairy": 1.0,
    },
    "Psychic": {
        "Normal": 1.0, "Fighting": 2.0, "Flying": 1.0, "Poison": 2.0, "Ground": 1.0,
        "Rock": 1.0, "Bug": 1.0, "Ghost": 1.0, "Steel": 0.5, "Fire": 1.0, "Water": 1.0,
        "Grass": 1.0, "Electric": 1.0, "Psychic": 0.5, "Ice": 1.0, "Dragon": 1.0,
        "Dark": 0.0, "Fairy": 1.0,
    },
    "Ice": {
        "Normal": 1.0, "Fighting": 1.0, "Flying": 2.0, "Poison": 1.0, "Ground": 2.0,
        "Rock": 1.0, "Bug": 1.0, "Ghost": 1.0, "Steel": 0.5, "Fire": 0.5, "Water": 0.5,
        "Grass": 2.0, "Electric": 1.0, "Psychic": 1.0, "Ice": 0.5, "Dragon": 2.0,
        "Dark": 1.0, "Fairy": 1.0,
    },
    "Dragon": {
        "Normal": 1.0, "Fighting": 1.0, "Flying": 1.0, "Poison": 1.0, "Ground": 1.0,
        "Rock": 1.0, "Bug": 1.0, "Ghost": 1.0, "Steel": 0.5, "Fire": 1.0, "Water": 1.0,
        "Grass": 1.0, "Electric": 1.0, "Psychic": 1.0, "Ice": 1.0, "Dragon": 2.0,
        "Dark": 1.0, "Fairy": 0.0,
    },
    "Dark": {
        "Normal": 1.0, "Fighting": 0.5, "Flying": 1.0, "Poison": 1.0, "Ground": 1.0,
        "Rock": 1.0, "Bug": 1.0, "Ghost": 2.0, "Steel": 1.0, "Fire": 1.0, "Water": 1.0,
        "Grass": 1.0, "Electric": 1.0, "Psychic": 2.0, "Ice": 1.0, "Dragon": 1.0,
        "Dark": 0.5, "Fairy": 0.5,
    },
    "Fairy": {
        "Normal": 1.0, "Fighting": 2.0, "Flying": 1.0, "Poison": 0.5, "Ground": 1.0,
        "Rock": 1.0, "Bug": 1.0, "Ghost": 1.0, "Steel": 0.5, "Fire": 0.5, "Water": 1.0,
        "Grass": 1.0, "Electric": 1.0, "Psychic": 1.0, "Ice": 1.0, "Dragon": 2.0,
        "Dark": 2.0, "Fairy": 1.0,
    },
}


if __name__ == "__main__":
    # Quick sanity checks against the examples given in the Bulbapedia article
    assert TYPE_CHART["Fire"]["Grass"] == 2.0
    assert TYPE_CHART["Water"]["Fire"] == 2.0
    assert TYPE_CHART["Electric"]["Ground"] == 0.0
    assert TYPE_CHART["Ground"]["Flying"] == 0.0
    assert TYPE_CHART["Fighting"]["Ghost"] == 0.0
    assert TYPE_CHART["Normal"]["Ghost"] == 0.0
    assert TYPE_CHART["Dragon"]["Fairy"] == 0.0
    assert TYPE_CHART["Psychic"]["Dark"] == 0.0

    # Every attacking type should have an entry for every defending type, and vice versa
    types = list(TYPE_CHART.keys())
    for atk in types:
        assert set(TYPE_CHART[atk].keys()) == set(types), f"Mismatch for {atk}"

    print("All checks passed.")
    print(f"Number of types: {len(types)}")
    print("Example - TYPE_CHART['Normal']:")
    print(TYPE_CHART["Normal"])
