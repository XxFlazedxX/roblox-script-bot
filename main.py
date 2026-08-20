import discord
from discord.ext import commands
import os
import time
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

bans_data = {}
script_players = {}

ALLOWED_USERS = [921818523305656370, 1376299488703938691]

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=discord.Game(name="/help | Roblox Script"))
    try:
        await bot.tree.sync()
        print("Slash commands synced successfully!")
    except Exception as e:
        print(f"Error syncing commands: {e}")

def is_allowed(interaction):
    return interaction.user.id in ALLOWED_USERS

@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"Pong! Latency: {latency}ms")

@bot.tree.command(name="addplayer", description="Add a player running the script")
async def add_player(interaction: discord.Interaction, roblox_username: str, roblox_id: int = None):
    if not is_allowed(interaction):
        await interaction.response.send_message("You don't have permission!", ephemeral=True)
        return
    guild_id = str(interaction.guild.id)
    if guild_id not in script_players:
        script_players[guild_id] = {}
    if roblox_username in script_players[guild_id]:
        script_players[guild_id][roblox_username]['last_seen'] = time.time()
        embed = discord.Embed(title="Player Updated", description=f"Updated {roblox_username}'s session", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)
        return
    script_players[guild_id][roblox_username] = {
        'id': roblox_id,
        'joined_at': time.time(),
        'last_seen': time.time(),
        'status': 'active',
        'added_by': str(interaction.user)
    }
    embed = discord.Embed(title="Player Added", description=f"{roblox_username} is now running the script!", color=discord.Color.green())
    if roblox_id:
        embed.add_field(name="Roblox ID", value=roblox_id)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="removeplayer", description="Remove a player from the script")
async def remove_player(interaction: discord.Interaction, roblox_username: str):
    if not is_allowed(interaction):
        await interaction.response.send_message("You don't have permission!", ephemeral=True)
        return
    guild_id = str(interaction.guild.id)
    if guild_id not in script_players:
        embed = discord.Embed(title="No Players", description="No players running the script.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return
    if roblox_username in script_players[guild_id]:
        del script_players[guild_id][roblox_username]
        embed = discord.Embed(title="Player Removed", description=f"{roblox_username} has been removed.", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title="Not Found", description=f"{roblox_username} is not running the script.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="statusplayers", description="Show all players running the script")
async def status_players(interaction: discord.Interaction):
    if not is_allowed(interaction):
        await interaction.response.send_message("You don't have permission!", ephemeral=True)
        return
    guild_id = str(interaction.guild.id)
    if guild_id not in script_players or not script_players[guild_id]:
        embed = discord.Embed(title="Script Status", description="No players running the script.", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)
        return
    current_time = time.time()
    active = []
    inactive = []
    for username, data in script_players[guild_id].items():
        if current_time - data['last_seen'] < 300:
            active.append(username)
        else:
            inactive.append(username)
    embed = discord.Embed(title="Script Status", description=f"Total: {len(script_players[guild_id])} players", color=discord.Color.green() if active else discord.Color.blue())
    if active:
        embed.add_field(name=f"🟢 Online ({len(active)})", value="\n".join(active[:10]), inline=False)
    if inactive:
        embed.add_field(name=f"🔴 Inactive ({len(inactive)})", value="\n".join(inactive[:5]), inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="scriptban", description="Ban a player from the script")
async def script_ban(interaction: discord.Interaction, roblox_username: str, reason: str = "No reason"):
    if not is_allowed(interaction):
        await interaction.response.send_message("You don't have permission!", ephemeral=True)
        return
    guild_id = str(interaction.guild.id)
    if guild_id not in bans_data:
        bans_data[guild_id] = {}
    if roblox_username in bans_data[guild_id]:
        embed = discord.Embed(title="Already Banned", description=f"{roblox_username} is already banned.", color=discord.Color.orange())
        await interaction.response.send_message(embed=embed)
        return
    bans_data[guild_id][roblox_username] = {
        'type': 'script_ban',
        'reason': reason,
        'banned_by': str(interaction.user),
        'timestamp': time.time()
    }
    if guild_id in script_players and roblox_username in script_players[guild_id]:
        del script_players[guild_id][roblox_username]
    embed = discord.Embed(title="Script Ban Added", description=f"{roblox_username} banned from the script!", color=discord.Color.red())
    embed.add_field(name="Reason", value=reason)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="scriptunban", description="Unban a player from the script")
async def script_unban(interaction: discord.Interaction, roblox_username: str):
    if not is_allowed(interaction):
        await interaction.response.send_message("You don't have permission!", ephemeral=True)
        return
    guild_id = str(interaction.guild.id)
    if guild_id not in bans_data or roblox_username not in bans_data[guild_id]:
        embed = discord.Embed(title="Not Found", description=f"{roblox_username} is not banned.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return
    del bans_data[guild_id][roblox_username]
    embed = discord.Embed(title="Script Unban", description=f"{roblox_username} unbanned from the script!", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="scriptbanlist", description="Show all banned players")
async def script_banlist(interaction: discord.Interaction):
    if not is_allowed(interaction):
        await interaction.response.send_message("You don't have permission!", ephemeral=True)
        return
    guild_id = str(interaction.guild.id)
    if guild_id not in bans_data:
        embed = discord.Embed(title="Ban List", description="No players banned.", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)
        return
    script_bans = {k: v for k, v in bans_data[guild_id].items() if v['type'] == 'script_ban'}
    if not script_bans:
        embed = discord.Embed(title="Ban List", description="No players banned.", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)
        return
    ban_list = []
    for username, data in script_bans.items():
        ban_list.append(f"{username} - {data['reason']}")
    embed = discord.Embed(title="Script Ban List", description="\n".join(ban_list[:20]), color=discord.Color.red())
    embed.set_footer(text=f"Total: {len(ban_list)} banned players")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="scriptkick", description="Kick a player from the script")
async def script_kick(interaction: discord.Interaction, roblox_username: str, reason: str = "No reason"):
    if not is_allowed(interaction):
        await interaction.response.send_message("You don't have permission!", ephemeral=True)
        return
    guild_id = str(interaction.guild.id)
    if guild_id not in script_players or roblox_username not in script_players[guild_id]:
        embed = discord.Embed(title="Not Found", description=f"{roblox_username} is not running the script.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return
    del script_players[guild_id][roblox_username]
    embed = discord.Embed(title="Script Kick", description=f"{roblox_username} kicked from the script!", color=discord.Color.orange())
    embed.add_field(name="Reason", value=reason)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="scriptstats", description="Script statistics")
async def script_stats(interaction: discord.Interaction):
    if not is_allowed(interaction):
        await interaction.response.send_message("You don't have permission!", ephemeral=True)
        return
    guild_id = str(interaction.guild.id)
    total_players = len(script_players.get(guild_id, {}))
    total_bans = len([b for b in bans_data.get(guild_id, {}).values() if b['type'] == 'script_ban'])
    current_time = time.time()
    active = 0
    for data in script_players.get(guild_id, {}).values():
        if current_time - data['last_seen'] < 300:
            active += 1
    embed = discord.Embed(title="Script Stats", color=discord.Color.blue())
    embed.add_field(name="Total Players", value=str(total_players), inline=True)
    embed.add_field(name="Active Players", value=str(active), inline=True)
    embed.add_field(name="Total Bans", value=str(total_bans), inline=True)
    await interaction.response.send_message(embed=embed)

bot.run(os.environ.get('TOKEN'))
