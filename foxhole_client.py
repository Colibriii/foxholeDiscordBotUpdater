import re
import requests
import json
import os
import time
import math

# config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "war_state.json")
SHARD_URL = "https://war-service-live.foxholeservices.com/api" # Able SHARD
SHARD_URL3 = "https://war-service-live-3.foxholeservices.com/api" # Charlie SHARD
HEADERS = { "User-Agent": "FoxholeWarBot/2.2 From .colibri" }

IMPORTANT_STRUCTURES = [56, 57, 58, 45, 27] 

CACHE_FILE = "static_data_cache.json"
_STATIC_DATA_MEMORY = {}
    
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            _STATIC_DATA_MEMORY = json.load(f)
        print(f"Static Data : {_STATIC_DATA_MEMORY.__len__()} loaded.")
    except Exception as e:
        print(f"Critical error, impossible to read {CACHE_FILE} : {e}")
        _STATIC_DATA_MEMORY = {}
else:
    print(f"impossible to fin file ! {CACHE_FILE}")
    print("   -> City names unavailable. May cause problems.")
    _STATIC_DATA_MEMORY = {}

FLAG_VICTORY_BASE = 0x01
FLAG_IS_SCORCHED  = 0x10

def load_local_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_local_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except:
        pass

def get_map_names():
    try:
        resp = requests.get(f"{SHARD_URL}/worldconquest/maps", headers=HEADERS)
        return resp.json() if resp.status_code == 200 else []
    except:
        return []

def get_map_data(map_name):
    """get death and cities data"""
    data = {"casualties": {}, "structures": {}}
    
    # 1. War Report
    try:
        resp = requests.get(f"{SHARD_URL}/worldconquest/warReport/{map_name}", headers=HEADERS, timeout=2)
        if resp.status_code == 200:
            r = resp.json()
            data["casualties"] = {
                "warden": r.get("wardenCasualties", 0),
                "colonial": r.get("colonialCasualties", 0)
            }
    except:
        pass 

    # 2. Dynamic Data
    try:
        resp = requests.get(f"{SHARD_URL}/worldconquest/maps/{map_name}/dynamic/public", headers=HEADERS, timeout=2)
        if resp.status_code == 200:
            items = resp.json().get("mapItems", [])
            for item in items:
                if item["iconType"] in IMPORTANT_STRUCTURES:
                    key = f"{item['x']:.3f}_{item['y']:.3f}"
                    flags = item["flags"]
                    
                    is_vp = (flags & FLAG_VICTORY_BASE) != 0
                    is_scorched = (flags & FLAG_IS_SCORCHED) != 0
                    
                    data["structures"][key] = {
                        "team": item["teamId"],
                        "type": item["iconType"],
                        "is_vp": is_vp,
                        "is_scorched": is_scorched
                    }
    except:
        pass

    return data

def get_war_info():
    """Global info of war"""
    try:
        resp = requests.get(f"{SHARD_URL}/worldconquest/war", headers=HEADERS, timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return None

import re
import math

def get_location_name(map_name, x, y):
    """
    Return the location exact (town then hex)
    """
    global _STATIC_DATA_MEMORY

    if x is None or y is None:
        return clean_map_name(map_name)
    
    if not _STATIC_DATA_MEMORY or map_name not in _STATIC_DATA_MEMORY:
        return clean_map_name(map_name)

    items = _STATIC_DATA_MEMORY[map_name].get("mapTextItems", [])
    
    closest_name = "Wilderness"
    min_dist = float('inf')

    found_any = False
    for item in items:
        if item.get("mapMarkerType") in ["Major", "Minor"] and item.get('x') is not None:
            
            dist = math.sqrt((x - item['x'])**2 + (y - item['y'])**2)
            
            if dist < min_dist:
                min_dist = dist
                closest_name = item['text']
                found_any = True
    
    pretty_map = clean_map_name(map_name)

    return f"{closest_name} (in hex {pretty_map})"

def clean_map_name(map_name):
    if map_name.endswith("Hex"):
        map_name = map_name[:-3]
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', map_name)

def update_war_state():
    print("Scanning war state...")
    
    old_state = load_local_data()
    new_state = {}
    maps = get_map_names()
    
    changes_log = []
    
    total_warden_dead_diff = 0
    total_colonial_dead_diff = 0
    total_casualties = 0
    
    vp_warden = 0
    vp_colonial = 0
    total_vp_count = 0

    recent_changes = {}

    active_maps = [m for m in maps if m != "HomeRegionC" and m != "HomeRegionW"]

    for map_name in active_maps:
        map_info = get_map_data(map_name)
        
        if not map_info:
            print(f"No data for {map_name}, skip. (this may be an error !)")
            continue

        new_state[map_name] = map_info
        
        for vp_struct in map_info["structures"].values():
            if vp_struct["is_vp"]:
                if not vp_struct["is_scorched"]:
                    total_vp_count += 1
                    if vp_struct["team"] == "WARDENS":
                        vp_warden += 1
                    elif vp_struct["team"] == "COLONIALS":
                        vp_colonial += 1

        current_w_dead = map_info["casualties"].get("warden", 0)
        current_c_dead = map_info["casualties"].get("colonial", 0)
        total_casualties += (current_w_dead + current_c_dead)

        if map_name in old_state:
            old_map = old_state[map_name]
            
            w_diff = current_w_dead - old_map["casualties"].get("warden", 0)
            c_diff = current_c_dead - old_map["casualties"].get("colonial", 0)
            
            if w_diff < 0: w_diff = 0
            if c_diff < 0: c_diff = 0
            
            total_warden_dead_diff += w_diff
            total_colonial_dead_diff += c_diff
            
            if w_diff + c_diff > 1000:
                changes_log.append(f"{map_name} : Big fights there : ({w_diff}W / {c_diff}C morts/h)")

            new_structs = map_info["structures"]
            old_structs = old_map.get("structures", {})
            
            for key, struct in new_structs.items():
                if key in old_structs:
                    old_s = old_structs[key]
                    
                    old_team = old_s["team"]
                    new_team = struct["team"]
                    
                    old_scorched = old_s.get("is_scorched", False)
                    new_scorched = struct["is_scorched"]
                    
                    if not old_scorched and new_scorched:
                        x_str, y_str = key.split("_")
                        s_x = float(x_str)
                        s_y = float(y_str)
                        full_loc = get_location_name(map_name, s_x, s_y)
                        changes_log.append(f"NUCLEAR ALERT : {full_loc} got litteraly nuked !!!")
                    
                    if not new_scorched and old_team != new_team:
                        
                        x_str, y_str = key.split("_")
                        s_x = float(x_str)
                        s_y = float(y_str)
                        full_loc = get_location_name(map_name, s_x, s_y)

                        if new_team == "NONE":
                            loser = "Wardens" if old_team == "WARDENS" else "Colonials"
                            changes_log.append(f"Contested area : {loser} lost {full_loc}.")
                        
                        else:
                            winner = "Wardens" if new_team == "WARDENS" else "Colonials"
                            if struct["is_vp"]:
                                changes_log.append(f"VICTORY POINT {winner} took {full_loc}, an important city !")
                            else:
                                changes_log.append(f"{winner} took {full_loc}")

                        if map_name not in recent_changes:
                            recent_changes[map_name] = []
                        recent_changes[map_name].append(key)

    war_info = get_war_info()
    required_vp = war_info.get("requiredVictoryTowns", 32) if war_info else 32

    save_local_data(new_state)
    print(f"Update finished. {total_warden_dead_diff}W / {total_colonial_dead_diff}C Deaths detected.")
    
    return {
        "logs": changes_log,
        "warden_dead": total_warden_dead_diff,
        "colonial_dead": total_colonial_dead_diff,
        "vp_warden": vp_warden,
        "vp_colonial": vp_colonial,
        "vp_total": total_vp_count,
        "vp_target": required_vp,
        "recent_changes": recent_changes,
        "total_casualties": total_casualties,
    }

def is_resistance_phase():
    """
    check if it is resistance phase or no.
    """
    try:
        response = requests.get(SHARD_URL)
        response.raise_for_status()
        data = response.json()
        
        winner = data.get("winner", "NONE")
        
        if winner != "NONE":
            return True
        return False
            
    except Exception as e:
        print(f"Error happened : {e}")
        return False

def get_war_winner():
    try:
        response = requests.get(SHARD_URL).json()
        return response.get("winner", "NONE")
    except:
        return "NONE"