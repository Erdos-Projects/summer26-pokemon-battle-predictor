import json, re, copy, time
import requests

import numpy as np

from dataclasses import dataclass, asdict
from urllib.parse import urlencode

#################################################
# Helper classes and functions
#################################################
@dataclass
class Player:
    """
    Player(name, elo0, elo1, seed)

    Dataclass for match players.

    Attributes
    ---------------
    .name: str
    .elo0: int # Elo at match start
    .elo1: int # Elo after match
    .seed: str # random seed for team generation
    """

    name: str
    elo0: int # old
    elo1: int # new
    seed: str # random seed for team generation


# -----------------------------------------------
def team_from_seed(seed: str) -> dict:
    params = urlencode({
        "format": 'gen9randombattle',
        "seed": seed
    })
    url = f"http://localhost:3000?{params}"

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestsException as e:
        print("Could not get team: %s", e)
        return []

    try:
        team = json.loads(response.content.decode())
    except json.JSONDecodeError as e:
        print("failed to parse team: %s", e)
        return []

    return team


#################################################
# Battle
#################################################
class Battle:
    """
    ParseBattle(data_json, verbose=False)

    Class that reads-in a Pokemon Showdown replay JSON file, and does some basic parsing.

    Parameters
    ----------
    data_json: dict
        json file with basic information about the battle.
    verbose: bool
        If True, print what Turn etc. parser is currently working on.


    Attributes (Some)
    ---------------
        .p1, .p2 : <Player> objects
            duplicating self.players[0-1] for easy reference.

        .team1
        .team2
        
        .start_time: game start time (in seconds since the 'Epoch')
        .end_time: (technically the time at the start of the final turn)
        .match_time: equal to .end_time-.start_time

        .winner: int
            0, 1, or 2 for 'tie/unknown', 'p1 win', and 'p2 win', respectively.

        .teams: array `[ <teamDict1>, <teamDict2> ]`
            - Only contains the pokemon appearing 'during' the match (as read by parser)
        .teams_full: `[<teamDict1>, <teamDict2>]`

        Logs
        ---------------------------------------
        .log: the main text log
        .inputlog: extra thing that contains the team seeds etc.

        .head: everything before '|start'
        .battle: everything in range ['|start', '|win|')
        .tail: everything after .battle

        States
        ---------------------------------------
        .TURNS: Array of turn-strings from splitting .battle.
            * .TURNS[i] gives the raw string for Turn `i`
            * Note 'turn0' = fielding leading pokemon
        .STATES: List of BattleStates (incl State0).
    """
    def __init__(self, data: dict, verbose=False):
        
        # -----------------------------
        # Initializing metadata/attributes
        #
        # Showdown replays by default have the fields: 
        #   - format: str   (ex: "[Gen 9] Random Battle")
        #   - formatid: str    (ex: "gen9randombattle")
        #   - id: str   (ex: "gen9randombattle-2631360263")
        #   - inputlog: str (contains player inputs and seeds)
        #   - log: str  (full battle log)
        #   - password: str | null
        #   - players: list[str]    (ex: ["alice123", "bob32"])
        #   - private: int
        #   - rating: int
        #       - 0 if unrated, lowest Elo in match if rated ("for search purposes").
        #   - uploadtime: int   (ex: 1781376422)
        #   - views: int

        for key in data.keys():
            self.__setattr__(key, data.get(key))

        if self.rating is None :
            self.rating = 0
        self.is_rated = (self.rating > 0)

        # -----------------------------
        # get players and seeds
        try:
            self.p1, self.p2 = self.get_players()
            self.players = [self.p1, self.p2] # for compatibility with Showdown's original fields.
        except:
            print(f"error in parsing `players` of battle {self.id}")

        # -----------------------------
        self.winner = 0 # tie/unknown = 0, p1 wins = 1, p2 wins = 2
        self.turns = 0 # count of turns

        self.teams = self.get_teams()
        self.team1 = self.teams[0] # for easy reference
        self.team2 = self.teams[1] # for easy reference

        # Used for updating team lists as battle progresses
        self.team_species = [ [self.teams[i][j]['species'] for j in range(6)] for i in range(2) ]
        self.team_species_ids = [ [self.teams[i][j]['speciesId'] for j in range(6)] for i in range(2) ]


        # records the number of turns in which a Pokémon was fielded;
        # incremented as battle progresses.
        for i in range(2):
            for j in range(6):
                self.teams[i][j]['turns_seen'] = 0 # count of turns
                self.teams[i][j]['first_turn_seen'] = None # first turn pokemon appears

        # -----------------------------

        # log setup
        self.log = re.sub(r'\n\|\n', '\n', self.log) # delete any lines that are only `|`

        # `head` takes 'START'->'|start', `tail` takes '|win|'->'END', and `bat` is what's in-between.
        self.head, self.battle, self.tail = self.head_sep()

        # -----------------------------
        # processing `head`
        self.gametype = self.get_gametype()
        self.has_custom_rules = (re.search(r'custom rule', self.head) != None)

        self.start_time = self.get_time()  # will be time of first turn
        self.end_time = 0  # will be time of last turn
        self.match_time = 0  # end_time - start_time

        # -----------------------------
        # processing `battle`
        self.pre_battle_corrections()

        self.turn_strs = re.split(r'\|turn\|', self.battle)[1:] # discard initial ''
        self.num_turns = len(self.turn_strs)
        self.turns = self.num_turns # for possible compatibility for later.
        self.turn_times = [] # [(turn#, turn_time)]

        self.parse_battle()
        # -----------------------------
        # processing `tail`
        self.parse_tail()
        self.post_battle()


    # =================================
    # END __init__()


    # =================================
    # function kept separate due to long length.
    def __repr__(self):
        return battle__repr__(self)

    # These are run only in __init__
    # =================================
    def head_sep(self): # separate log into 'header' and 'battle'
        head_end = self.log.index('|start\n')
        battle_end = self.log.index('\n|win|') + 1 # in case string `|win|` appears elsewhere
        return self.log[:head_end], self.log[head_end:battle_end], self.log[battle_end:]

    def get_time(self) -> int:
        secs = re.search(r'\|t:\|(\d+)$', self.head, re.M).group(1)
        return int(secs)

    def get_gametype(self) -> str:
        return re.search(r'\|gametype\|(\w*)$', self.head, re.M).group(1)

    # finds self.player index for player matching `name`
    def get_player_idx(self, name: str) -> int:
        if self.players[0].name == name :
            return 0
        elif self.players[1].name == name :
            return 1
        else :
            print(f"Player {name} not found.")
            return None

    def get_players(self) -> Player :
        # re.match objects for p1 and p2
        m1 = re.search(r'\>player p1 ({.*?})$', self.inputlog, re.M)
        p1_json = json.loads(m1.group(1))

        m2 = re.search(r'\>player p2 ({.*?})$', self.inputlog, re.M)
        p2_json = json.loads(m2.group(1))

        player1 = Player(
            name = p1_json.get("name"),
            elo0 = p1_json.get("rating"),
            elo1 = p1_json.get("rating"), # = elo0 for now
            seed = p1_json.get("seed")
        )
        player2 = Player(
            name = p2_json.get("name"),
            elo0 = p2_json.get("rating"),
            elo1 = p2_json.get("rating"),  # = elo0 for now
            seed = p2_json.get("seed")
        )

        return player1, player2

    # compute full teams from player seeds
    def get_teams(self) -> list:
        team1 = team_from_seed(self.players[0].seed)
        team2 = team_from_seed(self.players[1].seed)
        return [team1, team2]

    # simple wrapper of `parse_turn`
    def parse_battle(self):
        for turn in self.turn_strs :
            self.parse_turn(turn)

    def parse_turn(self, turn_str: str):
        turn_num = int(re.match(r'(\d+)\n', turn_str).group(1))

        turn_time = 0
        match = re.search(r'\|t:\|(\d+)\n', turn_str)
        if match != None:
            turn_time = int(match.group(1))

        self.turn_times.append((turn_num, turn_time))

        for line in turn_str.split('\n')[1:-1]:
            try:
                if line.startswith('|switch|'): self.parse_switch(line)
                elif line.startswith('|drag|'): self.parse_drag(line)
            except:
                print("Could not parse turn %d, line: %s (id:%s)" % (turn_num, line, self.id))
                continue

    # =================================
    def parse_tail(self):
        match = re.match(r'\|win\|(.*)?\n', self.tail)

        try:
            win_name = match.group(1)
        except AttributeError as e:
            print("Error parsing |win| line.")
            return None

        if win_name == self.p1.name :
            self.winner = 1
        elif win_name == self.p2.name :
            self.winner = 2
        else :
            self.winner = 0

        # parse Elo changes by finding deltas +/-, then applying
        if self.rating > 0 :
            loss_line = re.search(r'\|raw\|(?:.*?)\([-+](?P<EloLoss>\d+) for losing\)\n', self.tail)
            win_line = re.search(r'\|raw\|(?:.*?)\([-+](?P<EloGain>\d+) for winning\)\n', self.tail)

            try:
                elo_loss = int(loss_line.group('EloLoss'))
                elo_gain = int(win_line.group('EloGain'))

                if self.winner == 1 :
                    self.p1.elo1 += elo_gain
                    self.p2.elo1 -= elo_loss
                elif self.winner == 2 :
                    self.p1.elo1 -= elo_loss
                    self.p2.elo1 += elo_gain

            except AttributeError as e:
                print("Error parsing Elo changes "+f"(id:{self.id})")

        return None

    # misc fixes and edge cases
    def pre_battle_corrections(self):
        if ("zamazentacrowned" in self.team_species_ids[0]) :
            idx = self.get_mon_idx(self, 1, 'Zamazenta')
            self.teams[0][idx]['species'] = 'Zamazenta-Crowned'
        if ("zamazentacrowned" in self.team_species_ids[1]) :
            idx = self.get_mon_idx(self, 2, 'Zamazenta')
            self.teams[1][idx]['species'] = 'Zamazenta-Crowned'

        self.battle = re.sub(r'\|start\n', '|turn|0\n', self.battle)

        return None

    # misc fixes and edge cases, plus computing total match time, etc.
    def post_battle(self):
        self.turn_times[0] = (0, self.start_time) # turn 0 doesn't list a time

        if self.turn_times[-1][1] != 0 :
            end_time = self.turn_times[-1][1]
        else :
            end_time = self.turn_times[-2][1] # banking that this won't also be 0

        self.end_time = end_time
        self.match_time = self.end_time - self.start_time

        return None

    # =================================
    # Line Parsers
    # =================================
    # These accept only single lines
    def parse_switch(self, line: str):
        # test string: '|switch|p1a: Delphox|Delphox, L84, F|263/263'
        match = re.match(
            r"\|switch\|p(?P<side>\d)a?: (?P<base>[\w'\- ]+)\|(?P<species>[\w'\- ]+), (?P<lvl>L\d+)?(?:.*?)\|(?P<hp>\d+)/(?P<hpmax>\d+)(?:.*?)$",
            line, re.M)
        D = match.groupdict()  # dictionary of captured 'groups'; for brevity

        side = int(D.get('side'))
        base = D.get('base', '')
        species = D.get('species', '')
        hp = int(D.get('hp', 0))
        hpmax = int(D.get('hpmax', 0))

        # level 100 pokemon do not have a listed `level` in the log
        lvl = int(D['lvl'][1:]) if D.get('lvl') is not None else 100

        try:
            idx = self.get_mon_idx(self, side, species)
        except:
            if species == 'Zamazenta-Crowned':
                idx = self.get_mon_idx(self, side, 'Zamazenta')
        self.teams[side - 1][idx]['turns_seen'] += 1

        return None

    # =================================
    def parse_drag(self, line: str):
        # test string: '|drag|p1a: Delphox|Delphox, L84, F|263/263'
        match = re.match(
            r"\|drag\|p(?P<side>\d)a?: (?P<base>[\w\- ]+)\|(?P<species>[\w'\- ]+), (?P<lvl>L\d+)?(?:.*?)\|(?P<hp>\d+)/(?P<hpmax>\d+)(?:.*?)$",
            line, re.M)
        D = match.groupdict()  # dictionary of captured 'groups'; for brevity

        side = int(D.get('side'))
        base = D.get('base', '')
        species = D.get('species', '')
        hp = int(D.get('hp', 0))
        hpmax = int(D.get('hpmax', 0))

        # level 100 pokemon do not have a listed `level` in the log
        lvl = int(D['lvl'][1:]) if D.get('lvl') is not None else 100

        idx = self.get_mon_idx(self, side, species)
        self.teams[side - 1][idx]['turns_seen'] += 1

        return None

    # Misc helper functions
    # =================================
    def get_mon_idx(self, side: int, species: str) -> int:
        return self.team_species[side - 1].index(species)

# ===============================================
# add the BVs and computed Stats to each Pokemon
def get_stats(DEX: dict, mon: dict):
    '''
    Input poke dict, compute total stats for each Pokemon in it, append to Pokemon, and return team.
    '''
    speciesId = mon['speciesId']

    try:
        poke['bvs'] = copy.deepcopy(DEX[speciesId]['baseStats'])  # deepcopy for safety
        poke['stats'] = compute_stats(poke)  # [[3]]
        poke['types'] = copy.deepcopy(DEX[speciesId].get('types'))
    except:
        print("error with pokemon %s (%s)" % (species, battle_id))

    return None

def stat_formula(poke: dict):
    '''
    `poke` should have dictionaries `BV`, `EV`, `IV`, and entry `level`
    example output: {'hp': 263, 'atk': 120, 'def': 169, 'spa': 240, 'spd': 216, 'spe': 223}
    '''
    _stat_D = {}

    BV = poke['bvs']
    EV = poke['evs']
    IV = poke['ivs']
    lvl = poke['level']

    for k in BV.keys():
        Q_k = (2 * BV[k] + IV[k] + np.floor(EV[k] / 4)) * (lvl / 100)
        nat_k = 1.0  # in case we want to incorporate `nature`s later

        if k == 'hp':
            _stat_D[k] = int(np.floor(Q_k) + lvl + 10)
        else:
            _stat_D[k] = int(np.floor((Q_k + 5) * nat_k))

    return _stat_D








# function kept separate due to long length
def battle__repr__(bat: Battle):
    repr = f"%%%%%%%%%%   Battle {bat.id}   %%%%%%%%%%\n";
    repr += f"============================================================\n";
    repr += f"This was a battle between:\n"
    if bat.is_rated:
        repr += f"\t{bat.p1.name} \t(Elo: {bat.p1.elo0})\n"
        repr += f"\t{bat.p2.name} \t(Elo: {bat.p2.elo0}).\n\n"
    else:
        repr += f"\t{bat.p1.name}\n"
        repr += f"\t{bat.p2.name}.\n\n"

    repr += f"The battle lasted {bat.match_time} seconds with {bat.num_turns} turns.\n\n"

    repr += f"{bat.p1.name}'s team was:\n"
    for mon in bat.teams[0]:
        repr += f"\t{mon['species']}  ({mon['turns_seen']} turns seen)\n"
    repr += f"{bat.p2.name}'s team was:\n"
    for mon in bat.teams[1]:
        repr += f"\t{mon['species']}  ({mon['turns_seen']} turns seen)\n"
    repr += '\n'

    if bat.winner == 0 :
        repr += "This was either a tie, or the winner couldn't be determined!"
    else :
        winning_player = bat.players[0] if bat.winner == 1 else bat.players[1]
        losing_player = bat.players[1] if bat.winner == 1 else bat.players[0]
        repr += f"{winning_player.name} won!\n"
    if bat.is_rated:
        repr += f"{winning_player.name}'s rating increased to {winning_player.elo1}.\n"
        repr += f"{losing_player.name}'s rating fell to {losing_player.elo1}.\n"
    else:
        repr += "This was an unrated match, so no one's rating changed.\n"

    repr += f"%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\n"
    return repr


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#                   MAIN
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
def main():
    with open('./test/gen9randombattle-2662389740.json', 'r') as file:
        battle_json = json.load(file)
    BAT = Battle(battle_json)

    print(battle__repr__(BAT))
    for turn in BAT.turn_times :
        print(turn)

    print()
    for mon in BAT.teams[0] :
        print(json.dumps(mon, indent=2))

# ===============================================
if __name__ == "__main__":
    main()
