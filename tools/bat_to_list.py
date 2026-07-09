from full_pokemon import FullPokemon

# ===============================================
# Primary DataFrame-entry maker
# ===============================================
def battle_to_list(bat) : 
    '''
    battle_to_list(bat: Battle)

    Returns a long list with data about battle `bat`, players, and individual Pokemon therein.
    The list entries correspond to the column names from `data_col_names.txt`
    '''
    # `format`, `id#`
    data = [ 
        bat.formatid, 
        int(bat.id.removeprefix(bat.formatid+'-'))
    ]
    
    # `p1_win` {0,1}
    if bat.winner.name == bat.p1.name : 
        data.append(1)
    else : 
        data.append(0)
    
    # `rated`, `n_turns`, `start_time`, `end_time`, `duration`
    data.extend([bat.rated, len(bat.STATES), bat.start_time, bat.end_time, bat.end_time - bat.start_time])
    
    # `p#name`, `p#side`, `p#elo0`, `p#elo1`
    data.extend(vars(bat.p1).values())
    data.extend(vars(bat.p2).values())

    # `type_diversity_diff`, `num_boosting_abilities_diff`, ..., `p1_total_adv` #21
    data.extend(_aux_battle_data(bat)) # [[2]]

    # `p#_revealed_team_size`
    data.append(len(bat.teams[0].keys()))
    data.append(len(bat.teams[1].keys()))
    
    # getting mon info lists (see below for list of entries)
    # -----------------------
    for i in range(2) :
        team=bat.teams_full[i]
        for M in team.keys() :
            usedQ = int(M in bat.teams[i].keys())
            data.extend(mon_info_list(team[M], usedQ)) # [[1]]
    
    return data


# [[1]]
# ===========================
def mon_info_list(Mon, usedQ):
    '''
    Returns list with entries: 
        'name','speciesId','used',
        'gender','shinyQ','level',
        'ability','item','teraType','role',
        'mv1','mv2','mv3','mv4',
        'type1','type2',
        'hp','atk','def',
        'spa','spd','spe'
    '''
    _L = [Mon['name'], Mon['speciesId'], usedQ]
    
    _keys = [
        'gender','shiny','level','ability',
        'item','teraType','role'
        ]
    _L.extend([ Mon[key] for key in _keys ])

    # movelist
    _moves = Mon['moves']
    _moves.extend([""]*(4-len(_moves))) # pad with "" to get length 4
    _L.extend(_moves)

    # typelist
    _types = Mon['types']
    _types.extend([""]*(2-len(_types))) # pad with "" to get length 2
    _L.extend(_types)
    
    # did this manually b/c it seemed sometimes `off` would be omitted.
    _L.extend([
        Mon['stats']['hp'],
        Mon['stats']['atk'],
        Mon['stats']['def'],
        Mon['stats']['spa'],
        Mon['stats']['spd'],
        Mon['stats']['spe']
    ])
    if Mon['stats'].get('off') != None :
        _L.append(Mon['stats']['off'])
    else:
        _L.append(max(Mon['stats']['atk'], Mon['stats']['spa']))
    
    return _L


# [[2]]
# ===========================
def _aux_battle_data(battle):
    useful_traits = ["num_move_boosters_diff","num_boosting_abilities_diff"]
    stat_names = ['hp','atk','def','spa','spd','spe']
    red_stat_names = ['hp','off','def','spd','spe'] # reduced stat names where off stands in for max(atk,spa)

    _L = []
    
    # Team construction
    team1 = [FullPokemon(battle.teams_full[0][mon]) for mon in battle.teams_full[0].keys()]
    team2 = [FullPokemon(battle.teams_full[1][mon]) for mon in battle.teams_full[1].keys()]
    teams = [team1,team2]
    
    # `type_diversity_diff`
    p1_types = set(mon.types[i] for mon in team1 for i in range(len(mon.types)))
    p2_types = set(mon.types[i] for mon in team2 for i in range(len(mon.types)))
    _L.append(len(p1_types) - len(p2_types))
    
    # `num_boosting_abilities_diff`
    p1_num_boosting_abilities = sum(int(mon.has_boosting_ability()) for mon in team1)
    p2_num_boosting_abilities = sum(int(mon.has_boosting_ability()) for mon in team2)
    _L.append(p1_num_boosting_abilities - p2_num_boosting_abilities)

    # `num_move_boosters_diff`
    p1_num_move_boosters = sum(int(mon.has_boost_move()) for mon in team1)
    p2_num_move_boosters = sum(int(mon.has_boost_move()) for mon in team2)
    _L.append(p1_num_move_boosters - p2_num_move_boosters)
    
    # `total_stat_diff`
    p1_total_stats = sum(sum(mon.stats[stat] for stat in red_stat_names) for mon in team1)
    p2_total_stats = sum(sum(mon.stats[stat] for stat in red_stat_names) for mon in team2)
    _L.append(p1_total_stats - p2_total_stats)
    
    # `p1_total_adv`
    _L.append(sum(FullPokemon.advantage(team1[m1],team2[m2]) for m1 in range(6) for m2 in range(6)))

    return _L