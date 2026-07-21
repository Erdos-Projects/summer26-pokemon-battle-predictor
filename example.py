from damage_calc import Pokemon, Move, Field, Side, StatsTable, BoostsTable, calculate

def main():
    print("--- Smogon Calc Python Engine Test (Gen 9) ---\n")

    # 1. Instantiate Attacker (Flutter Mane with Choice Specs & Tera Fairy)
    flutter_mane = Pokemon(
        gen=9,
        name="Flutter Mane",
        level=100,
        item="Choice Specs",
        nature="Timid",
        is_terastallized=True,
        tera_type="Fairy",
        evs=StatsTable(hp=0, atk=0, def_=4, spa=252, spd=0, spe=252),
        ivs=StatsTable(hp=31, atk=0, def_=31, spa=31, spd=31, spe=31)
    )

    # 2. Instantiate Defender (Ting-Lu with Assault Vest)
    ting_lu = Pokemon(
        gen=9,
        name="Ting-Lu",
        level=100,
        item="Assault Vest",
        nature="Careful",
        evs=StatsTable(hp=252, atk=4, def_=0, spa=0, spd=252, spe=0),
        ivs=StatsTable(hp=31, atk=31, def_=31, spa=31, spd=31, spe=31)
    )

    # 3. Instantiate Move (Moonblast)
    moonblast = Move(gen=9, name="Moonblast")

    # 4. Instantiate Field Conditions (Sandstorm active)
    battle_field = Field(
        battle_format="Singles",
        weather="Sandstorm"
    )

    # 5. Run Calculation
    result = calculate(
        gen=9,
        attacker=flutter_mane,
        defender=ting_lu,
        move=moonblast,
        field=battle_field
    )

    # 6. Display Results
    print(f"Attacker: {flutter_mane.name} (Tera: {flutter_mane.tera_type}, Item: {flutter_mane.item})")
    print(f"Defender: {ting_lu.name} (HP: {ting_lu.max_hp}, Item: {ting_lu.item})")
    print(f"Move: {moonblast.name} (BP: {result.move.base_power})")
    print(f"Environment: Weather = {battle_field.weather}")
    print("-" * 50)
    print(f"Damage Range: {result.get_min_damage()} - {result.get_max_damage()}")
    print(f"Percentage Output: {result.get_percentage_range()}")
    print(f"All 16 Damage Rolls: {result.damage}")

if __name__ == "__main__":
    main()