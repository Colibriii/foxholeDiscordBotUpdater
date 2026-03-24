import discord
import os
import json
import datetime
from discord.ext import commands, tasks
from dotenv import load_dotenv
import geminiGenerator
import asyncio
import foxhole_client
import mapGenerator
import staticManager

# Config. Make sure to have a correct discord bot token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Channels directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHANNELS_FILE = os.path.join(BASE_DIR, "channels.json")

# Declaration of intents (you need to make sure you also declared it on discord bot website or it'll be refused)
intents = discord.Intents.default()
intents.message_content = True

# Basic commands mainly used for test and debug
bot = commands.Bot(command_prefix="!", intents=intents)

# Global embed
embed = None

# Previous stats are stocked in a json files. So if the server crashed we can keep up some old info.

############################################
# Management of the channels and saving

def load_channels():
    if os.path.exists(CHANNELS_FILE):
        try:
            with open(CHANNELS_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_channels(channels):
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f)

def add_channel(channel_id):
    channels = load_channels()
    if channel_id not in channels:
        channels.append(channel_id)
        save_channels(channels)
        return True
    return False

def remove_channel(channel_id):
    channels = load_channels()
    if channel_id in channels:
        channels.remove(channel_id)
        save_channels(channels)
        return True
    return False

############################################

# Booting of the bot
@bot.event
async def on_ready():
    print(f'Connected as {bot.user.name}')
    
    # This is the server i use for tests, and force the bot to update it first.
    DevServer = discord.Object(id=1469077454546276571)

    try:
        bot.tree.copy_global_to(guild=DevServer)

        synced = await bot.tree.sync()
        print(f"{len(synced)} commands synchronised.")
    except Exception as e:
        print(f"Error during synchronisation : {e}")

    # Giving the bot a status here
    activity = discord.Activity(
        type=discord.ActivityType.watching, 
        name="The vision ! /help"
    )
    await bot.change_presence(status=discord.Status.online, activity=activity)

    await bot.loop.run_in_executor(None, staticManager.load_static_data)

    # This is where we start the loop for generation.
    if not background_generator.is_running():
        background_generator.start()

##ROUTINE !
async def routine():
    global embed
    print("#" * 30)
    print(f"[{datetime.datetime.now().strftime('%H:%M')}] Analysing the front.")

    # Getting current stats from foxhole war API
    report_data = await bot.loop.run_in_executor(None,foxhole_client.update_war_state)
    
    warden_dead = f"{report_data["warden_dead"]:,}".replace(",", " ")
    colonial_dead = f"{report_data["colonial_dead"]:,}".replace(",", " ")
    events_list = report_data["logs"]
    total_casualties = f"{report_data["total_casualties"]:,}".replace(",", " ")

    vp_w = report_data["vp_warden"]
    vp_c = report_data["vp_colonial"]
    vp_target = report_data["vp_target"]
    changes = report_data["recent_changes"]
    
    events_text = "\n".join(events_list)
    if not events_text:
        events_text = "No territory changes. Just maximum larp."

    print(f"Result : {warden_dead}W / {colonial_dead}C morts. {len(events_list)} events.")

    if foxhole_client.is_resistance_phase():
        report = "This is resistance phase !"
    else :
        print("Asking GEMINI !")
        report = await bot.loop.run_in_executor(None,geminiGenerator.generate_war_report,warden_dead, colonial_dead, events_text, vp_w, vp_c, vp_target)

    embed_color = 0x2f3136
    if vp_w > vp_c: embed_color = 0x2c558f
    elif vp_c > vp_w: embed_color = 0x516c4b

    embed = discord.Embed(
    title="📡 WAR REPORT OF THE LAST HOUR",
    description=report,
    color=embed_color,
    timestamp=datetime.datetime.now()
    )

    embed.add_field(
    name="🏆 SCORE", 
    value=f"🔵 **{vp_w}** vs **{vp_c}** 🟢\n*(Objective : {vp_target})*", 
    inline=True
    )

    embed.add_field(
    name="☠️ CASUALTIES (Last hour)", 
    value=f"🔵 `{warden_dead}`\n🟢 `{colonial_dead}`", 
    inline=True
    )

    embed.add_field(
        name="Total war casulaties",
        value=f"{total_casualties}",
        inline=True
    )

    embed.set_footer(text="Foxhole War Correspondent Bot", icon_url="https://imgur.com/K4YlwPT")
    
    await bot.loop.run_in_executor(None,mapGenerator.generate_world_map,vp_w,vp_c,vp_target,changes)

    print("Report succefully generated.")

    print("Sending to all channels subbed !")
    
    channels_ids = load_channels()
    
    if not channels_ids:
        print("No channels found")
    
    for channel_id in channels_ids:
        channel = bot.get_channel(channel_id)
        if channel:
            try:
                map_path = os.path.join(BASE_DIR, "world_map_hex.png")

                if os.path.exists(map_path):
                    file = discord.File(map_path)
                
                await channel.send(embed=embed, file=file)
                print(f"   -> sent in {channel.guild.name} / #{channel.name}")
            except Exception as e:
                print(f"   Error when sendint to {channel_id} : {e}")
        else:
            print(f"   Problem occured with {channel_id}. (Likely bot got kicked of server)")

    print("Sent to all subscribed peoples !")

    w_clean = int(str(warden_dead).replace(" ", ""))
    c_clean = int(str(colonial_dead).replace(" ", ""))
    
    total_hourly = w_clean + c_clean
    
    total_fmt = f"{total_hourly:,}".replace(",", " ")

    new_status = f"🔵{vp_w} vs 🟢{vp_c} | ☠️ {total_fmt}/h"
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name=new_status
        )
    )

    print("Status changed !")

    print("End of the routine.")
    print("#" * 30)


# we create a loop repeating itself every hour to run the routine.
@tasks.loop(minutes=60)
async def background_generator():
    await routine()

@background_generator.before_loop
async def before_bg():
    global previous_stats
    await bot.wait_until_ready()

    now = datetime.datetime.now()
    next_hour = now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
    delta = (next_hour - now).total_seconds()
    print(f"⏳ Synchronisation : i sleep {int(delta/60)} min so i can start at {next_hour.strftime('%H:%M')}...")
    
    await asyncio.sleep(delta)


#### COMMANDS SECTION

# Command
@bot.tree.command(name="report", description="What happened the last hour on foxhole ?")
async def rapport(interaction: discord.Interaction):
    map_path = os.path.join(BASE_DIR, "world_map_hex.png")

    if os.path.exists(map_path):
        file = discord.File(map_path)
        
        await interaction.response.send_message(embed=embed, file=file)
    else:
        await interaction.response.send_message("Something went wrong*")

@bot.tree.command(name="set_display", description="Enable automatic updates on this channel.")
async def set_display(interaction: discord.Interaction):
    added = add_channel(interaction.channel_id)
    if added:
        await interaction.response.send_message(f"This channel (<#{interaction.channel_id}>) will receive automatically the updates.")
    else:
        await interaction.response.send_message("Error occured.", ephemeral=True)

@bot.tree.command(name="remove_display", description="Disable automatic updates from this channel.")
async def remove_display(interaction: discord.Interaction):
    removed = remove_channel(interaction.channel_id)
    if removed:
        await interaction.response.send_message(f"This channel (<#{interaction.channel_id}>) has been removed from automatic updates.")
    else:
        await interaction.response.send_message("Error occured.", ephemeral=True)

@bot.tree.command(name="help", description="Displays the list of commands and the user guide, and useful informations.")
async def help_cmd(interaction: discord.Interaction):
    
    embed = discord.Embed(
        title="📚 Help - Foxhole War Correspondent",
        description="I am a bot tracking the Foxhole war in real-time.\nI roast the front every hour.\n\n This was developped by '.colibri' for any help please reach out to him.\nThis bot is still in developpement, and some things may not work perfectly. Discord : https://discord.gg/B4hCxyfUyN",
        color=0xff9900
    )

    embed.add_field(
        name="📢 Public Commands",
        value=(
            "**/report** : Displays the latest situation report (Score + Map).\n"
            "**/help** : Displays this help message."
        ),
        inline=False
    )

    embed.add_field(
        name="⚙️ Administration (Admin Only)",
        value=(
            "**/set_display** : Sets this channel to receive automatic hourly reports.\n"
            "**/remove_display** : Stops automatic reporting in this channel."
        ),
        inline=False
    )

    embed.add_field(
        name="🗺️ Map Legend",
        value=(
            "🔵 **Light Blue**: Stable Warden Territory.\n"
            "🟦 **Dark Blue**: **Recent Warden Capture** (Last hour).\n"
            "🟢 **Light Green**: Stable Colonial Territory.\n"
            "🟩 **Dark Green**: **Recent Colonial Capture** (Last hour).\n"
            "⚪ **Grey**: Neutral / Contested Zone (Relic/TownHall destroyed)."
        ),
        inline=False
    )

    embed.set_footer(text="Developed for the Foxhole community. Using GEMINI AI on a very low use.")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# FORCE UPDATE, DEV TOOL INTENDED ONLY. PUT IN COMMENT WHEN NOT OF USE #################################################
# force la génération sans attendre 1h
@bot.command(name="force")
async def force(ctx):
    await ctx.send("Disabled command")

# Now running the bot.
print("Bot should run now.")
bot.run(TOKEN)
