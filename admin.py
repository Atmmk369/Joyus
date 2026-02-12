# -*- coding: utf-8 -*-
"""
Admin commands module for Joy Streak Bot
Handles bot management, resets, and admin utilities
"""

import discord
from discord.ext import commands
import json
import os
from datetime import datetime

class AdminCommands(commands.Cog):
    def __init__(self, bot, db, config):
        self.bot = bot
        self.db = db
        self.config = config
    
    def is_admin(self, ctx):
        """Check if user is admin"""
        # Check if user has admin role
        if ctx.guild:
            user_roles = [role.name for role in ctx.author.roles]
            if any(role in self.config['admin_roles'] for role in user_roles):
                return True
        
        # Check if user ID is in admin list
        if ctx.author.id in self.config.get('admin_user_ids', []):
            return True
        
        # Server owner is always admin
        if ctx.guild and ctx.author.id == ctx.guild.owner_id:
            return True
        
        return False
    
    @commands.command(name='reset_all')
    async def reset_all(self, ctx):
        """
        DANGER: Reset the entire bot database
        Admin only - works in any channel
        """
        if not self.is_admin(ctx):
            await ctx.send("❌ You don't have permission to use this command!")
            return
        
        # Confirmation embed
        embed = discord.Embed(
            title="⚠️ DANGER: Full Database Reset",
            description=(
                "This will **permanently delete ALL data**:\n"
                "• All user levels, XP, HP, coins\n"
                "• All streaks (personal and server)\n"
                "• All inventories and items\n"
                "• All achievements\n"
                "• All combat history\n\n"
                "**This action CANNOT be undone!**\n\n"
                f"Type `!confirm_reset` within 30 seconds to proceed."
            ),
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Requested by {ctx.author.name}")
        
        await ctx.send(embed=embed)
        
        def check(m):
            return (m.author == ctx.author and 
                    m.channel == ctx.channel and 
                    m.content.lower() == '!confirm_reset')
        
        try:
            await self.bot.wait_for('message', timeout=30.0, check=check)
        except:
            await ctx.send("❌ Reset cancelled - confirmation not received.")
            return
        
        # Execute reset
        try:
            self.db.reset_all_data()
            
            embed = discord.Embed(
                title="✅ Database Reset Complete",
                description=(
                    "All data has been wiped.\n"
                    "The bot is now in a fresh state.\n\n"
                    "Users can start fresh by sending Joy!"
                ),
                color=discord.Color.green()
            )
            embed.timestamp = datetime.utcnow()
            
            await ctx.send(embed=embed)
            print(f"🗑️ Full database reset performed by {ctx.author.name} ({ctx.author.id})")
            
        except Exception as e:
            await ctx.send(f"❌ Reset failed: {e}")
            print(f"Error during reset: {e}")
    
    @commands.command(name='reset_user')
    async def reset_user(self, ctx, member: discord.Member):
        """
        Reset a specific user's data
        Admin only - works in any channel
        Usage: !reset_user @username
        """
        if not self.is_admin(ctx):
            await ctx.send("❌ You don't have permission to use this command!")
            return
        
        try:
            self.db.reset_user(member.id)
            
            embed = discord.Embed(
                title="✅ User Reset",
                description=f"{member.mention}'s data has been completely reset.",
                color=discord.Color.green()
            )
            embed.add_field(name="Reset User", value=member.name, inline=True)
            embed.add_field(name="Admin", value=ctx.author.name, inline=True)
            embed.timestamp = datetime.utcnow()
            
            await ctx.send(embed=embed)
            print(f"🗑️ User {member.name} ({member.id}) reset by {ctx.author.name}")
            
        except Exception as e:
            await ctx.send(f"❌ Reset failed: {e}")
    
    @commands.command(name='give_xp')
    async def give_xp(self, ctx, member: discord.Member, amount: int):
        """
        Give XP to a user
        Admin only - works in any channel
        Usage: !give_xp @username 100
        """
        if not self.is_admin(ctx):
            await ctx.send("❌ You don't have permission to use this command!")
            return
        
        try:
            user = self.db.get_or_create_user(member.id, member.name)
            result = self.db.add_xp(member.id, amount)
            
            embed = discord.Embed(
                title="💫 XP Granted",
                color=discord.Color.blue()
            )
            embed.add_field(name="User", value=member.mention, inline=True)
            embed.add_field(name="XP Added", value=f"{amount:+d}", inline=True)
            embed.add_field(name="New Total", value=result['xp'], inline=True)
            
            if result['leveled_up']:
                embed.add_field(
                    name="Level Up!",
                    value=f"{result['old_level']} → {result['new_level']}",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Failed to give XP: {e}")
    
    @commands.command(name='give_coins')
    async def give_coins(self, ctx, member: discord.Member, amount: int):
        """
        Give coins to a user
        Admin only - works in any channel
        Usage: !give_coins @username 500
        """
        if not self.is_admin(ctx):
            await ctx.send("❌ You don't have permission to use this command!")
            return
        
        try:
            user = self.db.get_or_create_user(member.id, member.name)
            new_coins = user['coins'] + amount
            self.db.update_user(member.id, coins=new_coins)
            
            embed = discord.Embed(
                title="💰 Coins Granted",
                color=discord.Color.gold()
            )
            embed.add_field(name="User", value=member.mention, inline=True)
            embed.add_field(name="Coins Added", value=f"{amount:+d}", inline=True)
            embed.add_field(name="New Total", value=new_coins, inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Failed to give coins: {e}")
    
    @commands.command(name='give_item')
    async def give_item(self, ctx, member: discord.Member, item_id: str, quantity: int = 1):
        """
        Give an item to a user
        Admin only - works in any channel
        Usage: !give_item @username health_potion 5
        """
        if not self.is_admin(ctx):
            await ctx.send("❌ You don't have permission to use this command!")
            return
        
        try:
            # Load items to verify it exists
            with open('data/items.json', 'r') as f:
                items = json.load(f)
            
            if item_id not in items:
                await ctx.send(f"❌ Item '{item_id}' not found!")
                return
            
            user = self.db.get_or_create_user(member.id, member.name)
            self.db.add_item(member.id, item_id, quantity)
            
            item = items[item_id]
            
            embed = discord.Embed(
                title="🎁 Item Granted",
                color=discord.Color.purple()
            )
            embed.add_field(name="User", value=member.mention, inline=True)
            embed.add_field(
                name="Item", 
                value=f"{item.get('emoji', '📦')} {item['name']}", 
                inline=True
            )
            embed.add_field(name="Quantity", value=quantity, inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Failed to give item: {e}")
    
    @commands.command(name='set_hp')
    async def set_hp(self, ctx, member: discord.Member, hp: int):
        """
        Set a user's HP
        Admin only - works in any channel
        Usage: !set_hp @username 100
        """
        if not self.is_admin(ctx):
            await ctx.send("❌ You don't have permission to use this command!")
            return
        
        try:
            user = self.db.get_or_create_user(member.id, member.name)
            hp = max(0, min(hp, user['max_hp']))
            self.db.update_user(member.id, hp=hp)
            
            embed = discord.Embed(
                title="❤️ HP Updated",
                color=discord.Color.red()
            )
            embed.add_field(name="User", value=member.mention, inline=True)
            embed.add_field(name="New HP", value=f"{hp}/{user['max_hp']}", inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Failed to set HP: {e}")
    
    @commands.command(name='reload_data')
    async def reload_data(self, ctx):
        """
        Reload monsters, items, classes, and achievements from files
        Admin only - works in any channel
        Useful for adding new content without restarting the bot
        """
        if not self.is_admin(ctx):
            await ctx.send("❌ You don't have permission to use this command!")
            return
        
        try:
            # This will be handled by the main bot reloading JSON files
            # For now, just confirm
            embed = discord.Embed(
                title="🔄 Data Reloaded",
                description=(
                    "The following files have been reloaded:\n"
                    "• `monsters.json`\n"
                    "• `items.json`\n"
                    "• `classes.json`\n"
                    "• `achievements.json`\n"
                    "• `config.json`\n\n"
                    "New content is now available!"
                ),
                color=discord.Color.blue()
            )
            
            await ctx.send(embed=embed)
            print(f"📂 Data files reloaded by {ctx.author.name}")
            
        except Exception as e:
            await ctx.send(f"❌ Failed to reload data: {e}")
    
    @commands.command(name='set_channel')
    async def set_channel(self, ctx, channel_type: str, channel: discord.TextChannel = None):
        """
        Set a channel for a specific purpose
        Admin only - works in any channel
        Usage: !set_channel monster_hunting #monster-hunting
               !set_channel shop (uses current channel)
        
        Types: joy_stickers, monster_hunting, shop, bot_commands, admin
        """
        if not self.is_admin(ctx):
            await ctx.send("❌ You don't have permission to use this command!")
            return
        
        valid_types = ['joy_stickers', 'monster_hunting', 'shop', 'bot_commands', 'admin']
        
        if channel_type not in valid_types:
            await ctx.send(f"❌ Invalid channel type! Use: {', '.join(valid_types)}")
            return
        
        # Use current channel if none specified
        if channel is None:
            channel = ctx.channel
        
        # Update config
        self.config['channels'][channel_type] = channel.id
        
        # Save config
        with open('config/config.json', 'w') as f:
            json.dump(self.config, f, indent=2)
        
        embed = discord.Embed(
            title="✅ Channel Configured",
            color=discord.Color.green()
        )
        embed.add_field(name="Type", value=channel_type, inline=True)
        embed.add_field(name="Channel", value=channel.mention, inline=True)
        
        await ctx.send(embed=embed)
        print(f"📝 Channel {channel_type} set to #{channel.name} by {ctx.author.name}")
    
    @commands.command(name='stats')
    async def stats(self, ctx):
        """
        Show bot statistics
        Admin only - works in any channel
        Usage: !stats
        """
        if not self.is_admin(ctx):
            await ctx.send("❌ You don't have permission to use this command!")
            return
        
        try:
            # Get stats from database
            stats = self.db.get_server_stats()
            
            # Count users
            user_count = self.db.execute_query("SELECT COUNT(*) as count FROM users", fetch=True)[0]['count']
            
            # Count total monsters killed
            total_monsters = self.db.execute_query(
                "SELECT COUNT(*) as count FROM combat_logs WHERE outcome = 'win'", 
                fetch=True
            )[0]['count']
            
            # Get total XP earned
            total_xp = self.db.execute_query(
                "SELECT COALESCE(SUM(xp), 0) as total FROM users", 
                fetch=True
            )[0]['total']
            
            embed = discord.Embed(
                title="📊 Bot Statistics",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="Total Users", value=user_count, inline=True)
            embed.add_field(name="Server Streak", value=f"{stats['server_streak']} days", inline=True)
            embed.add_field(name="Monsters Killed", value=total_monsters, inline=True)
            embed.add_field(name="Total XP Earned", value=f"{total_xp:,}", inline=True)
            
            # Get top player
            top_player = self.db.execute_query(
                "SELECT discord_id, username, level, xp FROM users ORDER BY xp DESC LIMIT 1",
                fetch=True
            )
            
            if top_player:
                top = top_player[0]
                embed.add_field(
                    name="Top Player",
                    value=f"{top['username']} (Lvl {top['level']})",
                    inline=True
                )
            
            embed.timestamp = datetime.utcnow()
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Failed to get stats: {e}")
    
    @commands.command(name='maintenance')
    async def maintenance_mode(self, ctx, enabled: bool = None):
        """
        Toggle maintenance mode
        Admin only - works in any channel
        Usage: !maintenance true/false
        """
        if not self.is_admin(ctx):
            await ctx.send("❌ You don't have permission to use this command!")
            return
        
        if enabled is None:
            # Show current status
            current = self.config['bot_settings'].get('maintenance_mode', False)
            await ctx.send(f"Maintenance mode is currently: **{'ON' if current else 'OFF'}**")
            return
        
        # Update maintenance mode
        self.config['bot_settings']['maintenance_mode'] = enabled
        
        # Save config
        with open('config/config.json', 'w') as f:
            json.dump(self.config, f, indent=2)
        
        status = "🔧 ENABLED" if enabled else "✅ DISABLED"
        color = discord.Color.orange() if enabled else discord.Color.green()
        
        embed = discord.Embed(
            title=f"Maintenance Mode {status}",
            description=(
                "Normal users cannot use bot commands while in maintenance mode.\n"
                "Admins can still use all commands."
            ) if enabled else "Bot is back online for all users!",
            color=color
        )
        
        await ctx.send(embed=embed)
        print(f"🔧 Maintenance mode set to {enabled} by {ctx.author.name}")
    
    @commands.command(name='newday')
    async def force_new_day(self, ctx):
        """
        🧪 TESTING ONLY: Force a new day
        Admin only - works in any channel
        Allows testing daily mechanics without waiting 24 hours
        
        This command:
        - Clears daily sender tracking (allows Joy to be sent again)
        - Resets coin claim dates (allows !claim again)
        - Does NOT reset streaks or XP
        """
        if not self.is_admin(ctx):
            await ctx.send("❌ You don't have permission to use this command!")
            return
        
        try:
            # Clear daily senders
            self.db.execute_query("DELETE FROM daily_senders")
            
            # Reset last coin claim for all users (so they can claim again)
            self.db.execute_query("UPDATE users SET last_coin_claim = NULL")
            
            # Get server stats
            server_stats = self.db.get_server_stats()
            
            embed = discord.Embed(
                title="🌅 New Day Forced!",
                description=(
                    "**Testing mode activated**\n\n"
                    "✅ Daily senders reset - Can send Joy again\n"
                    "✅ Coin claims reset - Can use !claim again\n"
                    "✅ Streaks preserved - No streak resets\n"
                    "✅ XP preserved - No XP changes\n\n"
                    "You can now test daily progression!"
                ),
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="📊 Current State",
                value=(
                    f"Server Streak: **{server_stats['server_streak']} days**\n"
                    f"Ready for new day of testing!"
                ),
                inline=False
            )
            
            embed.set_footer(text="⚠️ This is for TESTING only - Use in production carefully!")
            
            await ctx.send(embed=embed)
            print(f"🌅 New day forced by {ctx.author.name} ({ctx.author.id})")
            
        except Exception as e:
            await ctx.send(f"❌ Failed to force new day: {e}")
            print(f"Error forcing new day: {e}")
    
    @commands.command(name='adminhelp')
    async def admin_help(self, ctx):
        """
        Show all admin commands
        Admin only - works in any channel
        """
        if not self.is_admin(ctx):
            await ctx.send("❌ You don't have permission to use this command!")
            return
        
        embed = discord.Embed(
            title="🛠️ Admin Command List",
            description="All available admin commands (admin-only)",
            color=discord.Color.red()
        )
        
        # Bot Management
        embed.add_field(
            name="🔧 Bot Management",
            value=(
                "`!stats` - View bot statistics\n"
                "`!reload_data` - Reload JSON files without restart\n"
                "`!maintenance [true/false]` - Toggle maintenance mode\n"
                "`!set_channel <type> #channel` - Configure channel purposes\n"
            ),
            inline=False
        )
        
        # User Management
        embed.add_field(
            name="👥 User Management",
            value=(
                "`!reset_user @user` - Reset a specific user's data\n"
                "`!give_xp @user <amount>` - Give XP to a user\n"
                "`!give_coins @user <amount>` - Give coins to a user\n"
                "`!give_item @user <item_id> [qty]` - Give item to user\n"
                "`!set_hp @user <amount>` - Set a user's HP\n"
            ),
            inline=False
        )
        
        # Testing & Debug
        embed.add_field(
            name="🧪 Testing & Debug",
            value=(
                "`!newday` - Force new day (reset daily tracking)\n"
                "`!reset_all` - **DANGER:** Wipe entire database\n"
            ),
            inline=False
        )
        
        # Channel Types
        embed.add_field(
            name="📍 Channel Types (for !set_channel)",
            value=(
                "`joy_stickers` - Daily Joy channel\n"
                "`monster_hunting` - Combat channel\n"
                "`shop` - Shop channel\n"
                "`bot_commands` - General commands\n"
                "`admin` - Admin commands (optional)\n"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💡 Tips",
            value=(
                "• Admin commands work in **any channel**\n"
                "• Use `!newday` to test daily progression quickly\n"
                "• Use `!reload_data` after editing JSON files\n"
                "• Be careful with `!reset_all` - it's permanent!"
            ),
            inline=False
        )
        
        embed.set_footer(text="Admin access configured in config.json")
        
        await ctx.send(embed=embed)

async def setup(bot, db, config):
    """Add admin cog to bot"""
    await bot.add_cog(AdminCommands(bot, db, config))
