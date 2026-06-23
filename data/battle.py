'''
Overview of battle.py 
#################################################

(for brevity, anything of the form `.x` means `self.x`)

`Player` class: 
---------------------------------------
    * .name: str
    * .side: int # 1 or 2
    * .elo0: int # Elo at match start
    * .elo1: int # Elo after match

The dataclasses `Team` and `Pokemon` seen below are fairly self-explanatory.
    * The `Pokemon.base` is the "base form" of the pokemon, possibly different from `Pokemon.forme`. 
        (Ex: `base` = `Tauros` and `forme` = `Tauros-Paldea-Aqua`)
    

`Battle` class (quick facts): 
---------------------------------------
    * `.id` (ex: `gen9randombattle-2631360263`)
    * `.format` (ex: `[Gen 9] Random Battle`)
    
    * `.player1`: <Player> 
    * `.player2`: <Player>
    
    * `.start_time`: game start time (in seconds since the 'Epoch')
    * `.end_time`: (technically the time at the start of the final turn)
    
    * `.winner`: <Player>
    * `.loser`: <Player>
    
    * `.lead_pokemon`: array `[ <lead1>, <lead2> ]` 
    * `.teams`: array `[ <teamDict1>, <teamDict2> ]`
        - Only contains the pokemon appearing 'during' the match (as read by parser)
    * `.teams_full`: `[<teamDict1>, <teamDict2>]`
    Logs
    ---------------------------------------
    * `.log`: the main text log
    * `.inputlog`: extra thing that contains the team seeds etc.
    
    * `.head`: everything before '|start'
    * `.bat`: everything in range `['|start', '|win|')`
    * `.tail` everything after `.bat`
    
    States
    ---------------------------------------
    * `.TURNS`: Array of turn-strings from splitting `.bat`. 
        * `.TURNS[i]` gives the raw string for Turn `i`
        * Note 'turn0' = fielding leading pokemon
    * `.STATES`: List of BattleStates (incl State_0).

`BattleState`:
---------------------------------------
    * `.time` : 'absolute' time turn occured at (seconds since *Epoch*)
    * `.turn`
    
    * `.team1`, 
    * `.team2`
    * `.time_elapsed` : seconds passed since `Battle.start_time`
    
    * `.battle_id` : copy of `Battle.id`; useful for printing errors.
    * `.print()` gives a nice printed summary.
'''


import json, copy, time
import re # regex

from copy import deepcopy
from dataclasses import dataclass


#################################################
# Dataclasses (Player, Team, Pokemon)
#################################################

# a `dataclass` is just a Class that only has attributes and no methods
# writing @dataclass lets you skip writing `__init__(...) : self.x = x` a bunch
@dataclass
class Player: 
    name: str
    side: int
    elo0: int # old
    elo1: int # new

class Team:
    def __init__(self, side: int, active: str, D: dict):
        self.side = side
        self.active = active
        self.D = D # team dictionary

    def __repr__(self):
        _out = "{" + f"side: {self.side}, active: {self.active}, D: <dict>" + "}"
        return _out

class Pokemon:
    def __init__(self, base, spec, lvl, hp, hp_max):
        self.base = base
        self.spec = spec
        self.lvl = int(lvl)
        self.hp = int(hp)
        self.hp_max = int(hp_max)

    def __repr__(self):
        _out = "{" + f"spec: {self.spec}, lvl: {self.lvl}, hp/max: {self.hp}/{self.hp_max}" + "}"
        return _out


# -----------------------------
# Extra functions to help with printing teams

def team_str(team: dict):
    _out = ""
    for poke in team.keys():
        _out += f" > {poke}: {str(team[poke])}\n"
    return _out

def team_full_str(team_full: dict):
    _out = ""
    for poke in team_full.keys() :
        poke_entry = team_full[poke]
        dict_to_show = {key : poke_entry[key] for key in ['species', 'level']}
        dict_to_show['hp'] = poke_entry['stats']['hp']
        _out += f" > {poke}: {dict_to_show}\n"
    return _out
        

#################################################
# BattleState
#################################################
class Battle:
    def __init__(self,file_name, verbose=False):
        with open("replays/gen9-randombattle/" + file_name,"r") as battle_json:
            data = json.load(battle_json)
        # -----------------------------
        # Initializing metadata/attributes
        self.id = data['id']
        self.format = data['format']
        self.formatid = data['formatid']
        
        self.rating = data['rating']
        self.rated = (self.rating != None)
        
        # self.time_list = [] # times can be wrapped into different Turn/State classes
        self.start_time = 0
        self.end_time = 0

        self.winner = ""
        self.loser = ""

        self.player_dets = data['player_dets'] # more info about players... may be redudant with self.p1, self.p2
        self.teams_full = data['teams_full'] # full teams including stats

        
        # -----------------------------
        # log setup
        self.inputlog = data.get("inputlog", "")
        self.log = data["log"]
        self.log = re.sub(r'\n\|\n', '\n', self.log) # delete any lines that are only `|`

        # `head` takes 'START'->'|start', `tail` takes '|win|'->'END', and `bat` is what's in-between.
        self.head, self.bat, self.tail = self._head_sep(self.log)

        # -----------------------------
        # processing `head`
        self.gametype = self._init_gametype(self.head)
        self.custom_ruleQ = (re.search(r'custom rules:', self.head) != None)
        
        self.start_time = self._init_time(self.head)
        self.end_time = 0 # changed after parsing STATES
        
        try:
            self.player1, self.player2 = self._init_players(self.head)
        except:
            print(f"error in parsing `players` of battle {self.id}")

        # -----------------------------
        # processing `bat`
        self.bat = re.sub(r'\|start\n', '|turn|0\n', self.bat)
        self.TURNS = re.split(r'\|turn\|', self.bat)[1:] # discard initial ''
        
        # initialize/parse starting state ("turn 0")
        
        # Need to allow for Zoroark weirdness:
        if 'Zoroark' in self.teams_full[0].keys() :
            poke = self.teams_full[0]['Zoroark']
            D0_0 = {poke['name'] : Pokemon(poke['name'], poke['species'], poke['level'], poke['stats']['hp'], poke['stats']['hp'])}
        else : D0_0 = {}
        if 'Zoroark' in self.teams_full[1].keys() :
            poke = self.teams_full[1]['Zoroark']
            D1_0 = {poke['name'] : Pokemon(poke['name'], poke['species'], poke['level'], poke['stats']['hp'], poke['stats']['hp'])}
        else : D1_0 = {}
        
        BS_0 = BattleState(
            Team(side=1, active='', D=D0_0),
            Team(side=2, active='', D=D1_0), 
            self.TURNS[0],
            battle_id = self.id
        )
        BS_0.time = self.start_time # turn 0 time is match start
        
        self.STATES = [BS_0]
        for i in range(len(self.TURNS)-1): # -1 b/c I use `i+1` below
            BS_i = self.STATES[i]
            BS_new = BattleState(
                copy.deepcopy(BS_i.team1), # can't leave out the deepcopy!
                copy.deepcopy(BS_i.team2), # can't leave out the deepcopy!
                self.TURNS[i+1],
                match_start_time = self.start_time,
                battle_id = self.id
            )
            self.STATES.append(BS_new)
            if verbose : 
                BS_new.print()

        # [<starter>]
        self.lead_pokemon = [
            BS_0.team1.active, 
            BS_0.team2.active
        ] 

        # -----------------------------
        # processing `tail`
        self.parse_tail(self.tail)

        self.end_time = self.STATES[-1].time
        
        self.teams = [
            self.clean_team(self.STATES[-1].team1.D), 
            self.clean_team(self.STATES[-1].team2.D)
        ] # [<{team_set}>]

    # =================================
    # END __init__()


    # =================================
    def __repr__(self):
        to_return = f"%%%%%%%%%%   Battle {self.id}   %%%%%%%%%%\n"; 
        to_return += f"============================================================\n";
        
        if self.rated:
            to_return += f"This was a battle between {self.p1.name} (pre-match rating {self.p1.elo0}) "
            to_return += f"and {self.p2.name} (pre-match rating {self.p2.elo0}).\n\n"
        else:
            to_return += f"This was a battle between {self.p1.name} and {self.p2.name}.\n\n"
        
        to_return += f"{self.p1.name}'s lead pokemon was {self.lead_pokemon[0]}, "
        to_return += f"and their team (by `base`) was\n{team_full_str(self.teams_full[0])}\n"
        to_return += f"{self.p2.name}'s lead pokemon was {self.lead_pokemon[1]}, "
        to_return += f"and their team (by `base`) was\n{team_full_str(self.teams_full[1])}\n"
        
        to_return += f"{self.winner.name} won!\n"
        if self.rated:
            to_return += f"{self.winner.name}'s rating increased to {self.winner.elo1}.\n"
            to_return += f"{self.loser.name}'s rating fell to {self.loser.elo1}.\n"
        else:
            to_return += "This was an unrated match, so no one's rating changed.\n"
        
        to_return += f"%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n\n"
        return to_return

        
    # These are meant to be run only in __init__
    # =================================
    def _head_sep(self, log): # separate log into 'header' and 'battle'
        head_end = log.index('|start\n')
        bat_end = log.index('\n|win|') + 1 # in case string `|win|` appears elsewhere
        return log[:head_end], log[head_end:bat_end], log[bat_end:]

    def _init_time(self, head):
        secs = re.search(r'\|t:\|(\d+)$', head, re.M).group(1)
        return int(secs) # returns a `time.tm` object
    
    def _init_gametype(self, head):
        return re.search(r'\|gametype\|(\w*)$', head, re.M).group(1)
    
    def _init_players(self, head):
        # test: |player|p1|kaisarian|lucas-gen4pt|
        # test: |player|p2|Flamesenpai557|101|
        player_pat = re.compile(r'\|player\|p(?P<side>\d)\|(?P<name>.*)\|(.*)\|(?P<elo>\d+)?\n'); # player line pattern

        p1 = player_pat.search(head)
        search_ind = p1.end() # advance the search beginning
        p2 = player_pat.search(head, pos=search_ind)

        # if battle unrated then elo is 'None'; we set to 0
        if p1.group('elo') == None : p1_elo = 0
        else : p1_elo = p1.group('elo') 
        
        if p2.group('elo') == None : p2_elo = 0
        else : p2_elo = p2.group('elo')
            
        player1 = Player(
            name = p1.group('name'), 
            side = int(p1.group('side')),
            elo0 = int(p1_elo),
            elo1 = int(p1_elo), # set equal for now
        )
        player2 = Player(
            name = p2.group('name'), 
            side = int(p2.group('side')),
            elo0 = int(p2_elo),
            elo1 = int(p2_elo), # set equal for now
        )
        
        return player1, player2

        
    # =================================
    def parse_tail(self, tail):
        match = re.match(r'\|win\|(.*)?\n', tail)

        try:
            win_name = match.group(1)
        except AttributeError as e:
            print("Error parsing |win| line.")
            return None
        
        if win_name == self.p1.name : 
            self.winner = self.p1
        else: 
            self.winner = self.p2

        if self.winner.side == 1 : 
            self.loser = self.p2
        else:
            self.loser = self.p1

        # parse Elo changes by finding deltas +/-, then applying
        if self.rated : 
            match_lose = re.search(r'\|raw\|(?:.*?)\([-+](?P<EloLoss>\d+) for losing\)\n', tail)
            match_win = re.search(r'\|raw\|(?:.*?)\([-\+](?P<EloGain>\d+) for winning\)\n', tail)
    
            try:
                elo_loss = int(match_lose.group('EloLoss'))
                self.loser.elo1 -= elo_loss # detract points
            except AttributeError as e:
                print("Error parsing Elo for loser "+f"(id:{self.id})")
            try: 
                elo_gain = int(match_win.group('EloGain'))
                self.winner.elo1 += elo_gain
            except AttributeError as e:
                print("Error parsing Elo for winner "+f"(id:{self.id})")

        return None

    
    # =================================
    # in essence this just resets all team HP's to max for printing purposes
    def clean_team(self, teamD: dict):
        if teamD == {} : 
            print("Need to pass a nonempty Team object.")
            return None
            
        _team = copy.deepcopy(teamD)
        for form in _team.keys():
            _team[form].hp = _team[form].hp_max
        return _team
        


#################################################
# BattleState class
#################################################

class BattleState:
    # feed current teams and turn string, plus optional battle start_time and id (for debugging)
    def __init__(self, team1, team2, turn: str, match_start_time = 0, battle_id = ''): 
        self.turn = int(re.match(r'(\d+)\n', turn).group(1)) # split turn-strings start with `#\n`
        
        # update self.time if a timestamp appears in `turn`
        self.time = 0
        t_match = re.search(r'\|t:\|(\d+)\n', turn)
        if t_match != None :
            self.time = int(t_match.group(1))
        
        self.team1 = team1 
        self.team2 = team2 
        
        self.elapsed_time = self.time - match_start_time
        self.battle_id = battle_id
        
        self.parse_turn(turn) # main builder

    # =================================
    def __repr__(self):
        return f"<BattleState;turn{self.turn}>"

    # =================================
    # Separating this from __repr__ makes looking at arrays of BattleStates easier
    def print(self):
        _out = ""
        _out += f"State at END of Turn {self.turn}: \n"
        _out += f"  Match time: {time.strftime("%M:%S",time.gmtime(self.elapsed_time))} (mm:ss)\n"
        _out += f"  Team: {self.team1}\n"
        _out += f"  Team: {self.team2}\n"
        print(_out)

    
    # =================================
    # Line Parsers 
    # =================================
    # These accept only single lines
    
    def parse_switch(self, s: str):
        # test string: '|switch|p1a: Delphox|Delphox, L84, F|263/263'
        match = re.match(r"\|switch\|p(?P<plr>\d)a?: (?P<base>[\w'\- ]+)\|(?P<forme>[\w'\- ]+), (?P<lvl>L\d+)?(?:.*?)\|(?P<hp>\d+)/(?P<hpmax>\d+)(?:.*?)$", s, re.M)
        D = match.groupdict() # dictionary of captured 'groups'; for brevity
        
        player = int(D['plr'])
        base = D['base']
        forme = D['forme']
        hp = int(D['hp'])
        hpmax = int(D['hpmax'])

        # level 100 pokemon do not have a listed `level` in the log
        if D['lvl'] == None : lvl = 100
        else : lvl = int(D['lvl'][1:])

        if player == 1:
            poke = Pokemon(base, forme, lvl, hp, hpmax)
            self.team1.D[base] = poke
            self.team1.active = forme
        else: 
            poke = Pokemon(base, forme, lvl, hp, hpmax)
            self.team2.D[base] = poke
            self.team2.active = forme
        return None

    # =================================
    def parse_drag(self, s: str):
        # test string: '|drag|p1a: Delphox|Delphox, L84, F|263/263'
        match = re.match(r"\|drag\|p(?P<plr>\d)a?: (?P<base>[\w\- ]+)\|(?P<forme>[\w'\- ]+), (?P<lvl>L\d+)?(?:.*?)\|(?P<hp>\d+)/(?P<hpmax>\d+)(?:.*?)$", s, re.M)
        D = match.groupdict() # dictionary of captured 'groups'; for brevity
        
        player = int(D['plr'])
        base = D['base']
        forme = D['forme']
        hp = int(D['hp'])
        hpmax = int(D['hpmax'])

        # level 100 pokemon do not have a listed `level` in the log
        if D['lvl'] == None : lvl = 100
        else : lvl = int(D['lvl'][1:]) # [1:] to map 'L##' |-> '##'
        
        if player == 1:
            poke = Pokemon(base, forme, lvl, hp, hpmax)
            self.team1.D[base] = poke
            self.team1.active = forme
        else: 
            poke = Pokemon(base, forme, lvl, hp, hpmax)
            self.team2.D[base] = poke
            self.team2.active = forme
        return None
    
    # =================================
    def parse_damage(self, s: str):
        # test strings
        # S1 = '|-damage|p2a: Snorlax|291/397|[from] item: Rocky Helmet|[of] p1a: Skarmory'
        # S2 = '|-damage|p1a: Wugtrio|0 fnt'
            
        # most damage lines look like this
        match = re.match(r"\|-damage\|p(?P<plr>\d)a?: (?P<base>[\w'\- ]+)\|(?P<hp>\d+)/(?P<hpmax>\d+).*$", s, re.M)
        if match == None :
            # could be a 'fainting line'
            match = re.match(r"\|-damage\|p(?P<plr>\d)a?: (?P<base>[\w'\- ]+)\|(?P<hp>\d+) fnt(?:.*?)$", s, re.M)
    
        # if neither work, stop
        if match == None : 
            print("Could not parse line:\n%s" % s)
            return None
            
        D = match.groupdict() # for brevity
        
        player = int(D['plr'])
        base = D['base']
        hp = int(D['hp'])
        
        if player == 1 : 
            poke = self.team1.D[base]
            poke.hp = hp
            if D.get('hpmax') != None : poke.hp_max = int(D['hpmax'])
        else:
            poke = self.team2.D[base]
            poke.hp = hp
            if D.get('hpmax') != None : poke.hp_max = int(D['hpmax'])
        return None

    # =================================
    def parse_heal(self, s: str):
        # test strings
        # S1 = '|-heal|p1a: Skarmory|169/235'
        # S2 = '|-heal|p2a: Wigglytuff|423/424|[from] item: Leftovers'
        
        match = re.match(r"\|-heal\|p(?P<plr>\d)a?:\s(?P<base>[\w'\- ]+)\|(?P<hp>\d+)/(?P<hpmax>\d+).*$", s, re.M)
        D = match.groupdict() # for brevity
        
        player = int(D['plr'])
        base = D['base']
        hp = D['hp']
        
        if player == 1 : 
            poke = self.team1.D[base]
            poke.hp = hp
            if D.get('hpmax') != None : poke.hp_max = int(D['hpmax'])
        else:
            poke = self.team2.D[base]
            poke.hp = hp
            if D.get('hpmax') != None : poke.hp_max = int(D['hpmax'])
        return None

    # =================================
    # Main Parser
    # =================================
    def parse_turn(self, turn: str):
        for line in turn.split('\n'): 
            try:
                if line.startswith('|switch|') : self.parse_switch(line)
                elif line.startswith('|drag|') : self.parse_drag(line)
                elif line.startswith('|-damage|') : self.parse_damage(line)
                elif line.startswith('|-heal|') : self.parse_heal(line)
            except:
                print("Could not parse turn %d, line: %s (id:%s)" % (self.turn, line, self.battle_id))
                continue