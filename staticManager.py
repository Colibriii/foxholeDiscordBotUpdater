import requests
import json
import os
import sys

CACHE_FILE = "static_data_cache.json"
API_URL = "https://war-service-live.foxholeservices.com/api"

def fetch_map_names():
    """
    get all HEXs names
    """
    try:
        response = requests.get(f"{API_URL}/worldconquest/maps")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error occured when fetching map names : {e}")
    return []

def download_and_save_static_data():
    """
    Download ALL static data
    """
    print("Downloading static data..")
    
    map_names = fetch_map_names()
    full_static_data = {}

    total = len(map_names)
    for i, map_name in enumerate(map_names):
        print(f"[{i+1}/{total}] Downloading {map_name}...")
        
        try:
            # On appelle l'API Static pour chaque map
            res = requests.get(f"{API_URL}/worldconquest/maps/{map_name}/static")
            if res.status_code == 200:
                data = res.json()
                
                # OPTIMISATION : On ne garde QUE 'mapTextItems' (les noms).
                # Le reste (arbres, routes...) est inutile pour ton bot et pèse lourd.
                full_static_data[map_name] = {
                    "mapTextItems": data.get("mapTextItems", [])
                }
        except Exception as e:
            print(f"Impossible to load {map_name}: {e}")

    # Sauvegarde dans le fichier JSON
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(full_static_data, f, ensure_ascii=False)
    
    print(f"Static data saved {CACHE_FILE}")
    return full_static_data

def load_static_data():
    """Load static data from json, or create them if not existing."""
    if os.path.exists(CACHE_FILE):
        print("Loading data or creating them...")
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return download_and_save_static_data()