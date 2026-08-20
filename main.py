import discord
from discord.ext import commands
import os
import time
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

bans_data = {}
script_players = {}

ALLOWED_USERS = [921818523305656370, 1376299488703938691]

def is_allowed(interaction):
    return interaction.user.id in ALLOWED_USERS

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=discord.Game(name="/help | Roblox Script"))
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands!")
    except Exception as e:
        print(e)

@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    if not is_allowed(interaction):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"Pong! Latency: {latency}ms")

@bot.tree.command(name="hello", description="Say hello to the bot")
async def hello(interaction: discord.Interaction):
    if not is_allowed(interaction):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    await interaction.response.send_message(f"Hello {interaction.user.mention}!")

@bot.tree.command(name="addplayer", description="Add a player running the script")
async def add_player(interaction: discord.Interaction, roblox_username: str, roblox_id: int = None):
    if not is_allowed(interaction):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    guild_id = str(interaction.guild.id)
    
    if guild_id not in script_players:
        script_players[guild_id] = {}
    
    if roblox_username in script_players[guild_id]:
        script_players[guild_id][roblox_username]['last_seen'] = time.time()
        script_players[guild_id][roblox_username]['id'] = roblox_id or script_players[guild_id][roblox_username]['id']
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
    
    embed = discord.Embed(title="Player Added to Script", description=f"{roblox_username} is now running the script!", color=discord.Color.green())
    if roblox_id:
        embed.add_field(name="Roblox ID", value=roblox_id)
    embed.add_field(name="Added By", value=str(interaction.user))
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="removeplayer", description="Remove a player from the script")
async def remove_player(interaction: discord.Interaction, roblox_username: str):
    if not is_allowed(interaction):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    guild_id = str(interaction.guild.id)
    
    if guild_id not in script_players:
        embed = discord.Embed(title="No Players Found", description="No players are currently running the script.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return
    
    if roblox_username in script_players[guild_id]:
        del script_players[guild_id][roblox_username]
        embed = discord.Embed(title="Player Removed", description=f"{roblox_username} has been removed from the script.", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title="Player Not Found", description=f"{roblox_username} is not currently running the script.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="statusplayers", description="Show all players currently running the script")
async def status_players(interaction: discord.Interaction):
    if not is_allowed(interaction):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    guild_id = str(interaction.guild.id)
    
    if guild_id not in script_players or not script_players[guild_id]:
        embed = discord.Embed(title="Script Status", description="No players are currently running the script.", color=discord.Color.blue())
        embed.set_footer(text=f"Requested by {interaction.user}")
        await interaction.response.send_message(embed=embed)
        return
    
    current_time = time.time()
    active_players = []
    inactive_players = []
    
    for username, data in script_players[guild_id].items():
        time_diff = current_time - data['last_seen']
        if time_diff < 300:
            active_players.append((username, data))
        else:
            inactive_players.append((username, data))
    
    embed = discord.Embed(title="Script Status - Active Players", description=f"Total players: {len(script_players[guild_id])}", color=discord.Color.green() if active_players else discord.Color.blue())
    
    if active_players:
        player_list = []
        for username, data in active_players:
            joined = datetime.fromtimestamp(data['joined_at']).strftime('%H:%M:%S')
            player_list.append(f"{username} (ID: {data['id'] or 'N/A'}) - Active since {joined}")
        embed.add_field(name=f"Online ({len(active_players)})", value="\n".join(player_list[:10]), inline=False)
        if len(active_players) > 10:
            embed.add_field(name="", value=f"...and {len(active_players) - 10} more", inline=False)
    
    if inactive_players:
        player_list = []
        for username, data in inactive_players[:5]:
            last_seen = datetime.fromtimestamp(data['last_seen']).strftime('%H:%M:%S')
            player_list.append(f"{username} - Last seen: {last_seen}")
        embed.add_field(name=f"Inactive ({len(inactive_players)})", value="\n".join(player_list) if player_list else "No inactive players", inline=False)
    
    embed.set_footer(text=f"Last updated | Requested by {interaction.user}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="playerinfo", description="Get detailed info about a script player")
async def player_info(interaction: discord.Interaction, roblox_username: str):
    if not is_allowed(interaction):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    guild_id = str(interaction.guild.id)
    
    if guild_id not in script_players or roblox_username not in script_players[guild_id]:
        embed = discord.Embed(title="Player Not Found", description=f"{roblox_username} is not currently running the script.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return
    
    data = script_players[guild_id][roblox_username]
    current_time = time.time()
    time_diff = current_time - data['last_seen']
    
    embed = discord.Embed(title=f"Player Info: {roblox_username}", color=discord.Color.blue())
    embed.add_field(name="Roblox ID", value=data['id'] or "N/A", inline=True)
    embed.add_field(name="Status", value="Active" if time_diff < 300 else "Inactive", inline=True)
    embed.add_field(name="Added By", value=data['added_by'], inline=True)
    embed.add_field(name="Joined At", value=datetime.fromtimestamp(data['joined_at']).strftime('%Y-%m-%d %H:%M:%S'), inline=True)
    embed.add_field(name="Last Seen", value=datetime.fromtimestamp(data['last_seen']).strftime('%Y-%m-%d %H:%M:%S'), inline=True)
    embed.add_field(name="Session Duration", value=f"{int(time_diff // 60)} minutes ago" if time_diff < 300 else f"{int(time_diff // 60)} minutes ago (inactive)", inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="scriptban", description="Ban a player from the script")
async def script_ban(interaction: discord.Interaction, roblox_username: str, reason: str = "No reason provided"):
    if not is_allowed(interaction):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    guild_id = str(interaction.guild.id)
    
    if guild_id not in bans_data:
        bans_data[guild_id] = {}
    
    if roblox_username in bans_data[guild_id]:
        embed = discord.Embed(title="Already Banned", description=f"{roblox_username} is already banned from the script.", color=discord.Color.orange())
        await interaction.response.send_message(embed=embed)
        return
    
    bans_data[guild_id][roblox_username] = {
        'type': 'script_ban',
        'reason': reason,
        'banned_by': str(interaction.user),
        'timestamp': time.time(),
        'roblox_id': None
    }
    
    if guild_id in script_players and roblox_username in script_players[guild_id]:
        del script_players[guild_id][roblox_username]
    
    embed = discord.Embed(title="Script Ban Added", description=f"{roblox_username} has been banned from the script!", color=discord.Color.red())
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Banned By", value=str(interaction.user), inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="scriptunban", description="Unban a player from the script")
async def script_unban(interaction: discord.Interaction, roblox_username: str):
    if not is_allowed(interaction):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    guild_id = str(interaction.guild.id)
    
    if guild_id not in bans_data or roblox_username not in bans_data[guild_id]:
        embed = discord.Embed(title="Not Found", description=f"{roblox_username} is not banned from the script.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return
    
    if bans_data[guild_id][roblox_username]['type'] != 'script_ban':
        embed = discord.Embed(title="Not a Script Ban", description=f"{roblox_username} has a different type of ban.", color=discord.Color.orange())
        await interaction.response.send_message(embed=embed)
        return
    
    del bans_data[guild_id][roblox_username]
    
    embed = discord.Embed(title="Script Unban", description=f"{roblox_username} has been unbanned from the script!", color=discord.Color.green())
    embed.add_field(name="Unbanned By", value=str(interaction.user), inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="scriptbanlist", description="Show all script-banned players")
async def script_banlist(interaction: discord.Interaction):
    if not is_allowed(interaction):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    guild_id = str(interaction.guild.id)
    
    if guild_id not in bans_data:
        embed = discord.Embed(title="Script Ban List", description="No players are banned from the script.", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)
        return
    
    script_bans = {k: v for k, v in bans_data[guild_id].items() if v['type'] == 'script_ban'}
    
    if not script_bans:
        embed = discord.Embed(title="Script Ban List", description="No players are banned from the script.", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)
        return
    
    ban_list = []
    for username, data in script_bans.items():
        banned_at = datetime.fromtimestamp(data['timestamp']).strftime('%Y-%m-%d')
        ban_list.append(f"{username} - {data['reason']} (banned {banned_at})")
    
    chunks = [ban_list[i:i+10] for i in range(0, len(ban_list), 10)]
    
    for i, chunk in enumerate(chunks):
        embed = discord.Embed(title=f"Script Ban List (Page {i+1}/{len(chunks)})", description="\n".join(chunk), color=discord.Color.red())
        embed.set_footer(text=f"Total banned: {len(ban_list)} players")
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="scriptkick", description="Kick a player from the script")
async def script_kick(interaction: discord.Interaction, roblox_username: str, reason: str = "No reason provided"):
    if not is_allowed(interaction):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    guild_id = str(interaction.guild.id)
    
    if guild_id not in script_players or roblox_username not in script_players[guild_id]:
        embed = discord.Embed(title="Player Not Found", description=f"{roblox_username} is not currently running the script.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return
    
    del script_players[guild_id][roblox_username]
    
    embed = discord.Embed(title="Script Kick", description=f"{roblox_username} has been kicked from the script!", color=discord.Color.orange())
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Kicked By", value=str(interaction.user), inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="scriptstats", description="Get script usage statistics")
async def script_stats(interaction: discord.Interaction):
    if not is_allowed(interaction):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    guild_id = str(interaction.guild.id)
    
    total_players = len(script_players.get(guild_id, {}))
    total_bans = len([b for b in bans_data.get(guild_id, {}).values() if b['type'] == 'script_ban'])
    
    current_time = time.time()
    active = 0
    for data in script_players.get(guild_id, {}).values():
        if current_time - data['last_seen'] < 300:
            active += 1
    
    embed = discord.Embed(title="Script Statistics", color=discord.Color.blue())
    embed.add_field(name="Total Players", value=str(total_players), inline=True)
    embed.add_field(name="Active Players", value=str(active), inline=True)
    embed.add_field(name="Total Bans", value=str(total_bans), inline=True)
    embed.add_field(name="Server", value=interaction.guild.name, inline=False)
    embed.set_footer(text=f"Last updated | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="clear", description="Clear messages (Admin only)")
@commands.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int = 5):
    if not is_allowed(interaction):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        return
    
    if amount > 100:
        await interaction.response.send_message("You can only delete up to 100 messages at a time!")
        return
    
    deleted = await interaction.channel.purge(limit=amount + 1)
    await interaction.response.send_message(f"Deleted {len(deleted)-1} messages!", ephemeral=True)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"Command not found. Use `/help` to see all commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing argument: {error.param.name}")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(f"You don't have permission to use this command!")
    else:
        await ctx.send(f"An error occurred: {str(error)}")

bot.run(os.environ.get('TOKEN'))
