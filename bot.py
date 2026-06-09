import os
import discord
from discord.ext import commands
import sqlite3
import datetime
from dotenv import load_dotenv

# ================= LOAD TOKEN =================
load_dotenv()
TOKEN = os.getenv("TOKEN")

# ================= INTENTS =================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ================= DATABASE =================
db = sqlite3.connect("bot.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    xp INTEGER
)
""")
db.commit()

# ================= IDS =================
AUTO_ROLE_ID = 1499491748278309085

NL_ROLE_ID = 1499808774620319946
EN_ROLE_ID = 1499808997123952871

NL_CHANNEL_ID = 1499455488213913751
EN_CHANNEL_ID = 1499811887569829909

sent_welcome = set()

# ================= READY =================
@bot.event
async def on_ready():

    try:
        synced = await bot.tree.sync()
        print(f"✅ Slash synced: {len(synced)} commands")
    except Exception as e:
        print("Sync error:", e)

    activity = discord.Activity(
        type=discord.ActivityType.listening,
        name="R-Owen"
    )

    await bot.change_presence(
        status=discord.Status.online,
        activity=activity
    )

    print(f"🤖 {bot.user} is online!")

# ================= AUTO ROLE =================
@bot.event
async def on_member_join(member):

    if member.bot:
        return

    role = member.guild.get_role(AUTO_ROLE_ID)

    if role:
        await member.add_roles(role)

# ================= WELCOME SYSTEM =================
@bot.event
async def on_member_update(before, after):

    nl_role = discord.utils.get(after.guild.roles, id=NL_ROLE_ID)
    en_role = discord.utils.get(after.guild.roles, id=EN_ROLE_ID)

    nl_channel = after.guild.get_channel(NL_CHANNEL_ID)
    en_channel = after.guild.get_channel(EN_CHANNEL_ID)

    if nl_role in after.roles and nl_role not in before.roles:
        if after.id not in sent_welcome:
            await nl_channel.send(f"👋 Welkom {after.mention}! 🇳🇱")
            sent_welcome.add(after.id)

    if en_role in after.roles and en_role not in before.roles:
        if after.id not in sent_welcome:
            await en_channel.send(f"👋 Welcome {after.mention}! 🇬🇧")
            sent_welcome.add(after.id)

# ================= XP SYSTEM =================
@bot.event
async def on_message(message):

    if message.author.bot:
        return

    cursor.execute("SELECT xp FROM users WHERE user_id=?", (message.author.id,))
    data = cursor.fetchone()

    if data:
        xp = data[0] + 5
        cursor.execute("UPDATE users SET xp=? WHERE user_id=?", (xp, message.author.id))
    else:
        cursor.execute("INSERT INTO users VALUES (?, ?)", (message.author.id, 5))

    db.commit()

    await bot.process_commands(message)

# ================= EMBED =================
def make_embed(title, desc):
    return discord.Embed(
        title=title,
        description=desc,
        color=discord.Color.blue()
    )


def parse_duration(duration: str) -> int | None:
    duration = duration.strip().lower()
    if duration.isdigit():
        return int(duration)

    if len(duration) < 2:
        return None

    value = duration[:-1]
    unit = duration[-1]

    if not value.isdigit():
        return None

    value = int(value)

    if unit == "m":
        return value
    if unit == "h":
        return value * 60
    if unit == "d":
        return value * 1440

    return None

# ================= PREFIX COMMANDS =================
@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

@bot.command()
async def rank(ctx):

    cursor.execute("SELECT xp FROM users WHERE user_id=?", (ctx.author.id,))
    data = cursor.fetchone()

    xp = data[0] if data else 0

    await ctx.send(embed=make_embed("📊 Rank", f"{ctx.author.mention} → {xp} XP"))

@bot.command()
async def top(ctx):

    cursor.execute("SELECT user_id, xp FROM users ORDER BY xp DESC LIMIT 5")
    rows = cursor.fetchall()

    text = ""

    for i, r in enumerate(rows, start=1):
        user = await bot.fetch_user(r[0])
        text += f"{i}. {user.name} - {r[1]} XP\n"

    await ctx.send(embed=make_embed("🏆 Leaderboard", text))

@bot.command()
async def userinfo(ctx, member: discord.Member = None):

    member = member or ctx.author

    e = discord.Embed(title="👤 User Info")
    e.add_field(name="Naam", value=member.name)
    e.add_field(name="ID", value=member.id)

    await ctx.send(embed=e)

@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(title="📜 Commands", colour=discord.Color.blue())
    embed.add_field(name="General", value="!ping, !rank, !top, !userinfo", inline=False)
    embed.add_field(name="Moderation", value="!purge <amount>, !ban <member> [reason], !kick <member> [reason], !timeout <member> <minutes> [reason], !mute <member> <minutes> [reason]", inline=False)
    embed.add_field(name="Channel", value="!deletechannel [channel], !createvoice <name>, !deletevoice [channel]", inline=False)
    embed.add_field(name="Roles", value="!addrole <member> <role>, !removerole <member> <role>", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="purge")
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    if amount < 1 or amount > 100:
        await ctx.send("Please specify a number between 1 and 100.")
        return

    deleted = await ctx.channel.purge(limit=amount + 1)
    confirm = await ctx.send(f"🧹 Deleted {len(deleted) - 1} messages.")
    await confirm.delete(delay=5)

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason: str = None):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member.mention} has been banned. Reason: {reason or 'No reason provided.'}")

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason: str = None):
    await member.kick(reason=reason)
    await ctx.send(f"👢 {member.mention} has been kicked. Reason: {reason or 'No reason provided.'}")

@bot.command(name="timeout")
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, duration: str, *, reason: str = None):
    minutes = parse_duration(duration)
    if minutes is None or minutes < 1 or minutes > 1440:
        await ctx.send("Timeout must be between 1 and 1440 minutes, or use m/h/d suffixes.")
        return

    until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=minutes)
    await member.timeout(until, reason)
    await ctx.send(f"⏱️ {member.mention} has been timed out for {minutes} minutes. Reason: {reason or 'No reason provided.'}")

@bot.command(name="mute")
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, duration: str, *, reason: str = None):
    minutes = parse_duration(duration)
    if minutes is None or minutes < 1 or minutes > 1440:
        await ctx.send("Mute duration must be between 1 and 1440 minutes, or use m/h/d suffixes.")
        return

    until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=minutes)
    await member.timeout(until, reason)
    await ctx.send(f"🔇 {member.mention} has been muted for {minutes} minutes. Reason: {reason or 'No reason provided.'}")

@bot.command(name="addrole")
@commands.has_permissions(manage_roles=True)
async def add_role(ctx, member: discord.Member, *, role: discord.Role):
    await member.add_roles(role)
    await ctx.send(f"✅ Added role {role.name} to {member.mention}.")

@bot.command(name="removerole")
@commands.has_permissions(manage_roles=True)
async def remove_role(ctx, member: discord.Member, *, role: discord.Role):
    await member.remove_roles(role)
    await ctx.send(f"✅ Removed role {role.name} from {member.mention}.")

@bot.command(name="deletechannel")
@commands.has_permissions(manage_channels=True)
async def delete_channel(ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    await channel.delete(reason=f"Deleted by {ctx.author}")
    await ctx.send(f"🗑️ Channel {channel.mention} deleted.", delete_after=5)

@bot.command(name="createvoice")
@commands.has_permissions(manage_channels=True)
async def create_voice(ctx, *, name: str):
    guild = ctx.guild
    voice_channel = await guild.create_voice_channel(name)
    await ctx.send(f"✅ Voice channel created: {voice_channel.mention}")

@bot.command(name="deletevoice")
@commands.has_permissions(manage_channels=True)
async def delete_voice(ctx, channel: discord.VoiceChannel = None):
    channel = channel or ctx.author.voice.channel if ctx.author.voice else None
    if channel is None:
        await ctx.send("Please specify a voice channel or join one first.")
        return

    await channel.delete(reason=f"Deleted by {ctx.author}")
    await ctx.send(f"🗑️ Voice channel deleted: {channel.name}")

# ================= SLASH COMMANDS =================
@bot.tree.command(name="ping", description="Test bot")
async def ping_slash(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")

@bot.tree.command(name="rank", description="Check XP")
async def rank_slash(interaction: discord.Interaction):

    cursor.execute("SELECT xp FROM users WHERE user_id=?", (interaction.user.id,))
    data = cursor.fetchone()

    xp = data[0] if data else 0

    await interaction.response.send_message(
        embed=make_embed("📊 Rank", f"{interaction.user.mention} → {xp} XP")
    )

@bot.tree.command(name="top", description="Leaderboard")
async def top_slash(interaction: discord.Interaction):

    cursor.execute("SELECT user_id, xp FROM users ORDER BY xp DESC LIMIT 5")
    rows = cursor.fetchall()

    text = ""

    for i, r in enumerate(rows, start=1):
        user = await bot.fetch_user(r[0])
        text += f"{i}. {user.name} - {r[1]} XP\n"

    await interaction.response.send_message(embed=make_embed("🏆 Leaderboard", text))

@bot.tree.command(name="purge", description="Delete recent messages")
@discord.app_commands.describe(amount="Number of messages to delete")
async def purge_slash(interaction: discord.Interaction, amount: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You need Manage Messages permission.", ephemeral=True)
        return

    if amount < 1 or amount > 100:
        await interaction.response.send_message("Please specify a number between 1 and 100.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 Deleted {len(deleted)} messages.", ephemeral=True)

@bot.tree.command(name="deletechannel", description="Delete a text channel")
@discord.app_commands.describe(channel="Text channel to delete")
async def delete_channel_slash(interaction: discord.Interaction, channel: discord.TextChannel = None):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("You need Manage Channels permission.", ephemeral=True)
        return

    channel = channel or interaction.channel
    await channel.delete(reason=f"Deleted by {interaction.user}")
    await interaction.response.send_message(f"🗑️ Channel {channel.name} deleted.", ephemeral=True)

@bot.tree.command(name="createvoice", description="Create a new voice channel")
@discord.app_commands.describe(name="Voice channel name")
async def create_voice_slash(interaction: discord.Interaction, name: str):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("You need Manage Channels permission.", ephemeral=True)
        return

    voice_channel = await interaction.guild.create_voice_channel(name)
    await interaction.response.send_message(f"✅ Voice channel created: {voice_channel.mention}", ephemeral=True)

@bot.tree.command(name="deletevoice", description="Delete a voice channel")
@discord.app_commands.describe(channel="Voice channel to delete")
async def delete_voice_slash(interaction: discord.Interaction, channel: discord.VoiceChannel = None):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("You need Manage Channels permission.", ephemeral=True)
        return

    channel = channel or (interaction.user.voice.channel if interaction.user.voice else None)
    if channel is None:
        await interaction.response.send_message("Please provide a voice channel or join one first.", ephemeral=True)
        return

    await channel.delete(reason=f"Deleted by {interaction.user}")
    await interaction.response.send_message(f"🗑️ Voice channel deleted: {channel.name}", ephemeral=True)

@bot.tree.command(name="ban", description="Ban a member")
@discord.app_commands.describe(member="Member to ban", reason="Reason for the ban")
async def ban_slash(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("You need Ban Members permission.", ephemeral=True)
        return

    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 {member.mention} has been banned. Reason: {reason or 'No reason provided.'}", ephemeral=True)

@bot.tree.command(name="kick", description="Kick a member")
@discord.app_commands.describe(member="Member to kick", reason="Reason for the kick")
async def kick_slash(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("You need Kick Members permission.", ephemeral=True)
        return

    await member.kick(reason=reason)
    await interaction.response.send_message(f"👢 {member.mention} has been kicked. Reason: {reason or 'No reason provided.'}", ephemeral=True)

@bot.tree.command(name="timeout", description="Timeout a member")
@discord.app_commands.describe(member="Member to timeout", duration="Timeout duration in minutes or with m/h/d suffix", reason="Reason for the timeout")
async def timeout_slash(interaction: discord.Interaction, member: discord.Member, duration: str, reason: str = None):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("You need Moderate Members permission.", ephemeral=True)
        return

    minutes = parse_duration(duration)
    if minutes is None or minutes < 1 or minutes > 1440:
        await interaction.response.send_message("Timeout must be between 1 and 1440 minutes, or use m/h/d suffixes.", ephemeral=True)
        return

    until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=minutes)
    await member.timeout(until, reason)
    await interaction.response.send_message(f"⏱️ {member.mention} has been timed out for {minutes} minutes. Reason: {reason or 'No reason provided.'}", ephemeral=True)

@bot.tree.command(name="mute", description="Mute a member")
@discord.app_commands.describe(member="Member to mute", duration="Mute duration in minutes or with m/h/d suffix", reason="Reason for the mute")
async def mute_slash(interaction: discord.Interaction, member: discord.Member, duration: str, reason: str = None):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("You need Moderate Members permission.", ephemeral=True)
        return

    minutes = parse_duration(duration)
    if minutes is None or minutes < 1 or minutes > 1440:
        await interaction.response.send_message("Mute duration must be between 1 and 1440 minutes, or use m/h/d suffixes.", ephemeral=True)
        return

    until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=minutes)
    await member.timeout(until, reason)
    await interaction.response.send_message(f"🔇 {member.mention} has been muted for {minutes} minutes. Reason: {reason or 'No reason provided.'}", ephemeral=True)

@bot.tree.command(name="addrole", description="Add a role to a member")
@discord.app_commands.describe(member="Member to give the role", role="Role to add")
async def addrole_slash(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("You need Manage Roles permission.", ephemeral=True)
        return

    await member.add_roles(role)
    await interaction.response.send_message(f"✅ Added role {role.name} to {member.mention}.", ephemeral=True)

@bot.tree.command(name="removerole", description="Remove a role from a member")
@discord.app_commands.describe(member="Member to remove the role from", role="Role to remove")
async def removerole_slash(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("You need Manage Roles permission.", ephemeral=True)
        return

    await member.remove_roles(role)
    await interaction.response.send_message(f"✅ Removed role {role.name} from {member.mention}.", ephemeral=True)

# ================= START BOT =================
bot.run(os.getenv("TOKEN"))