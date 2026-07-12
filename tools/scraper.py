#!/usr/bin/env python3
'''
Automate scraping pages of battles from PS, getting their respective replays, 
and saving them to disk. The 'main' function is toward the end.

Roughly, we 
    1. Pull pages full of Battles;
    2. Get `battle_id`s from each Battle;
    3. Pull and write the Replay using the `battle_id`.
'''

import json, time
import typing
import logging, requests

from pathlib import Path
from dataclasses import dataclass
from urllib.parse import urlencode

# Useful 'constants'
SEARCH_BASE_URL = "https://replay.pokemonshowdown.com/api/replays/search"
REPLAY_BASE_URL = "https://replay.pokemonshowdown.com/"
USER_BASE_URL = "https://pokemonshowdown.com/users/"

# Only needed if you want messages to appear when an error, etc. occurs
logger = logging.getLogger()
logger.setLevel(logging.ERROR)

# ensuring directory exists
# ===============================================
def extantDir(path):
    try:
        Path(path).mkdir(exist_ok=True)
    except OSError as e:
        logger.error("failed to create dir %s: %s", path, e)
        raise SystemExit(1)
    return Path(path)

    
# ===============================================
# for parsing CLI args
import argparse

parser = argparse.ArgumentParser(
    description="Scrapes battle JSONs from pokemonshowdown.com."
)

# positional
parser.add_argument(
    "outDir",
    type=extantDir,
    help="Dir for replays"
)  

# flags
parser.add_argument(
    "-q", "--quiet", 
    action="store_true",    # boolean flag
    help="Do not print page progress; default=`False`"
)

parser.add_argument(
    "--fmt",
    type=str,
    default="gen9-randombattle", 
    help="Battle format; default=`gen9-randombattle`"
)

parser.add_argument(
    "--start", 
    type=int,
    default=3,
    help="Starting page number; default=3, capped at 100"
)

parser.add_argument(
    "--end", 
    type=int,
    default=100,
    help="Ending page number; default=100, and capped at 100"
) 

parser.add_argument(
    "--pause", 
    type=float,
    default=2,
    help="Seconds to 'sleep' between each page; default=2; NOTE: recommend >= .50 to avoid response denial"
)   


# ===============================================
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



# ===============================================
# Core functions
# ===============================================
def scrape_replays(out_dir, page_num, fmt=""):
    '''
    Search page, get battle Replays, and write to file.
    '''
    
    page = get_page(page_num, fmt) # [[1]]
    
    if page == [] : 
        print(f"Failed to get page {page_num}.")
        return None
    
    for battle in page :
        replay = get_replay(battle['id']) # [[2]]
        if replay is None:
            logger.error("failed to get replay %s", battle['id'])
            return None
        
        # Writing
        out_file = out_dir / f"{replay.id}.json"
        
        try:
            out_file.write_text(json.dumps(replay.__dict__), encoding="utf-8")
        except OSError as e:
            logger.error("failed to save replay %s : %s", battle['id'], e)

# [[1]]
# ===========================
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

# [[2]]
# ===========================
def get_replay(battle_id: str) -> Replay:
    '''
    Returns a Replay object pulled using the unique battle_id. Much like `get_page` in function .
    '''
    
    url = REPLAY_BASE_URL + f'{battle_id}' + '.json'
    
    try:
        response = requests.get(url, timeout=10)
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



# ===============================================
# MAIN
# ===============================================
def main():
    args = parser.parse_args()

    Q = args.quiet
    FMT = args.fmt
    START = args.start
    END = args.end
    PAUSE = args.pause
    OUT = args.outDir
    
    # some basic checks
    if not ((1 <= START <= 100) and (type(START)==int)) :
        parser.error("START should be in {1,...,100}; use -h for details")
    if not ((1 <= END <= 100) and (type(END)==int)) :
        parser.error("END should be in {1,...,100}; use -h for details")
    if not (START <= END) :
        parser.error("need START <= END")
    if not (PAUSE >= 0.5) :
        parser.error("PAUSE should be >= 0.5 to avoid connection denial")

    # Note: recommend START >= 2 because ongoing battles may occur on page 1; 
    # END capped at 100 b/c no further results provided
    for j in range(START,END+1): 
        if not Q : print(f"Now working on page {j}.")
        scrape_replays(OUT, j, fmt=FMT)
        if (j<END) : 
            if not Q : print(f"    Done; taking a {PAUSE} second break.")
            time.sleep(PAUSE)
        elif (j==END) : 
            print("All done.")

# ===============================================
if __name__ == "__main__":
    main()