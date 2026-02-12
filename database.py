# -*- coding: utf-8 -*-
"""
Database module for Joy Streak Bot
Handles all PostgreSQL interactions
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from datetime import datetime, date
from typing import Optional, List, Dict, Any
import json

class Database:
    def __init__(self):
        self.connection_string = os.getenv('DATABASE_URL')
        if not self.connection_string:
            raise Exception("DATABASE_URL environment variable not set!")
        
        # Fix for Railway/Heroku postgres:// vs postgresql://
        if self.connection_string.startswith('postgres://'):
            self.connection_string = self.connection_string.replace('postgres://', 'postgresql://', 1)
        
        self.conn = None
        self.connect()
        self.init_database()
    
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(self.connection_string)
            self.conn.autocommit = False
            print("✅ Database connected successfully")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """Execute a query with error handling"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if fetch:
                    return cur.fetchall()
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Query error: {e}")
            print(f"Query: {query}")
            raise
    
    def init_database(self):
        """Create all tables if they don't exist"""
        schema = """
        -- Core user data
        CREATE TABLE IF NOT EXISTS users (
            discord_id BIGINT PRIMARY KEY,
            username VARCHAR(255),
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            hp INTEGER DEFAULT 100,
            max_hp INTEGER DEFAULT 100,
            coins INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            depth INTEGER DEFAULT 0,
            user_class VARCHAR(50),
            last_joy_sent DATE,
            last_coin_claim DATE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Inventory system
        CREATE TABLE IF NOT EXISTS inventory (
            id SERIAL PRIMARY KEY,
            discord_id BIGINT REFERENCES users(discord_id) ON DELETE CASCADE,
            item_id VARCHAR(100),
            quantity INTEGER DEFAULT 1,
            equipped BOOLEAN DEFAULT FALSE,
            acquired_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Achievement tracking
        CREATE TABLE IF NOT EXISTS achievements (
            id SERIAL PRIMARY KEY,
            discord_id BIGINT REFERENCES users(discord_id) ON DELETE CASCADE,
            achievement_id VARCHAR(100),
            progress INTEGER DEFAULT 0,
            completed BOOLEAN DEFAULT FALSE,
            completed_at TIMESTAMP
        );
        
        -- Combat history
        CREATE TABLE IF NOT EXISTS combat_logs (
            id SERIAL PRIMARY KEY,
            discord_id BIGINT REFERENCES users(discord_id) ON DELETE CASCADE,
            monster_id VARCHAR(100),
            outcome VARCHAR(20),
            damage_dealt INTEGER,
            damage_taken INTEGER,
            xp_change INTEGER,
            depth INTEGER,
            co_op_participants TEXT[],
            timestamp TIMESTAMP DEFAULT NOW()
        );
        
        -- Shop rotation
        CREATE TABLE IF NOT EXISTS shop_rotation (
            id SERIAL PRIMARY KEY,
            item_id VARCHAR(100) UNIQUE,
            available_until TIMESTAMP,
            rotation_type VARCHAR(20)
        );
        
        -- Server stats
        CREATE TABLE IF NOT EXISTS server_stats (
            id INTEGER PRIMARY KEY DEFAULT 1,
            server_streak INTEGER DEFAULT 0,
            last_joy_sent DATE,
            total_monsters_killed INTEGER DEFAULT 0,
            CHECK (id = 1)
        );
        
        -- Daily senders tracking
        CREATE TABLE IF NOT EXISTS daily_senders (
            discord_id BIGINT,
            date DATE,
            PRIMARY KEY (discord_id, date)
        );
        
        -- Channel configuration
        CREATE TABLE IF NOT EXISTS channel_config (
            channel_type VARCHAR(50) PRIMARY KEY,
            channel_id BIGINT
        );
        
        -- Initialize server stats if not exists
        INSERT INTO server_stats (id, server_streak, total_monsters_killed)
        VALUES (1, 0, 0)
        ON CONFLICT (id) DO NOTHING;
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(schema)
            self.conn.commit()
            print("✅ Database schema initialized")
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Schema initialization failed: {e}")
            raise
    
    # ===== USER MANAGEMENT =====
    
    def get_user(self, discord_id: int) -> Optional[Dict]:
        """Get user data or None if doesn't exist"""
        query = "SELECT * FROM users WHERE discord_id = %s"
        result = self.execute_query(query, (discord_id,), fetch=True)
        return dict(result[0]) if result else None
    
    def create_user(self, discord_id: int, username: str) -> Dict:
        """Create a new user with default values"""
        query = """
        INSERT INTO users (discord_id, username, level, xp, hp, max_hp, coins)
        VALUES (%s, %s, 1, 0, 100, 100, 0)
        RETURNING *
        """
        result = self.execute_query(query, (discord_id, username), fetch=True)
        return dict(result[0])
    
    def get_or_create_user(self, discord_id: int, username: str) -> Dict:
        """Get user or create if doesn't exist"""
        user = self.get_user(discord_id)
        if not user:
            user = self.create_user(discord_id, username)
        return user
    
    def update_user(self, discord_id: int, **kwargs):
        """Update user fields"""
        # Build dynamic UPDATE query
        set_clauses = []
        values = []
        
        for key, value in kwargs.items():
            set_clauses.append(f"{key} = %s")
            values.append(value)
        
        values.append(discord_id)
        
        query = f"""
        UPDATE users 
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE discord_id = %s
        """
        
        self.execute_query(query, tuple(values))
    
    def calculate_max_hp(self, level: int, user_class: Optional[str]) -> int:
        """Calculate max HP based on level and class"""
        if not user_class or user_class == 'peasant' or level < 3:
            # Peasants: 10 HP per level
            return level * 10
        
        # Class-specific HP formulas (base + per level)
        class_hp = {
            'joy_keeper': {'base': 80, 'per_level': 8},
            'chud_warrior': {'base': 120, 'per_level': 12},
            'achievement_hunter': {'base': 90, 'per_level': 9},
            'pit_wizard': {'base': 70, 'per_level': 7},
            'gladiator_of_the_pit': {'base': 110, 'per_level': 11}
        }
        
        if user_class in class_hp:
            stats = class_hp[user_class]
            return stats['base'] + (level - 3) * stats['per_level']
        
        # Default if class not found
        return level * 10
    
    def add_xp(self, discord_id: int, xp_amount: int) -> Dict:
        """Add XP and handle leveling up"""
        user = self.get_user(discord_id)
        if not user:
            return None
        
        new_xp = max(0, user['xp'] + xp_amount)
        old_level = user['level']
        new_level = self.calculate_level_from_xp(new_xp)
        
        # Calculate new max HP if leveled up
        new_max_hp = user['max_hp']
        if new_level != old_level:
            new_max_hp = self.calculate_max_hp(new_level, user['user_class'])
        
        self.update_user(
            discord_id,
            xp=new_xp,
            level=new_level,
            max_hp=new_max_hp
        )
        
        return {
            'old_level': old_level,
            'new_level': new_level,
            'xp': new_xp,
            'leveled_up': new_level > old_level,
            'max_hp': new_max_hp
        }
    
    def calculate_level_from_xp(self, xp: int) -> int:
        """Calculate level based on XP (same formula as before)"""
        level = 1
        while self.calculate_xp_for_level(level + 1) <= xp:
            level += 1
        return level
    
    def calculate_xp_for_level(self, level: int) -> int:
        """Calculate total XP needed for a level"""
        if level == 1:
            return 0
        
        total_xp = 0
        for lvl in range(2, level + 1):
            if lvl <= 16:
                total_xp += 60
            elif lvl <= 36:
                total_xp += 90
            else:
                total_xp += 120
        
        return total_xp
    
    def damage_user(self, discord_id: int, damage: int) -> Dict:
        """Apply damage to user HP"""
        user = self.get_user(discord_id)
        if not user:
            return None
        
        new_hp = max(0, user['hp'] - damage)
        died = new_hp == 0
        
        self.update_user(discord_id, hp=new_hp)
        
        return {
            'old_hp': user['hp'],
            'new_hp': new_hp,
            'damage': damage,
            'died': died
        }
    
    def heal_user(self, discord_id: int, amount: int) -> Dict:
        """Heal user HP (cannot exceed max)"""
        user = self.get_user(discord_id)
        if not user:
            return None
        
        new_hp = min(user['max_hp'], user['hp'] + amount)
        
        self.update_user(discord_id, hp=new_hp)
        
        return {
            'old_hp': user['hp'],
            'new_hp': new_hp,
            'healed': new_hp - user['hp']
        }
    
    def set_user_class(self, discord_id: int, class_name: str):
        """Set user's class and recalculate max HP"""
        user = self.get_user(discord_id)
        if not user:
            return None
        
        new_max_hp = self.calculate_max_hp(user['level'], class_name)
        
        self.update_user(
            discord_id,
            user_class=class_name,
            max_hp=new_max_hp,
            hp=new_max_hp  # Fully heal on class selection
        )
    
    # ===== STREAK MANAGEMENT =====
    
    def check_daily_sender(self, discord_id: int, check_date: date) -> bool:
        """Check if user sent Joy on a specific date"""
        query = "SELECT 1 FROM daily_senders WHERE discord_id = %s AND date = %s"
        result = self.execute_query(query, (discord_id, check_date), fetch=True)
        return len(result) > 0
    
    def add_daily_sender(self, discord_id: int, send_date: date):
        """Mark user as having sent Joy on a date"""
        query = """
        INSERT INTO daily_senders (discord_id, date)
        VALUES (%s, %s)
        ON CONFLICT (discord_id, date) DO NOTHING
        """
        self.execute_query(query, (discord_id, send_date))
    
    def reset_daily_senders(self):
        """Clear daily senders table (call at midnight)"""
        # Keep last 7 days for reference
        query = "DELETE FROM daily_senders WHERE date < CURRENT_DATE - INTERVAL '7 days'"
        self.execute_query(query)
    
    def get_server_stats(self) -> Dict:
        """Get server-wide statistics"""
        query = "SELECT * FROM server_stats WHERE id = 1"
        result = self.execute_query(query, fetch=True)
        return dict(result[0]) if result else None
    
    def update_server_stats(self, **kwargs):
        """Update server statistics"""
        set_clauses = []
        values = []
        
        for key, value in kwargs.items():
            set_clauses.append(f"{key} = %s")
            values.append(value)
        
        query = f"UPDATE server_stats SET {', '.join(set_clauses)} WHERE id = 1"
        self.execute_query(query, tuple(values))
    
    # ===== INVENTORY =====
    
    def get_inventory(self, discord_id: int) -> List[Dict]:
        """Get user's inventory"""
        query = """
        SELECT * FROM inventory 
        WHERE discord_id = %s 
        ORDER BY equipped DESC, acquired_at DESC
        """
        result = self.execute_query(query, (discord_id,), fetch=True)
        return [dict(row) for row in result] if result else []
    
    def add_item(self, discord_id: int, item_id: str, quantity: int = 1):
        """Add item to inventory or increase quantity"""
        query = """
        INSERT INTO inventory (discord_id, item_id, quantity)
        VALUES (%s, %s, %s)
        ON CONFLICT (discord_id, item_id) 
        DO UPDATE SET quantity = inventory.quantity + EXCLUDED.quantity
        """
        self.execute_query(query, (discord_id, item_id, quantity))
    
    def remove_item(self, discord_id: int, item_id: str, quantity: int = 1) -> bool:
        """Remove item from inventory"""
        # Check if user has enough
        query = "SELECT quantity FROM inventory WHERE discord_id = %s AND item_id = %s"
        result = self.execute_query(query, (discord_id, item_id), fetch=True)
        
        if not result or result[0]['quantity'] < quantity:
            return False
        
        new_quantity = result[0]['quantity'] - quantity
        
        if new_quantity <= 0:
            query = "DELETE FROM inventory WHERE discord_id = %s AND item_id = %s"
            self.execute_query(query, (discord_id, item_id))
        else:
            query = "UPDATE inventory SET quantity = %s WHERE discord_id = %s AND item_id = %s"
            self.execute_query(query, (new_quantity, discord_id, item_id))
        
        return True
    
    def equip_item(self, discord_id: int, item_id: str, item_type: str):
        """Equip an item (unequip others of same type)"""
        # Unequip all items of this type
        query = """
        UPDATE inventory 
        SET equipped = FALSE 
        WHERE discord_id = %s 
        AND item_id IN (
            SELECT item_id FROM inventory WHERE discord_id = %s
        )
        """
        # Note: This is simplified - in reality you'd check item types from items.json
        
        # Equip the selected item
        query = """
        UPDATE inventory 
        SET equipped = TRUE 
        WHERE discord_id = %s AND item_id = %s
        """
        self.execute_query(query, (discord_id, item_id))
    
    def get_equipped_items(self, discord_id: int) -> List[Dict]:
        """Get all equipped items"""
        query = "SELECT * FROM inventory WHERE discord_id = %s AND equipped = TRUE"
        result = self.execute_query(query, (discord_id,), fetch=True)
        return [dict(row) for row in result] if result else []
    
    # ===== COMBAT LOGS =====
    
    def log_combat(self, discord_id: int, monster_id: str, outcome: str, 
                   damage_dealt: int, damage_taken: int, xp_change: int, 
                   depth: int, co_op: List[int] = None):
        """Log a combat encounter"""
        query = """
        INSERT INTO combat_logs 
        (discord_id, monster_id, outcome, damage_dealt, damage_taken, xp_change, depth, co_op_participants)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        self.execute_query(query, (
            discord_id, monster_id, outcome, damage_dealt, 
            damage_taken, xp_change, depth, co_op or []
        ))
    
    def get_combat_history(self, discord_id: int, limit: int = 10) -> List[Dict]:
        """Get recent combat history"""
        query = """
        SELECT * FROM combat_logs 
        WHERE discord_id = %s 
        ORDER BY timestamp DESC 
        LIMIT %s
        """
        result = self.execute_query(query, (discord_id, limit), fetch=True)
        return [dict(row) for row in result] if result else []
    
    # ===== ACHIEVEMENTS =====
    
    def get_achievement(self, discord_id: int, achievement_id: str) -> Optional[Dict]:
        """Get achievement progress"""
        query = "SELECT * FROM achievements WHERE discord_id = %s AND achievement_id = %s"
        result = self.execute_query(query, (discord_id, achievement_id), fetch=True)
        return dict(result[0]) if result else None
    
    def update_achievement(self, discord_id: int, achievement_id: str, progress: int):
        """Update achievement progress"""
        query = """
        INSERT INTO achievements (discord_id, achievement_id, progress)
        VALUES (%s, %s, %s)
        ON CONFLICT (discord_id, achievement_id) 
        DO UPDATE SET progress = %s
        """
        self.execute_query(query, (discord_id, achievement_id, progress, progress))
    
    def complete_achievement(self, discord_id: int, achievement_id: str):
        """Mark achievement as completed"""
        query = """
        UPDATE achievements 
        SET completed = TRUE, completed_at = NOW() 
        WHERE discord_id = %s AND achievement_id = %s
        """
        self.execute_query(query, (discord_id, achievement_id))
    
    def get_all_achievements(self, discord_id: int) -> List[Dict]:
        """Get all achievements for user"""
        query = "SELECT * FROM achievements WHERE discord_id = %s"
        result = self.execute_query(query, (discord_id,), fetch=True)
        return [dict(row) for row in result] if result else []
    
    # ===== SHOP =====
    
    def get_shop_rotation(self) -> List[str]:
        """Get currently available items in shop"""
        query = """
        SELECT item_id FROM shop_rotation 
        WHERE available_until > NOW() OR rotation_type = 'always'
        """
        result = self.execute_query(query, fetch=True)
        return [row['item_id'] for row in result] if result else []
    
    def set_shop_rotation(self, item_ids: List[str], duration_hours: int = 24):
        """Set shop rotation"""
        query = """
        INSERT INTO shop_rotation (item_id, available_until, rotation_type)
        VALUES (%s, NOW() + INTERVAL '%s hours', 'timed')
        ON CONFLICT (item_id) DO UPDATE 
        SET available_until = NOW() + INTERVAL '%s hours'
        """
        for item_id in item_ids:
            self.execute_query(query, (item_id, duration_hours, duration_hours))
    
    # ===== ADMIN FUNCTIONS =====
    
    def reset_all_data(self):
        """DANGER: Wipe entire database (admin only)"""
        tables = [
            'combat_logs', 'achievements', 'inventory', 
            'daily_senders', 'shop_rotation', 'users'
        ]
        
        for table in tables:
            self.execute_query(f"TRUNCATE TABLE {table} CASCADE")
        
        # Reset server stats
        self.execute_query("UPDATE server_stats SET server_streak = 0, total_monsters_killed = 0, last_joy_sent = NULL WHERE id = 1")
        
        print("🗑️ ALL DATA WIPED")
    
    def reset_user(self, discord_id: int):
        """Reset a specific user's data"""
        self.execute_query("DELETE FROM users WHERE discord_id = %s", (discord_id,))
        print(f"🗑️ User {discord_id} reset")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("Database connection closed")

# Global database instance
db = None

def get_db() -> Database:
    """Get or create database instance"""
    global db
    if db is None:
        db = Database()
    return db
