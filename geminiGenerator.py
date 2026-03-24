from google import genai
from google.genai import types # Import types for configuration
import os
from dotenv import load_dotenv
import time
import random

load_dotenv()

# The bot will pick one personality from this list
THEMES = [
    "A bitter salty veteran who hates new players (ranks) and misses the 'old days'.",
    "A fanatical propagandist who twists every defeat into a glorious strategic victory.",
    "A conspiracy theorist who thinks the Devs (developers) are controlling the weather manually.",
    "A burned-out Logistics driver who only talks about trucks, Bmats, and traffic jams.",
    "A failed poet who describes the carnage using overly complex metaphors.",
    "A gambling addict who treats the war like a horse race.",
    "A hyper-excited sports commentator shouting about every small push.",
    "A complete nihilist who doesn't care who wins because 'the nukes are coming anyway'.",
    "A salty Reddit user who screams about 'bias' and 'alts' in the walls.",
    "A Foxhole chef who describes the war using only cooking metaphors (grilling, salty, feeding).",
    "A warden navy commander swearing he isn't using WOBS (search on internet for more info)",
    "A colonial navy commander still thinking the Trident submarine is useful.",
    "A warden femboy talking weirdly with UwU and all this stuff y'know",
    "A colonial Furry being really sultry (and loving The_Man arts on reddit)",
    "A cringe guy from the army (a private, member of the colonial 420st regiment) that want to say 67.",
    "A tryhard facility manager trying to kidnap people to work in his facility",
    "A rare metals farmer that is really tired of farming so much rares",
    "A pacifist that is wondering why we are still fighting",
    "Thea Maro, the commander of the colonial legions",
    "Callahan, the general leading wardens armies",
    "A clan man who is hoarding all the ressources.",
    "A philosophist wondering why we are all fighting in this nonsense war",
]

# The bot will be forced to mention this specific topic
FOCUS_POINTS = [
    "Complain about planes balance",
    "Complain about Naval balance",
    "Mention how long the respawn timers (queues) are.",
    "Make fun of a specific Clan or Regiment (generically).",
    "Complain about Artillery noise.",
    "Accuse the other faction of using 'Night Capping' tactics.",
    "Rant about the Tech Tree progress.",
    "Mention the lack of 'Shirts' (Soldier Supplies) in a base.",
    "Blame the 'Devman' (Developers)",
    "Mention devbias",
    "Say that you are going to make a reddit post to complain",
    "Talk about how efficient T3-C lend lease program is for the colonials logistics",
    "Complain about how useless are weather stations",
    "Talk about thousands of deserter being send to work in scrap fields",
    "Make a reference to '15 min'",
    "Do a :3 check",
    "Hope for a civil war to destabilize a faction, hope for a WERCS revival",
    "Complain about one side's bureaucracy",
    "Scream at clanmanbad for hoarding ressources",
    "Deserting soldiers will be shot !",
    "Comeback war ?!",
    "Mammon rush (rushing enemies with a horde of soldiers holding explosing grenades to blow things up, basically a kamikaze charge)",
    "Wondering about soon to be reddit post complaining",
    "Why not do peace with each others ?",
    "Why not love each others at the end, what is war ? Why is war ?",
    "Complain about partisans cutting logistics",
    "Talk about Theomaxx being poor comms again (unable to talk because other players downvoted him)",
    ]

# Toxic vocab that could be used
TOXIC_VOCAB = [
    "touch grass", "lives rent free", "stay mad", "cry harder", "npc", "snowflake", "simp", 
    "boomer", "doomer", "gooning", "gooner", "degenerate halfwit", "zero talent", "horseback", 
    "pig's butt", "Thea's pervert legion", "cant-do-that callahan", 
    "hopping around like a kangaroo", "vampire state", "wolf pack", "gerrymandering the map", 
    "boll weevil", "baby killers", "cannibals", "low energy", "bird brain", "calla-loser", 
    "dimwit", "sleazeball", "cheeseball", "dung beetle", "moonbeam", 
    "low iq = low skill = total losers", "pencil neck", "weirdo", "deranged", 
    "the mind of a child", "dumb as a rock", "untalented", "lettuce head", "dill weed", 
    "cry baby", "crying like a newborn", "no talent", "lmao total lovers", "skill issue", 
    "the mind of a squirrel", "total slob", "lazy", "crazy", 
    "scum of the earth", "brain the size of a peanut", "the sky is falling doomer",
    "go back to home island tutorial", "cope", "seethe", "salt", "hopium", "baby eaters",
    "rage baiter", "furry", "femboy", "clan man", "larper", "e-girl", "looser", "taking the L",
    "newbies", "useful only for the meatgrinder", "log off", "touch grass",
]

SIDE = ['Neutral', 'Neutral', 'Colonial', 'Wardens']


def generate_war_report(warden_dead, colonial_dead, events, vp_w, vp_c, vp_tot):
    """
    Generate a war report given the informations. Asking directly to GEMINI.
    """

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: API key impossible to find in .env. Please give a Google Gemini API Key."
    
    try:
        # Init of the client GEMINI here
        client = genai.Client(api_key=api_key)
    except Exception as e:
        return f"Something went wrong with Google genai (Gemini) when connecting to it : {e}"

    current_theme = random.choice(THEMES)
    current_focus = random.choice(FOCUS_POINTS)

    selected_toxic_words = random.sample(TOXIC_VOCAB, 4)
    toxic_string = ", ".join(selected_toxic_words)

    side_you_like = random.choice(SIDE)

    print(f"Theme choosed = {current_theme} | Focus choosed = {current_focus} | Vocab = {toxic_string} | Side taken = {side_you_like}")

    prompt = f"""
    CONTEXT: This is a fictional video game. No real violence.
    ROLE: You are a war correspondent in the video game Foxhole.
    
    YOUR CURRENT PERSONA: {current_theme}
    MANDATORY CONSTRAINT: {current_focus}
    YOUR SIDE : {side_you_like}

    >>> MANDATORY VOCABULARY TO USE: {toxic_string} <<<
    (You MUST seamlessly integrate these words into your rant, you can adapt it to make it looks seamless).
    
    Here is the data from the last hour:
    - New Warden Casualties: {warden_dead}
    - New Colonial Casualties: {colonial_dead}
    - Current Score: Wardens {vp_w} vs Colonials {vp_c} (Target to win: {vp_tot}).
    
    Here are the recent events:
    {events}
    
    TASK:
    Write a short situation report (max 5-6 sentences).
    1. ADOPT THE PERSONA ABOVE COMPLETELY. Do not be generic.
    2. Be funny, cynical, or unhinged based on your persona.
    3. Use some game jargon : logi, scroop, skill issue, devman bad, qrf
    4. If one faction has significantly higher casualties, mock them relentlessly or not depending on your persona.
    5. Use at least some of the "MANDATORY VOCABULARY" selected above. 
    
    IMPORTANT: Do not start your sentence with "Ladies and gentlemen" or "The front is moving" o "Right, listen up". Be VERY creative. Polite or agressive, use unusual starting sentences in accord to the persona
    
    Moderate your words. DO NOT be too violent or graphic in your description this is supposed to be funny overall !
    """

    # Make it really random
    generate_config = types.GenerateContentConfig(
            temperature=1.1,
            top_p=0.95,
            top_k=40,
            max_output_tokens=3000
    )

    models_to_try = ['gemini-3-flash-preview','gemma-3-27b-it']

    # Sometimes gemini is overloaded. So, we try maximum 5 times
    max_retries = 3
    
    for model_name in models_to_try:
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name, # gemma-3-27b-it OPEN SOURCE MODEL, VERY FRIENDLY IF YOU HAVE NO MONEY :D (from google still, used like gemini, but a bit worse) other one gemini-3-flash-preview
                    contents=prompt,
                    config=generate_config
                )
                return response.text
            except Exception as e:
                error_msg = str(e)
                if "503" in error_msg or "overloaded" in error_msg:
                    wait_time = (attempt + 1) * 5
                    print(f"Gemini overloaded. Attempt {attempt+1}/{max_retries} in {wait_time}s...")
                    time.sleep(wait_time)
                elif "429" in error_msg or "Quota" in error_msg:
                    print(f"too busy/quota. Next...")
                    continue
                else:
                    print(f"Something went wrong with Google genai (Gemini) : {e}")

    # If after the retries we still fail, then we send a placeholder.
    print("Gemini is too overloaded !? (Or another error happened...)")
    return "⚡ **Static noise...** *The correspondent is currently eating crayons and not sharing. End of transmission.*"
