# -*- coding: utf-8 -*-
"""
Joy Streak Bot v3.0
Discord bot for tracking Joy sticker streaks with RPG mechanics
"""

import discord
from discord.ext import commands
from discord.ui import Button, View
import json
import os
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from database import get_db
import admin

# ===== LOAD CONFIGURATION =====
with open('config/config.json', 'r') as f:
    CONFIG = json.load(f)

with open('data/monsters.json', 'r') as f:
    MONSTERS = json.load(f)

with open('data/items.json', 'r') as f:
    ITEMS = json.load(f)

with open('data/classes.json', 'r') as f:
    CLASSES = json.load(f)

with open('data/achievements.json', 'r') as f:
    ACHIEVEMENTS = json.load(f)

# ===== CONFIGURATION =====
TIMEZONE = ZoneInfo(CONFIG['timezone'])
CHANNELS = CONFIG['channels']
PENALTIES = CONFIG['penalties']
REWARDS = CONFIG['rewards']

# ===== BOT SETUP =====
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(
    command_prefix=CONFIG['bot_settings']['command_prefix'],
    intents=intents,
    help_command=None  # We'll use custom help
)

# ===== DATABASE =====
db = None

# ===== HELPER FUNCTIONS =====

def get_today_str():
    """Get today's date as string in configured timezone"""
    return datetime.now(TIMEZONE).strftime('%Y-%m-%d')

def get_yesterday_str():
    """Get yesterday's date as string"""
    yesterday = datetime.now(TIMEZONE) - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')

def get_today_date():
    """Get today's date object"""
    return datetime.now(TIMEZONE).date()

def check_channel(ctx, channel_type: str) -> bool:
    """Check if command is in correct channel"""
    # Admin commands work anywhere
    if ctx.command.cog_name == 'AdminCommands':
        return True
    
    # If channel not configured, allow anywhere
    if CHANNELS.get(channel_type) is None:
        return True
    
    # Check if in correct channel
    return ctx.channel.id == CHANNELS[channel_type]

async def wrong_channel_penalty(ctx, correct_channel_type: str):
    """Apply penalty for using command in wrong channel"""
    channel_id = CHANNELS.get(correct_channel_type)
    if channel_id:
        channel = bot.get_channel(channel_id)
        channel_mention = channel.mention if channel else f"the correct channel"
    else:
        channel_mention = "the correct channel"
    
    # Apply XP penalty
    user = db.get_or_create_user(ctx.author.id, ctx.author.name)
    db.add_xp(ctx.author.id, -PENALTIES['wrong_channel_xp_loss'])
    
    embed = discord.Embed(
        title="⚠️ Wrong Channel!",
        description=f"Please use {channel_mention} for this command.\n**-{PENALTIES['wrong_channel_xp_loss']} XP**",
        color=discord.Color.orange()
    )
    
    await ctx.send(embed=embed, delete_after=10)

def get_class_tier_name(user_class: str, level: int) -> dict:
    """Get class name and emoji for current level"""
    if not user_class or user_class == 'peasant' or level < 3:
        return {
            'name': 'Peasant',
            'emoji': '👤',
            'tier': 1
        }
    
    if user_class not in CLASSES:
        return {'name': 'Unknown', 'emoji': '❓', 'tier': 1}
    
    class_data = CLASSES[user_class]
    
    # Find appropriate tier
    tier_index = 0
    for i, tier in enumerate(class_data['tiers']):
        if level >= tier['level']:
            tier_index = i
    
    tier_info = class_data['tiers'][tier_index]
    
    return {
        'name': tier_info['name'],
        'emoji': tier_info['emoji'],
        'tier': tier_index + 1
    }

# ===== CLASS SELECTION VIEW =====
class ClassSelectionView(View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.user_id = user_id
        
        # Create buttons for each non-peasant class
        for class_key, class_info in CLASSES.items():
            if class_key == 'peasant':
                continue
            
            tier1_info = class_info['tiers'][0]
            button = Button(
                label=tier1_info['name'],
                emoji=tier1_info['emoji'],
                style=discord.ButtonStyle.primary,
                custom_id=class_key
            )
            button.callback = self.create_callback(class_key)
            self.add_item(button)
    
    def create_callback(self, class_key):
        async def callback(interaction: discord.Interaction):
            if str(interaction.user.id) != str(self.user_id):
                await interaction.response.send_message(
                    "This class selection is not for you!", 
                    ephemeral=True
                )
                return
            
            # Set user's class
            db.set_user_class(self.user_id, class_key)
            
            # Get updated user info
            user = db.get_user(self.user_id)
            class_info = get_class_tier_name(class_key, user['level'])
            
            embed = discord.Embed(
                title=f"✅ Class Selected: {class_info['name']}",
                description=CLASSES[class_key]['description'],
                color=discord.Color.green()
            )
            
            # Show tier progression
            tier_names = " → ".join([t['name'] for t in CLASSES[class_key]['tiers']])
            embed.add_field(
                name="Evolution Path",
                value=tier_names,
                inline=False
            )
            
            # Show passive ability
            if 'passive' in CLASSES[class_key]:
                passive = CLASSES[class_key]['passive']
                embed.add_field(
                    name="Passive Ability",
                    value=f"**{passive['name']}**: {passive['description']}",
                    inline=False
                )
            
            # Show HP update
            embed.add_field(
                name="❤️ Max HP Updated",
                value=f"{user['max_hp']} HP",
                inline=True
            )
            
            embed.set_footer(text="You can change your class anytime with !selectclass")
            
            await interaction.response.edit_message(embed=embed, view=None)
        
        return callback

# ===== BOT EVENTS =====

@bot.event
async def on_ready():
    global db
    
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot ID: {bot.user.id}')
    print(f'Timezone: {TIMEZONE}')
    
    # Initialize database
    db = get_db()
    
    # Load admin commands
    await admin.setup(bot, db, CONFIG)
    
    # Display configured channels
    print("\n📋 Configured Channels:")
    for channel_type, channel_id in CHANNELS.items():
        if channel_id:
            channel = bot.get_channel(channel_id)
            if channel:
                print(f"  {channel_type}: #{channel.name}")
            else:
                print(f"  {channel_type}: {channel_id} (not found)")
        else:
            print(f"  {channel_type}: Not configured")
    
    print("\n✅ Bot is ready!")
    print("=" * 50)

@bot.event
async def on_message(message):
    # Ignore bot messages
    if message.author.bot:
        return
    
    # Check maintenance mode
    if CONFIG['bot_settings'].get('maintenance_mode', False):
        # Check if user is admin
        if message.guild:
            user_roles = [role.name for role in message.author.roles]
            is_admin = any(role in CONFIG['admin_roles'] for role in user_roles)
            if not is_admin and message.author.id not in CONFIG.get('admin_user_ids', []):
                return
    
    # Check if message contains Joy sticker
    if message.stickers:
        for sticker in message.stickers:
            if sticker.name == "Joy":
                # Must be in joy_stickers channel
                if CHANNELS['joy_stickers'] and message.channel.id != CHANNELS['joy_stickers']:
                    # Wrong channel - apply penalty
                    channel = bot.get_channel(CHANNELS['joy_stickers'])
                    await message.channel.send(
                        f"⚠️ {message.author.mention} Please send Joy in {channel.mention}! **-{PENALTIES['wrong_channel_xp_loss']} XP**",
                        delete_after=10
                    )
                    db.add_xp(message.author.id, -PENALTIES['wrong_channel_xp_loss'])
                    return
                
                await handle_joy_sticker(message)
                break
    
    # Process commands
    await bot.process_commands(message)

# ===== JOY STICKER HANDLER =====

async def handle_joy_sticker(message):
    """Handle Joy sticker with database"""
    user_id = message.author.id
    today = get_today_date()
    
    # Get or create user
    user = db.get_or_create_user(user_id, message.author.name)
    
    # Check if already sent today
    if db.check_daily_sender(user_id, today):
        # User sent Joy twice today - break their streak
        old_streak = user['streak']
        db.update_user(user_id, streak=0)
        
        await message.add_reaction('💔')
        await message.channel.send(
            f"💔 **STREAK BROKEN!** 💔\n"
            f"{message.author.mention} sent Joy twice in one day!\n"
            f"Streak was: **{old_streak}** → Now: **0**\n"
            f"Better luck tomorrow! 😢"
        )
        return
    
    # Mark as sent today
    db.add_daily_sender(user_id, today)
    
    # Check if user missed yesterday (broke streak before today)
    yesterday = get_today_date() - timedelta(days=1)
    missed_yesterday = False
    
    if user['last_joy_sent']:
        last_sent = user['last_joy_sent']
        if last_sent != yesterday and last_sent != today:
            missed_yesterday = True
            old_streak = user['streak']
            
            # Reset streak and apply XP loss
            db.update_user(user_id, streak=0)
            result = db.add_xp(user_id, -PENALTIES['wrong_channel_xp_loss'])
            
            await message.channel.send(
                f"💔 {message.author.mention} broke their streak by missing a day!\n"
                f"Streak was: **{old_streak}** → Now: **0**\n"
                f"Lost **{PENALTIES['wrong_channel_xp_loss']} XP**\n"
                f"Starting fresh today! 🌟"
            )
    
    # Update last sent date
    db.update_user(user_id, last_joy_sent=today)
    
    # Increment streak
    new_streak = user['streak'] + 1
    db.update_user(user_id, streak=new_streak)
    
    # Calculate XP reward
    xp_reward = REWARDS['joy_base_xp']
    
    # Check for milestones
    is_milestone = new_streak in [7, 30, 100, 365]
    
    # Add XP
    old_level = user['level']
    result = db.add_xp(user_id, xp_reward)
    new_level = result['new_level']
    
    # Update server streak
    server_stats = db.get_server_stats()
    if server_stats['last_joy_sent'] != today:
        # First Joy of the day
        yesterday_date = get_today_date() - timedelta(days=1)
        
        if server_stats['last_joy_sent'] == yesterday_date:
            # Increment server streak
            db.update_server_stats(
                server_streak=server_stats['server_streak'] + 1,
                last_joy_sent=today
            )
        else:
            # Server streak broken
            if server_stats['server_streak'] > 0:
                await message.channel.send(
                    f"💔 **SERVER STREAK BROKEN!** 💔\n"
                    f"No one sent Joy yesterday!\n"
                    f"Server streak was: **{server_stats['server_streak']}** → Now: **0**\n"
                    f"Let's rebuild together! 💪"
                )
            db.update_server_stats(server_streak=1, last_joy_sent=today)
    
    # React to message
    await message.add_reaction('✅')
    
    # Build response
    response_parts = []
    
    # XP notification
    response_parts.append(f"**+{xp_reward} XP** earned!")
    
    # Level up
    if new_level > old_level:
        response_parts.append(
            f"\n\n🎉 **LEVEL UP!** 🎉\n"
            f"{message.author.mention} reached **Level {new_level}**! 🔥"
        )
        
        # Check for tier up
        old_class_info = get_class_tier_name(user['user_class'], old_level)
        new_class_info = get_class_tier_name(user['user_class'], new_level)
        
        if new_class_info['tier'] > old_class_info['tier']:
            response_parts.append(
                f"\n\n✨ **CLASS EVOLUTION!** ✨\n"
                f"{message.author.mention} evolved to **{new_class_info['name']}**! "
                f"(Tier {new_class_info['tier']})"
            )
        
        # Check if unlocked class selection
        if old_level < 3 and new_level >= 3:
            response_parts.append(
                f"\n\n🎭 **CLASS SELECTION UNLOCKED!** 🎭\n"
                f"Use `!selectclass` to choose your class!"
            )
    
    # Milestone
    if is_milestone:
        response_parts.append(
            f"\n\n🎊 **MILESTONE!** 🎊\n"
            f"{message.author.mention} reached a **{new_streak}-day streak!** 🔥"
        )
    
    # Send response
    if response_parts:
        await message.channel.send(''.join(response_parts))

# ===== PROFILE & STATS COMMANDS =====

@bot.command(name='profile')
async def profile(ctx, member: discord.Member = None):
    """View your or another user's profile"""
    # Check channel
    if not check_channel(ctx, 'bot_commands'):
        await wrong_channel_penalty(ctx, 'bot_commands')
        return
    
    target = member or ctx.author
    user = db.get_or_create_user(target.id, target.name)
    
    # Calculate XP progress
    current_xp = user['xp']
    current_level_xp = db.calculate_xp_for_level(user['level'])
    next_level_xp = db.calculate_xp_for_level(user['level'] + 1)
    xp_progress = current_xp - current_level_xp
    xp_needed = next_level_xp - current_level_xp
    
    # Progress bar
    progress_bar_length = 10
    filled = int((xp_progress / xp_needed) * progress_bar_length) if xp_needed > 0 else 0
    progress_bar = '█' * filled + '░' * (progress_bar_length - filled)
    
    # Get class info
    class_info = get_class_tier_name(user['user_class'], user['level'])
    
    # Create embed
    embed = discord.Embed(
        title=f"👤 {target.display_name}'s Profile",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    
    # Level & XP
    embed.add_field(
        name="⚡ Level & Experience",
        value=f"**Level:** {user['level']}\n**XP:** {xp_progress}/{xp_needed}\n{progress_bar}",
        inline=False
    )
    
    # HP
    hp_percent = (user['hp'] / user['max_hp']) * 100 if user['max_hp'] > 0 else 0
    hp_color = "🟢" if hp_percent > 66 else "🟡" if hp_percent > 33 else "🔴"
    
    embed.add_field(
        name=f"❤️ Health",
        value=f"{hp_color} **{user['hp']}/{user['max_hp']} HP**",
        inline=True
    )
    
    # Coins
    embed.add_field(
        name="💰 Coins",
        value=f"**{user['coins']}** coins",
        inline=True
    )
    
    # Streak
    embed.add_field(
        name="🔥 Streak",
        value=f"**{user['streak']}** days",
        inline=True
    )
    
    # Class
    if user['level'] < 3:
        embed.add_field(
            name=f"{class_info['emoji']} Class",
            value=f"**{class_info['name']}**\n*Reach Level 3 to choose a class!*",
            inline=False
        )
    else:
        embed.add_field(
            name=f"{class_info['emoji']} Class - {class_info['name']}",
            value=f"**Tier {class_info['tier']}/3**",
            inline=False
        )
    
    # Depth (for monster hunting)
    if user['depth'] > 0:
        embed.add_field(
            name="🌲 Forest Depth",
            value=f"**{user['depth']}** (Deeper = Harder monsters)",
            inline=True
        )
    
    await ctx.send(embed=embed)

@bot.command(name='selectclass')
async def select_class(ctx):
    """Choose or change your class"""
    # Check channel
    if not check_channel(ctx, 'bot_commands'):
        await wrong_channel_penalty(ctx, 'bot_commands')
        return
    
    user = db.get_or_create_user(ctx.author.id, ctx.author.name)
    
    # Check level requirement
    if user['level'] < 3:
        xp_needed = db.calculate_xp_for_level(3) - user['xp']
        
        embed = discord.Embed(
            title="🔒 Class Selection Locked",
            description=(
                f"You must reach **Level 3** to choose a class!\n\n"
                f"Current Level: **{user['level']}**\n"
                f"XP Needed: **{xp_needed}** more XP"
            ),
            color=discord.Color.red()
        )
        embed.add_field(
            name="👤 Current Status",
            value="**Peasant** - Keep sending Joy to unlock classes!",
            inline=False
        )
        
        await ctx.send(embed=embed)
        return
    
    # Show class selection
    embed = discord.Embed(
        title="🎭 Choose Your Class",
        description="Select a class to gain unique bonuses! Classes evolve as you level up.\n",
        color=discord.Color.purple()
    )
    
    for class_key, class_info in CLASSES.items():
        if class_key == 'peasant':
            continue
        
        tier_names = " → ".join([t['name'] for t in class_info['tiers']])
        
        # Get passive description
        passive_desc = ""
        if 'passive' in class_info:
            passive = class_info['passive']
            passive_desc = f"\n**{passive['name']}:** {passive['description']}"
        
        embed.add_field(
            name=f"{class_info['tiers'][0]['emoji']} {class_info['tiers'][0]['name']}",
            value=f"{class_info['description']}{passive_desc}\n`{tier_names}`",
            inline=False
        )
    
    # Show current class if any
    if user['user_class'] and user['user_class'] != 'peasant':
        current_info = get_class_tier_name(user['user_class'], user['level'])
        embed.set_footer(text=f"Current: {current_info['name']} (Tier {current_info['tier']})")
    
    view = ClassSelectionView(ctx.author.id)
    await ctx.send(embed=embed, view=view)

@bot.command(name='leaderboard')
async def leaderboard(ctx, sort_by: str = 'level'):
    """View leaderboard (sort by: level, xp, streak, coins)"""
    # Check channel
    if not check_channel(ctx, 'bot_commands'):
        await wrong_channel_penalty(ctx, 'bot_commands')
        return
    
    sort_by = sort_by.lower()
    
    valid_sorts = ['level', 'xp', 'streak', 'coins']
    if sort_by not in valid_sorts:
        await ctx.send(f"❌ Invalid sort! Use: {', '.join(valid_sorts)}")
        return
    
    # Get top 10 users
    query = f"SELECT * FROM users ORDER BY {sort_by} DESC LIMIT 10"
    users = db.execute_query(query, fetch=True)
    
    if not users:
        await ctx.send("No users yet! Start sending Joy! 😊")
        return
    
    # Build embed
    title_map = {
        'level': '🏆 Leaderboard - By Level',
        'xp': '⚡ Leaderboard - By XP',
        'streak': '🔥 Leaderboard - By Streak',
        'coins': '💰 Leaderboard - By Coins'
    }
    
    embed = discord.Embed(
        title=title_map[sort_by],
        color=discord.Color.gold()
    )
    
    for i, user_data in enumerate(users, 1):
        try:
            user = await bot.fetch_user(user_data['discord_id'])
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            
            # Get class info
            class_info = get_class_tier_name(user_data['user_class'], user_data['level'])
            
            embed.add_field(
                name=f"{medal} {user.display_name}",
                value=(
                    f"{class_info['emoji']} Lvl {user_data['level']} | "
                    f"💰 {user_data['coins']} | "
                    f"🔥 {user_data['streak']} | "
                    f"⚡ {user_data['xp']} XP"
                ),
                inline=False
            )
        except:
            continue
    
    # Server streak
    server_stats = db.get_server_stats()
    embed.add_field(
        name="🌟 Server Streak",
        value=f"{server_stats['server_streak']} days",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name='classes')
async def list_classes(ctx):
    """View all available classes"""
    # Check channel
    if not check_channel(ctx, 'bot_commands'):
        await wrong_channel_penalty(ctx, 'bot_commands')
        return
    
    embed = discord.Embed(
        title="🎭 Available Classes",
        description="Each class evolves through 3 tiers!\n*Unlock at Level 3*\n",
        color=discord.Color.purple()
    )
    
    for class_key, class_info in CLASSES.items():
        if class_key == 'peasant':
            continue
        
        # Build tier progression
        tiers = " → ".join([f"{t['emoji']} {t['name']}" for t in class_info['tiers']])
        
        # HP formula
        hp_formula = class_info['hp_formula']
        hp_desc = f"HP: {hp_formula['base']} + {hp_formula['per_level']}/level"
        
        # Passive
        passive_desc = ""
        if 'passive' in class_info:
            passive = class_info['passive']
            passive_desc = f"\n**{passive['name']}:** {passive['description']}"
        
        embed.add_field(
            name=f"{class_info['tiers'][0]['emoji']} {class_info['name']}",
            value=f"{class_info['description']}{passive_desc}\n*{hp_desc}*\n`{tiers}`",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='help')
async def help_command(ctx):
    """Show all available commands"""
    embed = discord.Embed(
        title="📖 Command List",
        description="All available bot commands",
        color=discord.Color.blue()
    )
    
    # Profile & Stats
    embed.add_field(
        name="👤 Profile & Stats",
        value=(
            "`!profile [@user]` - View your or someone's profile\n"
            "`!leaderboard [level|xp|streak|coins]` - View rankings\n"
            "`!classes` - View all available classes\n"
        ),
        inline=False
    )
    
    # Progression
    embed.add_field(
        name="⚡ Progression",
        value=(
            "`!selectclass` - Choose or change your class (Level 3+)\n"
            "`!claim` - Claim your daily coins\n"
        ),
        inline=False
    )
    
    # Information
    embed.add_field(
        name="ℹ️ Information",
        value=(
            "`!joyhelp` - Detailed help and how the bot works\n"
            "`!help` - This command list\n"
        ),
        inline=False
    )
    
    # Check if user is admin to show admin commands
    is_admin = False
    if ctx.guild:
        user_roles = [role.name for role in ctx.author.roles]
        is_admin = any(role in CONFIG['admin_roles'] for role in user_roles)
        if not is_admin:
            is_admin = ctx.author.id in CONFIG.get('admin_user_ids', [])
        if not is_admin:
            is_admin = ctx.author.id == ctx.guild.owner_id
    
    if is_admin:
        embed.add_field(
            name="🛠️ Admin",
            value="`!adminhelp` - View admin commands",
            inline=False
        )
    
    embed.set_footer(text="Use !joyhelp for detailed information about how the bot works")
    
    await ctx.send(embed=embed)

@bot.command(name='joyhelp')
async def joy_help(ctx):
    """Show help information"""
    embed = discord.Embed(
        title="📋 Joy Streak Bot Help",
        description="Track your Joy streaks, level up, and prepare for monster hunting!",
        color=discord.Color.green()
    )
    
    embed.add_field(
        name="🎯 How it Works",
        value=(
            "• Send 'Joy' sticker once per day to build your streak\n"
            "• Earn XP and level up!\n"
            "• Reach Level 3 to choose your class\n"
            "• Classes evolve at levels 16 and 36\n"
            "• **Send Joy twice?** Streak resets to 0\n"
            "• **Miss a day?** Lose XP and streak resets\n"
            "• Day resets at midnight Eastern Time"
        ),
        inline=False
    )
    
    embed.add_field(
        name="📜 Commands",
        value=(
            "`!profile [@user]` - View profile\n"
            "`!selectclass` - Choose your class (Level 3+)\n"
            "`!classes` - View all classes\n"
            "`!leaderboard [level|xp|streak|coins]` - Rankings\n"
            "`!claim` - Claim daily coins\n"
            "`!joyhelp` - This help message"
        ),
        inline=False
    )
    
    # Add admin commands section if user is admin
    if ctx.guild:
        user_roles = [role.name for role in ctx.author.roles]
        is_admin = any(role in CONFIG['admin_roles'] for role in user_roles)
        if is_admin or ctx.author.id in CONFIG.get('admin_user_ids', []):
            embed.add_field(
                name="🛠️ Admin Commands",
                value=(
                    "`!newday` - Force new day (testing)\n"
                    "`!give_xp @user <amount>` - Give XP\n"
                    "`!reset_all` - Wipe database\n"
                    "`!stats` - View statistics"
                ),
                inline=False
            )
    
    embed.add_field(
        name="⚡ Leveling",
        value=(
            f"• Earn {REWARDS['joy_base_xp']} XP per Joy sent\n"
            "• Missing a day loses XP\n"
            "• Level up to unlock classes and abilities\n"
            "• Collect coins daily (1 coin per level)"
        ),
        inline=False
    )
    
    embed.add_field(
        name="📍 Channels",
        value=(
            "Use commands in the right channels:\n"
            "• Joy stickers: <#" + str(CHANNELS['joy_stickers']) + ">\n"
            "• Commands: <#" + str(CHANNELS['bot_commands']) + ">\n"
            "• Shop: <#" + str(CHANNELS['shop']) + "> (coming soon)\n"
            "• Hunting: <#" + str(CHANNELS['monster_hunting']) + "> (coming soon)"
        ),
        inline=False
    )
    
    embed.set_footer(text="More features coming soon! 🎮")
    
    await ctx.send(embed=embed)

# ===== COIN COLLECTION =====

@bot.command(name='claim')
async def claim_coins(ctx):
    """Claim your daily coins"""
    # Check channel
    if not check_channel(ctx, 'bot_commands'):
        await wrong_channel_penalty(ctx, 'bot_commands')
        return
    
    user = db.get_or_create_user(ctx.author.id, ctx.author.name)
    today = get_today_date()
    
    # Check if already claimed today
    if user['last_coin_claim'] == today:
        next_claim = datetime.now(TIMEZONE).replace(hour=0, minute=0, second=0) + timedelta(days=1)
        hours_left = (next_claim - datetime.now(TIMEZONE)).total_seconds() / 3600
        
        await ctx.send(
            f"⏰ You already claimed coins today!\n"
            f"Come back in **{hours_left:.1f} hours**."
        )
        return
    
    # Calculate coin reward
    coins_earned = user['level'] * REWARDS['daily_coins_per_level']
    
    # Update user
    new_coins = user['coins'] + coins_earned
    db.update_user(ctx.author.id, coins=new_coins, last_coin_claim=today)
    
    embed = discord.Embed(
        title="💰 Daily Coins Claimed!",
        description=f"You earned **{coins_earned} coins**!",
        color=discord.Color.gold()
    )
    embed.add_field(name="Total Coins", value=f"**{new_coins}** coins", inline=True)
    embed.add_field(
        name="Next Claim",
        value="Come back tomorrow!",
        inline=True
    )
    embed.set_footer(text=f"Earn more coins by leveling up! (Currently {REWARDS['daily_coins_per_level']} coin/level)")
    
    await ctx.send(embed=embed)

# ===== RUN BOT =====

if __name__ == '__main__':
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    
    if not TOKEN:
        print("❌ ERROR: DISCORD_BOT_TOKEN not found in environment variables!")
        print("Create a .env file with: DISCORD_BOT_TOKEN=your_token_here")
        exit(1)
    
    if not os.getenv('DATABASE_URL'):
        print("❌ ERROR: DATABASE_URL not found in environment variables!")
        print("Make sure PostgreSQL is added to your Railway project")
        exit(1)
    
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ Bot failed to start: {e}")
