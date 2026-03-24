import requests
from PIL import Image, ImageDraw, ImageOps, ImageFont
import math
import os

HEX_RADIUS = 100
VORONOI_PRECISION = 32

COLOR_WARDEN = (44, 85, 143)
COLOR_COLONIAL = (81, 108, 75)
COLOR_NEUTRAL = (200, 200, 200)
COLOR_WARDEN_DARK = (20, 40, 90)
COLOR_COLONIAL_DARK = (40, 60, 35)

API_URL = "https://war-service-live.foxholeservices.com/api" # Able
API_URL_3 = "https://war-service-live-3.foxholeservices.com/api" # Charlie

WORLD_GRID = {
    "OlavisWakeHex": (-2, 2),

    "PariPeakHex": (-1, 1),
    "PalantineBermHex": (-1, 2),
    "OarbreakerHex": (-1, 3),

    "KuuraStrandHex": (0, 1),
    "GutterHex": (0, 2),
    "FishermansRowHex": (0, 3),
    "StemaLandingHex": (0, 4),

    "NevishLineHex": (1, 1),
    "FarranacCoastHex": (1, 2),
    "WestgateHex": (1, 3),
    "OriginHex": (1, 4),

    "CallumsCapeHex": (2, 1),
    "StonecradleHex": (2, 2),
    "KingsCageHex": (2, 3),
    "SableportHex": (2, 4),
    "AshFieldsHex": (2, 5),

    "SpeakingWoodsHex": (3, 0),
    "MooringCountyHex": (3, 1),
    "LinnMercyHex": (3, 2),
    "LochMorHex": (3, 3),
    "HeartlandsHex": (3, 4),
    "RedRiverHex": (3, 5),

    "BasinSionnachHex": (4, 0),
    "ReachingTrailHex": (4, 1),
    "CallahansPassageHex": (4, 2),
    "DeadLandsHex": (4, 3),
    "UmbralWildwoodHex": (4, 4),
    "GreatMarchHex": (4, 5),
    "KalokaiHex": (4, 6),

    "HowlCountyHex": (5, 0),
    "ViperPitHex": (5, 1),
    "MarbanHollow": (5, 2),
    "DrownedValeHex": (5, 3),
    "ShackledChasmHex": (5, 4),
    "AcrithiaHex": (5, 5),

    "ClansheadValleyHex": (6, 1),
    "WeatheredExpanseHex": (6, 2),
    "ClahstraHex": (6, 3),
    "AllodsBightHex": (6, 4),
    "TerminusHex": (6, 5),

    "MorgensCrossingHex": (7, 1),
    "StlicanShelfHex": (7, 2),
    "EndlessShoreHex": (7, 3),
    "ReaversPassHex": (7, 4),

    "GodcroftsHex": (8, 2),
    "TempestIslandHex": (8, 3),
    "WrestaHex": (8, 4),
    "OnyxHex": (8, 5),

    "LykosIsleHex": (9, 2),
    "TheFingersHex": (9, 3),
    "TyrantFoothillsHex": (9, 4),

    "PipersEnclaveHex": (10, 4),
}

def get_api_url(shard):
    return API_URL_3 if shard == 3 else API_URL

def get_data(map_name, type_data, shard=1):
    try:
        headers = { "User-Agent": "FoxholeWarBot/2.2 From .colibri" }
        url_base = get_api_url(shard)
        url = f"{url_base}/worldconquest/maps/{map_name}/{type_data}"
        resp = requests.get(url, headers=headers, timeout=2)
        return resp.json() if resp.status_code == 200 else None
    except:
        return None

def create_hex_mask(radius):
    hex_width = 2 * radius
    hex_height = math.sqrt(3) * radius
    
    w = int(math.ceil(hex_width))
    h = int(math.ceil(hex_height))
    
    mask = Image.new('L', (w, h), 0)
    draw = ImageDraw.Draw(mask)
    
    center_x = w / 2
    center_y = h / 2
    
    points = []
    for i in range(6):
        angle_deg = 60 * i 
        angle_rad = math.radians(angle_deg)
        
        x = center_x + (radius - 1) * math.cos(angle_rad)
        y = center_y + (radius - 1) * math.sin(angle_rad)
        points.append((x, y))
    
    draw.polygon(points, fill=255)
    return mask, w, h

def generate_single_hex(map_name, radius=HEX_RADIUS, return_image=False, highlight_list=None, shard=1):
    mask, w, h = create_hex_mask(radius)
    img = Image.new("RGBA", (w, h), (0,0,0,0))
    
    static = get_data(map_name, "static", shard)
    dynamic = get_data(map_name, "dynamic/public", shard)
    
    if not static or not dynamic:
        if return_image: return None
        return None

    bases = []
    if highlight_list is None:
        highlight_list = []
        
    for item in dynamic.get("mapItems", []):
        if item["iconType"] in [56, 57, 58, 45, 27]:
             key = f"{item['x']:.3f}_{item['y']:.3f}"
             is_fresh = key in highlight_list
             
             bases.append({
                 "x": item["x"], 
                 "y": item["y"], 
                 "team": item["teamId"],
                 "is_fresh": is_fresh
             })
    
    pixels = img.load()
    step = max(1, int(w / VORONOI_PRECISION))
    
    if bases:
        for px in range(0, w):
            for py in range(0, h):
                if mask.getpixel((px, py)) == 0: continue

                nx, ny = px/w, py/h
                closest_dist = 2.0
                closest_team = "NONE"
                closest_is_fresh = False
                
                for base in bases:
                    dist = ((nx - base["x"]) * (w/h))**2 + (ny - base["y"])**2
                    if dist < closest_dist:
                        closest_dist = dist
                        closest_team = base["team"]
                        closest_is_fresh = base["is_fresh"]
                
                col = COLOR_NEUTRAL
                if closest_team == "WARDENS": 
                    col = COLOR_WARDEN_DARK if closest_is_fresh else COLOR_WARDEN
                elif closest_team == "COLONIALS": 
                    col = COLOR_COLONIAL_DARK if closest_is_fresh else COLOR_COLONIAL
                
                pixels[px, py] = col + (255,)
    else:
        draw = ImageDraw.Draw(img)
        draw.rectangle((0,0,w,h), fill=COLOR_NEUTRAL)

    draw = ImageDraw.Draw(img)
    center_x, center_y = w / 2, h / 2
    points = []
    for i in range(6):
        angle_deg = 60 * i 
        angle_rad = math.radians(angle_deg)
        
        x = center_x + (radius - 1) * math.cos(angle_rad)
        y = center_y + (radius - 1) * math.sin(angle_rad)
        points.append((x, y))
    
    points.append(points[0])
    draw.line(points, fill="black", width=3)
    
    for base in bases:
        bx, by = base["x"] * w, base["y"] * h
        r = 3
        fill = "white"
        if base["team"] == "WARDENS": fill = (180, 220, 255)
        if base["team"] == "COLONIALS": fill = (200, 255, 180)
        draw.ellipse((bx-r, by-r, bx+r, by+r), fill=fill, outline="black")

    clean_name = map_name.replace("Hex", "")
    initials = "".join([c for c in clean_name if c.isupper()])
    if len(initials) == 1 and len(clean_name) > 1: initials = clean_name[:2].upper()

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 40)
    except:
        font = ImageFont.load_default()

    draw.text((w/2, h/2), initials, font=font, anchor="mm", fill="white", stroke_width=2, stroke_fill="black")

    img.putalpha(mask)

    if return_image:
        return img
    else:
        suffix = "-3" if shard == 3 else ""
        filename = f"{map_name}_hex{suffix}.png"
        img.save(filename)
        return filename

def generate_world_map(vp_w=0, vp_c=0, vp_target=32, recent_changes=None, shard=1):
    print(f"Generating map for Shard {shard}!")
    
    if recent_changes is None:
        recent_changes = {}

    url_base = get_api_url(shard)
    try:
        maps = requests.get(f"{url_base}/worldconquest/maps").json()
    except:
        print("Error fetching map list for generation.")
        return None
    
    hex_w = int(2 * HEX_RADIUS)
    hex_h = int(math.sqrt(3) * HEX_RADIUS)
    col_step = int(hex_w * 0.75)
    row_step = hex_h
    
    valid_positions = [WORLD_GRID[m] for m in maps if m in WORLD_GRID]
    if not valid_positions: return None

    all_xs = [pos[0] for pos in valid_positions]
    all_ys = [pos[1] for pos in valid_positions]
    min_x, max_x = min(all_xs), max(all_xs)
    min_y, max_y = min(all_ys), max(all_ys)
    
    CANVAS_W = int((max_x - min_x + 3) * col_step) + hex_w 
    CANVAS_H = int((max_y - min_y + 3) * row_step) + hex_h
    
    world_img = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    
    for map_name in maps:
        if map_name in ["HomeRegionC", "HomeRegionW"]: continue
        if map_name not in WORLD_GRID: continue
            
        gx, gy = WORLD_GRID[map_name]
        map_highlights = recent_changes.get(map_name, [])
        
        tile = generate_single_hex(map_name, radius=HEX_RADIUS, return_image=True, highlight_list=map_highlights, shard=shard)
        
        if tile:
            draw_x = gx - min_x
            draw_y = gy - min_y
            offset_y = (hex_h // 2) if (gx % 2 == 1) else 0
            
            px = (draw_x * col_step) + 100
            py = (draw_y * row_step) + offset_y + 100
            world_img.alpha_composite(tile, (px, py))
            
    bbox = world_img.getbbox()
    if bbox:
        world_img = world_img.crop(bbox)
        margin = 60
        final_w = world_img.width + 2 * margin
        final_h = world_img.height + 2 * margin
        final_img = Image.new("RGBA", (final_w, final_h), (0, 0, 0, 0))
        final_img.paste(world_img, (margin, margin))
        world_img = final_img
    
    
    draw = ImageDraw.Draw(world_img)
    
    try:
        label_font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 40)
        number_font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 65)
    except:
        label_font = ImageFont.load_default()
        number_font = ImageFont.load_default()

    text_w = f"{vp_w} / {vp_target}"
    label_w = "WARDENS"
    
    x_w = world_img.width - 30
    y_w = 30
    
    draw.text((x_w, y_w), label_w, font=label_font, fill=COLOR_WARDEN, anchor="ra", stroke_width=3, stroke_fill="black")
    draw.text((x_w, y_w + 50), text_w, font=number_font, fill="white", anchor="ra", stroke_width=4, stroke_fill="black")
    
    draw.rectangle((x_w + 10, y_w, x_w + 25, y_w + 125), fill=COLOR_WARDEN, outline="black")

    text_c = f"{vp_c} / {vp_target}"
    label_c = "COLONIALS"
    
    x_c = 30
    y_c = world_img.height - 30
    
    draw.text((x_c, y_c - 20), text_c, font=number_font, fill="white", anchor="lb", stroke_width=4, stroke_fill="black")
    draw.text((x_c, y_c - 95), label_c, font=label_font, fill=COLOR_COLONIAL, anchor="lb", stroke_width=3, stroke_fill="black")
    
    draw.rectangle((x_c - 25, y_c - 135, x_c - 10, y_c), fill=COLOR_COLONIAL, outline="black")

    shard_name = "ABLE" if shard == 1 else "CHARLIE"
    
    if vp_w > vp_c:
        shard_color = COLOR_WARDEN
    elif vp_c > vp_w:
        shard_color = COLOR_COLONIAL
    else:
        shard_color = COLOR_NEUTRAL

    draw.text((30, 30), shard_name, font=number_font, fill=shard_color, anchor="la", stroke_width=4, stroke_fill="black")

    if world_img.width > 2000:
        ratio = 2000 / world_img.width
        new_h = int(world_img.height * ratio)
        world_img = world_img.resize((2000, new_h), resample=Image.Resampling.BILINEAR)

    suffix = "-3" if shard == 3 else ""
    filename = f"world_map_hex{suffix}.png"
    
    world_img.save(filename, "PNG")
    print(f"Map generated and saved as {filename} !")
    return filename

# Local testing
if __name__ == "__main__":
    generate_world_map(16, 16, shard=1)