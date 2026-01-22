#!/usr/bin/env python3
"""
ChronoRift Database Seeding Script
Populates PostgreSQL with initial game data (Echoes, Moves, Items, etc.)
Run this after database migrations are complete.

Usage:
    python seed_db.py                    # Seed with default data
    python seed_db.py --reset            # Clear existing data first
    python seed_db.py --dev              # Include test/debug data
"""

import os
import sys
import argparse
import psycopg2
from psycopg2.extras import Json, execute_batch
from datetime import datetime, timedelta
import json

# Configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', 5432)
DB_NAME = os.getenv('DB_NAME', 'chronorift')
DB_USER = os.getenv('DB_USER', 'chronorift')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'changeme')

class DatabaseSeeder:
    def __init__(self, reset=False, dev_mode=False):
        self.reset = reset
        self.dev_mode = dev_mode
        self.conn = None
        self.cur = None

    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            self.cur = self.conn.cursor()
            print("✓ Connected to database")
        except psycopg2.Error as e:
            print(f"✗ Failed to connect: {e}")
            sys.exit(1)

    def disconnect(self):
        """Close database connection"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        print("✓ Disconnected from database")

    def reset_data(self):
        """Clear existing data"""
        if not self.reset:
            return

        print("\n[RESET] Clearing existing data...")
        tables = [
            'user_achievements',
            'user_items',
            'user_echoes',
            'battles',
            'moves',
            'echo_moves',
            'items',
            'echoes',
            'users'
        ]

        for table in tables:
            try:
                self.cur.execute(f"TRUNCATE TABLE {table} CASCADE")
                self.conn.commit()
                print(f"  ✓ Cleared {table}")
            except psycopg2.Error as e:
                print(f"  ✗ Error clearing {table}: {e}")
                self.conn.rollback()

    def seed_echoes(self):
        """Seed Echo creatures database"""
        print("\n[ECHOES] Seeding Echo creatures...")

        echoes_data = [
            # Tier 1 - Starting Forest
            {
                'name': 'Firewing',
                'types': Json(['fire']),
                'rarity': 'common',
                'base_hp': 39,
                'base_attack': 52,
                'base_defense': 43,
                'base_sp_atk': 60,
                'base_sp_def': 50,
                'base_speed': 65,
                'description': 'A small bird engulfed in flames. Its wings shimmer with heat.',
                'icon_url': '/assets/echoes/firewing.png',
            },
            {
                'name': 'Aquatide',
                'types': Json(['water']),
                'rarity': 'common',
                'base_hp': 45,
                'base_attack': 49,
                'base_defense': 49,
                'base_sp_atk': 65,
                'base_sp_def': 65,
                'base_speed': 45,
                'description': 'A water spirit with a fluid, graceful form.',
                'icon_url': '/assets/echoes/aquatide.png',
            },
            {
                'name': 'Verdiant',
                'types': Json(['grass']),
                'rarity': 'common',
                'base_hp': 45,
                'base_attack': 49,
                'base_defense': 49,
                'base_sp_atk': 65,
                'base_sp_def': 65,
                'base_speed': 45,
                'description': 'A plant-like creature with vibrant leaves.',
                'icon_url': '/assets/echoes/verdiant.png',
            },
            # Tier 2 - Crystal Caverns
            {
                'name': 'Voltaire',
                'types': Json(['electric']),
                'rarity': 'uncommon',
                'base_hp': 55,
                'base_attack': 40,
                'base_defense': 40,
                'base_sp_atk': 90,
                'base_sp_def': 80,
                'base_speed': 100,
                'description': 'An electric entity crackling with power.',
                'icon_url': '/assets/echoes/voltaire.png',
            },
            {
                'name': 'Frostveil',
                'types': Json(['ice', 'water']),
                'rarity': 'uncommon',
                'base_hp': 70,
                'base_attack': 40,
                'base_defense': 90,
                'base_sp_atk': 70,
                'base_sp_def': 95,
                'base_speed': 35,
                'description': 'An icy phantom with crystalline structures.',
                'icon_url': '/assets/echoes/frostveil.png',
            },
            # Tier 3 - Storm Peaks
            {
                'name': 'Tempestus',
                'types': Json(['wind', 'electric']),
                'rarity': 'rare',
                'base_hp': 80,
                'base_attack': 100,
                'base_defense': 75,
                'base_sp_atk': 95,
                'base_sp_def': 85,
                'base_speed': 110,
                'description': 'A storm spirit of tremendous power.',
                'icon_url': '/assets/echoes/tempestus.png',
            },
            # Tier 4 - Abyss
            {
                'name': 'Abyssmal',
                'types': Json(['dark', 'void']),
                'rarity': 'epic',
                'base_hp': 120,
                'base_attack': 130,
                'base_defense': 100,
                'base_sp_atk': 120,
                'base_sp_def': 100,
                'base_speed': 95,
                'description': 'A creature from the depths of the void.',
                'icon_url': '/assets/echoes/abyssmal.png',
            },
            # Tier 5 - Void Nexus
            {
                'name': 'Chronarch',
                'types': Json(['chrono', 'void']),
                'rarity': 'legendary',
                'base_hp': 150,
                'base_attack': 140,
                'base_defense': 120,
                'base_sp_atk': 160,
                'base_sp_def': 140,
                'base_speed': 120,
                'description': 'The master of time and void. A force beyond comprehension.',
                'icon_url': '/assets/echoes/chronarch.png',
            },
        ]

        sql = """
            INSERT INTO echoes 
            (name, types, rarity, base_hp, base_attack, base_defense, 
             base_sp_atk, base_sp_def, base_speed, description, icon_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (name) DO NOTHING
        """

        try:
            for echo in echoes_data:
                self.cur.execute(sql, (
                    echo['name'],
                    echo['types'],
                    echo['rarity'],
                    echo['base_hp'],
                    echo['base_attack'],
                    echo['base_defense'],
                    echo['base_sp_atk'],
                    echo['base_sp_def'],
                    echo['base_speed'],
                    echo['description'],
                    echo['icon_url'],
                ))
            self.conn.commit()
            print(f"  ✓ Seeded {len(echoes_data)} Echoes")
        except psycopg2.Error as e:
            print(f"  ✗ Error seeding Echoes: {e}")
            self.conn.rollback()

    def seed_moves(self):
        """Seed moves database"""
        print("\n[MOVES] Seeding moves...")

        moves_data = [
            # Fire moves
            {'name': 'Ember', 'type': 'fire', 'category': 'special', 'power': 40, 'accuracy': 100, 'pp': 25},
            {'name': 'Flame Burst', 'type': 'fire', 'category': 'special', 'power': 70, 'accuracy': 100, 'pp': 15},
            {'name': 'Inferno', 'type': 'fire', 'category': 'special', 'power': 150, 'accuracy': 90, 'pp': 5},
            # Water moves
            {'name': 'Water Gun', 'type': 'water', 'category': 'special', 'power': 40, 'accuracy': 100, 'pp': 25},
            {'name': 'Aqua Jet', 'type': 'water', 'category': 'physical', 'power': 60, 'accuracy': 100, 'pp': 20},
            {'name': 'Hydro Pump', 'type': 'water', 'category': 'special', 'power': 110, 'accuracy': 80, 'pp': 5},
            # Electric moves
            {'name': 'Thunderbolt', 'type': 'electric', 'category': 'special', 'power': 90, 'accuracy': 100, 'pp': 15},
            {'name': 'Thunder Wave', 'type': 'electric', 'category': 'status', 'power': 0, 'accuracy': 90, 'pp': 20},
            {'name': 'Thunder', 'type': 'electric', 'category': 'special', 'power': 110, 'accuracy': 70, 'pp': 10},
            # Status moves
            {'name': 'Protect', 'type': 'normal', 'category': 'status', 'power': 0, 'accuracy': 100, 'pp': 10},
            {'name': 'Swords Dance', 'type': 'normal', 'category': 'status', 'power': 0, 'accuracy': 100, 'pp': 30},
            {'name': 'Agility', 'type': 'psychic', 'category': 'status', 'power': 0, 'accuracy': 100, 'pp': 30},
        ]

        sql = """
            INSERT INTO moves 
            (name, type, category, power, accuracy, pp)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (name) DO NOTHING
        """

        try:
            for move in moves_data:
                self.cur.execute(sql, (
                    move['name'],
                    move['type'],
                    move['category'],
                    move['power'],
                    move['accuracy'],
                    move['pp'],
                ))
            self.conn.commit()
            print(f"  ✓ Seeded {len(moves_data)} moves")
        except psycopg2.Error as e:
            print(f"  ✗ Error seeding moves: {e}")
            self.conn.rollback()

    def seed_items(self):
        """Seed items database"""
        print("\n[ITEMS] Seeding items...")

        items_data = [
            {'name': 'Potion', 'type': 'potion', 'rarity': 'common', 'effect': 'Restores 20 HP', 'value': 300},
            {'name': 'Super Potion', 'type': 'potion', 'rarity': 'uncommon', 'effect': 'Restores 50 HP', 'value': 700},
            {'name': 'Hyper Potion', 'type': 'potion', 'rarity': 'rare', 'effect': 'Restores 200 HP', 'value': 1500},
            {'name': 'Full Restore', 'type': 'potion', 'rarity': 'epic', 'effect': 'Restores all HP and status', 'value': 3000},
            {'name': 'Revive', 'type': 'revive', 'rarity': 'uncommon', 'effect': 'Revives with 50% HP', 'value': 1500},
            {'name': 'Max Revive', 'type': 'revive', 'rarity': 'rare', 'effect': 'Revives with full HP', 'value': 4000},
            {'name': 'Chronosphere', 'type': 'key_item', 'rarity': 'legendary', 'effect': 'Legendary artifact', 'value': 0},
        ]

        sql = """
            INSERT INTO items 
            (name, type, rarity, effect, value)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (name) DO NOTHING
        """

        try:
            for item in items_data:
                self.cur.execute(sql, (
                    item['name'],
                    item['type'],
                    item['rarity'],
                    item['effect'],
                    item['value'],
                ))
            self.conn.commit()
            print(f"  ✓ Seeded {len(items_data)} items")
        except psycopg2.Error as e:
            print(f"  ✗ Error seeding items: {e}")
            self.conn.rollback()

    def seed_test_users(self):
        """Seed test user data (dev mode only)"""
        if not self.dev_mode:
            return

        print("\n[TEST USERS] Seeding test user data...")

        # Note: In production, use proper password hashing (bcrypt)
        test_users = [
            {
                'username': 'testplayer',
                'email': 'test@chronorift.local',
                'password_hash': 'hashed_password_123',  # Replace with actual hash
                'level': 50,
                'experience': 500000,
            },
            {
                'username': 'admin',
                'email': 'admin@chronorift.local',
                'password_hash': 'hashed_admin_pass',
                'level': 100,
                'experience': 9999999,
            },
        ]

        sql = """
            INSERT INTO users 
            (username, email, password_hash, level, experience)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
        """

        try:
            for user in test_users:
                self.cur.execute(sql, (
                    user['username'],
                    user['email'],
                    user['password_hash'],
                    user['level'],
                    user['experience'],
                ))
            self.conn.commit()
            print(f"  ✓ Seeded {len(test_users)} test users")
        except psycopg2.Error as e:
            print(f"  ✗ Error seeding test users: {e}")
            self.conn.rollback()

    def run(self):
        """Execute all seeding operations"""
        print("\n" + "="*60)
        print("ChronoRift Database Seeding")
        print("="*60)

        try:
            self.connect()
            self.reset_data()
            self.seed_echoes()
            self.seed_moves()
            self.seed_items()
            self.seed_test_users()

            print("\n" + "="*60)
            print("✓ Database seeding completed successfully!")
            print("="*60 + "\n")

        except Exception as e:
            print(f"\n✗ Seeding failed: {e}\n")
            sys.exit(1)
        finally:
            self.disconnect()


def main():
    parser = argparse.ArgumentParser(
        description='ChronoRift Database Seeding Script'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Clear existing data before seeding'
    )
    parser.add_argument(
        '--dev',
        action='store_true',
        help='Include test/debug data'
    )

    args = parser.parse_args()

    seeder = DatabaseSeeder(reset=args.reset, dev_mode=args.dev)
    seeder.run()


if __name__ == '__main__':
    main()
