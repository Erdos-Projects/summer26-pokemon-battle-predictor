from multiprocessing import Pool
import sys
from pathlib import Path
import json
from itertools import product
import time

repo = Path.cwd().resolve()
sys.path.append(str(repo / "damage-calc-python-wrapper"))
sys.path.append(str(repo / "damage-calc-python-wrapper" / "python_calc"))

from python_calc import Pokemon,advantage

id = "2631360263"
with open("data/replays/gen9-randombattle/gen9randombattle-" + id + ".json") as battle_json:
    data = json.load(battle_json)

team1 = [
    Pokemon(
        name=data["teams_full"][0][mon_name]["speciesId"],
        gen=9,
        level=data["teams_full"][0][mon_name]["level"],
        ability = data["teams_full"][0][mon_name]["ability"],
        item = data["teams_full"][0][mon_name]["item"],
        gender = data["teams_full"][0][mon_name]["gender"],
        ivs = data["teams_full"][0][mon_name]["ivs"],
        evs = data["teams_full"][0][mon_name]["evs"],
        teraType = data["teams_full"][0][mon_name]["teraType"],
        moves = data["teams_full"][0][mon_name]["moves"]
    )
    for mon_name in data["teams_full"][0].keys()
]

team2 = [
    Pokemon(
        name=data["teams_full"][1][mon_name]["speciesId"],
        gen=9,
        level=data["teams_full"][1][mon_name]["level"],
        ability = data["teams_full"][1][mon_name]["ability"],
        item = data["teams_full"][1][mon_name]["item"],
        gender = data["teams_full"][1][mon_name]["gender"],
        ivs = data["teams_full"][1][mon_name]["ivs"],
        evs = data["teams_full"][1][mon_name]["evs"],
        # teraType = data["teams_full"][1][mon_name]["teraType"], # calculate will assume that the teraType is on
        moves = data["teams_full"][1][mon_name]["moves"]
    )
    for mon_name in data["teams_full"][1].keys()
]

def adv_helper(args):
    return advantage(*args)

min_time = 100

for num_processes in range(1,13):

    start = time.time()

    if __name__ == '__main__':
        with Pool(num_processes) as p:
            result = p.map_async(adv_helper,product(team1,team2))
            print(f"Player 1 total advantage:{sum(result.get())}")
            print(f"Total time taken with {num_processes} processes: {time.time() - start} seconds")
            print()