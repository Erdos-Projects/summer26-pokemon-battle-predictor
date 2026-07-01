#!/usr/bin/env python3

# Summary: 
# Automate scraping pages of battles from PS, getting their respective replays, 
# and saving them to disk. The 'main' function is toward the end.


import json, os, time
import logging, requests
from dataclasses import dataclass, asdict
from pathlib import Path
import typing
from urllib.parse import urlencode, urljoin


import re # for regex things

# Useful 'constants'
SEARCH_BASE_URL = "https://replay.pokemonshowdown.com/api/replays/search"
REPLAY_BASE_URL = "https://replay.pokemonshowdown.com/"
USER_BASE_URL = "https://pokemonshowdown.com/users/"

REPLAY_DIR = Path('../data/replays/')

# Only needed if you want messages to appear when an error, etc. occurs
logger = logging.getLogger()
logger.setLevel(logging.ERROR)



# Roughly, we 
#    1. Pull pages full of Battles;
#    2. Get `battle_id`s from each Battle;
#    3. Pull and write the Replay using the `battle_id`.
# 
@dataclass
class Replay:
    id: str
    format: str
    players: list[str]
    log: str
    inputlog: str
    uploadtime: int
    views: int
    formatid: str
    rating: object = None
    private: int = 0
    password: object = None



# ensuring directory exists
# ===============================================
def ensure_dir(name):
    try:
        Path(name).mkdir(exist_ok=True)
    except OSError as e:
        logger.error("failed to create dir %s: %s", name, e)
        raise SystemExit(1)
    


# 'getters'
# ===============================================
def get_page(page_num, fmt=''):
    '''
    Returns a list of dicts, with each dict corresponding to a `json` of a battle.
    The dicts have keys/values like that of the Battle dataclass; `id` is the only crucial one.

    Leaving `fmt=''` searches for battles of any format.
    '''
    
    params = urlencode({"format": fmt, "page": str(page_num)}) 
    url = f"{SEARCH_BASE_URL}?{params}"

    # This deals with an apparent quirk in PS's search: the first-page results are fine, 
    # but subsequent searches seem to want this `Referer` in the GET request.
    headers = {}
    if page_num > 1: 
        headers = {"Referer": f"https://replay.pokemonshowdown.com/?format={fmt}&page={page_num}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error("failed to get page %d: %s", page_num, e)
        return []

    # The API response starts with a leading character ']' before valid JSON,
    # so remove it
    raw = response.content[1:]
    
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("failed to parse page %d: %s", page_num, e)
        return []
    return data


# ===========================
def get_replay(battle_id: str) -> Replay:
    '''
    Returns a Replay object pulled using the unique battle_id.
    
    Much like `get_page` in function .
    '''
    
    url = REPLAY_BASE_URL + f'{battle_id}' + '.json'
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error("failed to get replay: %s", e)
        return None

    try:
        data = response.json()
    except json.JSONDecodeError as e:
        logger.error("failed to parse replay: %s", e)
        return None

    return Replay(
        id=data.get("id", ""),
        format=data.get("format", ""),
        players=data.get("players", []),
        log=data.get("log", ""),
        inputlog=data.get("inputlog", ""),
        uploadtime=data.get("uploadtime", 0),
        views=data.get("views", 0),
        formatid=data.get("formatid", ""),
        rating=data.get("rating"),
        private=data.get("private", 0),
        password=data.get("password"),
    )


# Definition
def scrape_replays(page_num, fmt=""):
    '''
    Search page, get battle Replays, and write to file.
    '''
    
    # main page-scraping
    page = get_page(page_num, fmt)
    
    if page == [] : 
        print(f"Failed to get page {page_num}.")
        return None
    
    for battle in page :
        # main replay-scraping
        replay = get_replay(battle['id'])
        if replay is None:
            logger.error("failed to get replay %s", battle['id'])
            return None
        
        # Writing
        if fmt == "" : 
            out_path = REPLAY_DIR / f"{replay.id}.json"
        else : 
            out_path = REPLAY_DIR / f"gen9-randombattle_3/{replay.id}.json"
        
        try:
            out_path.write_text(json.dumps(replay.__dict__), encoding="utf-8")
        except OSError as e:
            logger.error("failed to save replay %s : %s", battle['id'], e)



# ===============================================
def main():
    # Automation/Running
    FORMAT='gen9-randombattle';

    ensure_dir('../data/replays/')
    ensure_dir('../data/replays/'+FORMAT+'_3')

    PAUSE = 3; # seconds between pages; NOTE: Should be at least 1 to safely avoid connection denial.

    # Note: even trying searching manually, it seems results stop at page 100
    for j in range(5,100): 
        print(f"Now working on page {j}.")
        
        scrape_replays(j, fmt=FORMAT)
        
        print(f"\tDone; taking a {PAUSE} second break.")
        time.sleep(PAUSE)

if __name__ == "__main__":
    main()