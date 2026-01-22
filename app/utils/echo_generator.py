"""
ChronoRift Echo Generator
Procedurally generates Echo creatures with stats, abilities, and attributes
"""

import random
import uuid
from enum import Enum
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class EchoRarity(Enum):
    """Echo rarity tiers"""
    COMMON = "common"           # 60% spawn rate
    UNCOMMON = "uncommon"       # 25% spawn rate
    RARE = "rare"               # 10% spawn rate
    EPIC = "epic"               # 4% spawn rate
    LEGENDARY = "legendary"     # 1% spawn rate


class EchoType(Enum):
    """Echo type classifications"""
    BEAST = "beast"
    SPIRIT = "spirit"
    MACHINE = "machine"
    VOID = "void"
    FLORA = "flora"
    ELEMENTAL = "elemental"


class EchoElement(Enum):
    """Echo elemental alignment"""
    FIRE = "fire"
    WATER = "water"
    WIND = "wind"
    EARTH = "earth"
    LIGHT = "light"
    DARK = "dark"
    NEUTRAL = "neutral"


# Stat scaling multipliers by rarity
RARITY_MULTIPLIERS = {
    EchoRarity.COMMON: 1.0,
    EchoRarity.UNCOMMON: 1.15,
    EchoRarity.RARE: 1.35,
    EchoRarity.EPIC: 1.60,
    EchoRarity.LEGENDARY: 2.0,
}

# Base stat templates for each type
TYPE_STAT_TEMPLATES = {
    EchoType.BEAST: {'hp': 45, 'atk': 52, 'def': 43, 'sp_atk': 40, 'sp_def': 40, 'spd': 35},
    EchoType.SPIRIT: {'hp': 40, 'atk': 35, 'def': 40, 'sp_atk': 60, 'sp_def': 60, 'spd': 50},
    EchoType.MACHINE: {'hp': 50, 'atk': 55, 'def': 65, 'sp_atk': 45, 'sp_def': 45, 'spd': 30},
    EchoType.VOID: {'hp': 55, 'atk': 60, 'def': 45, 'sp_atk': 65, 'sp_def': 35, 'spd': 50},
    EchoType.FLORA: {'hp': 65, 'atk': 40, 'def': 55, 'sp_atk': 50, 'sp_def': 60, 'spd': 30},
    EchoType.ELEMENTAL: {'hp': 45, 'atk': 45, 'def': 45, 'sp_atk': 65, 'sp_def': 50, 'spd': 55},
}

# Ability pool - mapped by type
ABILITY_POOL = {
    EchoType.BEAST: [
        {'name': 'Feral Instinct', 'effect': 'atk_boost', 'power': 1.2},
        {'name': 'Predator', 'effect': 'crit_boost', 'power': 1.5},
        {'name': 'Thick Hide', 'effect': 'def_boost', 'power': 1.15},
        {'name': 'Pack Mentality', 'effect': 'team_atk_boost', 'power': 1.1},
    ],
    EchoType.SPIRIT: [
        {'name': 'Ethereal Drift', 'effect': 'evade_boost', 'power': 1.2},
        {'name': 'Soul Link', 'effect': 'sp_atk_boost', 'power': 1.2},
        {'name': 'Spectral Form', 'effect': 'take_half_physical', 'power': 0.5},
        {'name': 'Resonance', 'effect': 'sp_def_boost', 'power': 1.15},
    ],
    EchoType.MACHINE: [
        {'name': 'Overdrive', 'effect': 'atk_boost', 'power': 1.25},
        {'name': 'Armor Plating', 'effect': 'def_boost', 'power': 1.25},
        {'name': 'Precision Systems', 'effect': 'crit_boost', 'power': 1.6},
        {'name': 'Energy Core', 'effect': 'sp_atk_boost', 'power': 1.2},
    ],
    EchoType.VOID: [
        {'name': 'Void Touch', 'effect': 'dark_damage', 'power': 1.3},
        {'name': 'Entropy', 'effect': 'def_reduction', 'power': 0.85},
        {'name': 'Abyssal Aura', 'effect': 'enemy_sp_def_down', 'power': 0.9},
        {'name': 'Temporal Distortion', 'effect': 'spd_boost', 'power': 1.2},
    ],
    EchoType.FLORA: [
        {'name': 'Photosynthesis', 'effect': 'hp_regen', 'power': 0.125},  # 12.5% per turn
        {'name': 'Growth', 'effect': 'stat_growth', 'power': 1.1},
        {'name': 'Root Defense', 'effect': 'def_boost', 'power': 1.2},
        {'name': 'Spore Cloud', 'effect': 'poison_damage', 'power': 1.15},
    ],
    EchoType.ELEMENTAL: [
        {'name': 'Inferno', 'effect': 'fire_damage', 'power': 1.25},
        {'name': 'Torrent', 'effect': 'water_damage', 'power': 1.25},
        {'name': 'Static Charge', 'effect': 'electric_damage', 'power': 1.25},
        {'name': 'Elemental Fusion', 'effect': 'mixed_damage', 'power': 1.15},
    ],
}

# Move pool by type
MOVE_POOL = {
    EchoType.BEAST: [
        {'name': 'Claw Strike', 'type': 'physical', 'power': 75, 'accuracy': 100},
        {'name': 'Bite', 'type': 'physical', 'power': 60, 'accuracy': 100},
        {'name': 'Howl', 'type': 'status', 'effect': 'atk_boost', 'accuracy': 100},
        {'name': 'Tackle', 'type': 'physical', 'power': 40, 'accuracy': 100},
    ],
    EchoType.SPIRIT: [
        {'name': 'Spirit Blast', 'type': 'special', 'power': 80, 'accuracy': 100},
        {'name': 'Ethereal Bolt', 'type': 'special', 'power': 65, 'accuracy': 90},
        {'name': 'Reflect', 'type': 'status', 'effect': 'def_boost', 'accuracy': 100},
        {'name': 'Spectral Gaze', 'type': 'status', 'effect': 'paralyze', 'accuracy': 75},
    ],
    EchoType.MACHINE: [
        {'name': 'Metal Burst', 'type': 'physical', 'power': 85, 'accuracy': 100},
        {'name': 'Laser Focus', 'type': 'special', 'power': 75, 'accuracy': 100},
        {'name': 'Iron Defense', 'type': 'status', 'effect': 'def_boost', 'accuracy': 100},
        {'name': 'Power Surge', 'type': 'special', 'power': 70, 'accuracy': 95},
    ],
    EchoType.VOID: [
        {'name': 'Void Claw', 'type': 'physical', 'power': 90, 'accuracy': 100},
        {'name': 'Dark Pulse', 'type': 'special', 'power': 80, 'accuracy': 100},
        {'name': 'Temporal Slash', 'type': 'physical', 'power': 95, 'accuracy': 85},
        {'name': 'Entropy Beam', 'type': 'special', 'power': 70, 'accuracy': 90},
    ],
    EchoType.FLORA: [
        {'name': 'Vine Whip', 'type': 'physical', 'power': 75, 'accuracy': 100},
        {'name': 'Solar Beam', 'type': 'special', 'power': 120, 'accuracy': 100},
        {'name': 'Spore', 'type': 'status', 'effect': 'poison', 'accuracy': 85},
        {'name': 'Synthesis', 'type': 'status', 'effect': 'heal', 'accuracy': 100},
    ],
    EchoType.ELEMENTAL: [
        {'name': 'Fireball', 'type': 'special', 'power': 85, 'accuracy': 100},
        {'name': 'Ice Storm', 'type': 'special', 'power': 85, 'accuracy': 100},
        {'name': 'Thunderbolt', 'type': 'special', 'power': 85, 'accuracy': 100},
        {'name': 'Elemental Surge', 'type': 'special', 'power': 75, 'accuracy': 95},
    ],
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class EchoStats:
    """Echo battle statistics"""
    hp: int
    atk: int              # Physical attack
    def_: int             # Physical defense
    sp_atk: int           # Special attack
    sp_def: int           # Special defense
    spd: int              # Speed
    
    def total(self) -> int:
        """Calculate total stats"""
        return self.hp + self.atk + self.def_ + self.sp_atk + self.sp_def + self.spd


@dataclass
class Echo:
    """Echo creature definition"""
    id: str
    name: str
    echo_type: EchoType
    element: EchoElement
    rarity: EchoRarity
    level: int
    base_stats: EchoStats
    current_stats: EchoStats
    ability: Dict
    moves: List[Dict]
    gender: str              # 'male', 'female', 'unknown'
    nature: str              # Affects stat growth
    experience: int
    captured_at: datetime
    is_shiny: bool = False


# ============================================================================
# ECHO GENERATOR
# ============================================================================

class EchoGenerator:
    """Procedural Echo generation system"""
    
    @staticmethod
    def generate_rarity() -> EchoRarity:
        """
        Generate Echo rarity with weighted probability
        
        Returns:
            EchoRarity: Generated rarity tier
        """
        roll = random.randint(1, 100)
        
        if roll <= 60:
            return EchoRarity.COMMON
        elif roll <= 85:
            return EchoRarity.UNCOMMON
        elif roll <= 95:
            return EchoRarity.RARE
        elif roll <= 99:
            return EchoRarity.EPIC
        else:
            return EchoRarity.LEGENDARY
    
    
    @staticmethod
    def generate_shiny(rarity: EchoRarity) -> bool:
        """
        Determine if Echo is shiny (alternate coloring)
        Rarer Echoes have higher shiny rates
        
        Args:
            rarity: Echo rarity tier
            
        Returns:
            bool: Whether Echo is shiny
        """
        shiny_chance = {
            EchoRarity.COMMON: 0.5,
            EchoRarity.UNCOMMON: 1.0,
            EchoRarity.RARE: 3.0,
            EchoRarity.EPIC: 8.0,
            EchoRarity.LEGENDARY: 25.0,
        }
        
        return random.randint(1, 10000) <= (shiny_chance[rarity] * 100)
    
    
    @staticmethod
    def generate_stats(echo_type: EchoType, rarity: EchoRarity, level: int) -> EchoStats:
        """
        Generate base stats for Echo
        
        Args:
            echo_type: Type of Echo
            rarity: Rarity tier
            level: Echo level (1-100)
            
        Returns:
            EchoStats: Generated stats
        """
        template = TYPE_STAT_TEMPLATES[echo_type]
        multiplier = RARITY_MULTIPLIERS[rarity]
        
        # Add variance (±10% per stat)
        variance_range = 0.1
        
        def calculate_stat(base: int) -> int:
            # Apply rarity multiplier
            stat = base * multiplier
            
            # Apply variance
            variance = random.uniform(-variance_range, variance_range)
            stat = stat * (1 + variance)
            
            # Apply level scaling (curve formula)
            # Stats grow exponentially with level
            level_scaling = 1 + (level - 1) * 0.05  # 5% per level
            stat = stat * level_scaling
            
            # Ensure minimum of 1
            return max(1, int(stat))
        
        return EchoStats(
            hp=calculate_stat(template['hp']),
            atk=calculate_stat(template['atk']),
            def_=calculate_stat(template['def']),
            sp_atk=calculate_stat(template['sp_atk']),
            sp_def=calculate_stat(template['sp_def']),
            spd=calculate_stat(template['spd']),
        )
    
    
    @staticmethod
    def generate_name(echo_type: EchoType, is_shiny: bool) -> str:
        """
        Generate Echo name procedurally
        
        Args:
            echo_type: Type of Echo
            is_shiny: Whether Echo is shiny
            
        Returns:
            str: Generated name
        """
        prefixes = {
            EchoType.BEAST: ['Fer', 'Bru', 'Sav', 'Rag', 'Claw', 'Fang'],
            EchoType.SPIRIT: ['Spec', 'Phan', 'Wraith', 'Ether', 'Soul', 'Echo'],
            EchoType.MACHINE: ['Mech', 'Cyber', 'Auto', 'Iron', 'Tech', 'Gear'],
            EchoType.VOID: ['Void', 'Shad', 'Abyss', 'Dark', 'Chao', 'Null'],
            EchoType.FLORA: ['Leaf', 'Bloom', 'Petal', 'Vine', 'Thorn', 'Spore'],
            EchoType.ELEMENTAL: ['Flame', 'Frost', 'Storm', 'Ember', 'Spark', 'Gale'],
        }
        
        suffixes = ['ion', 'oid', 'asaurus', 'ling', 'sprite', 'form', 'flux', 'surge']
        
        prefix = random.choice(prefixes[echo_type])
        suffix = random.choice(suffixes)
        
        name = prefix + suffix
        
        # Shiny Echoes get special prefix
        if is_shiny:
            name = 'Golden' + name.capitalize()
        
        return name
    
    
    @staticmethod
    def generate_element(echo_type: EchoType) -> EchoElement:
        """
        Generate elemental alignment based on type
        
        Args:
            echo_type: Type of Echo
            
        Returns:
            EchoElement: Elemental alignment
        """
        type_elements = {
            EchoType.BEAST: [EchoElement.NEUTRAL, EchoElement.DARK, EchoElement.EARTH],
            EchoType.SPIRIT: [EchoElement.LIGHT, EchoElement.DARK, EchoElement.NEUTRAL],
            EchoType.MACHINE: [EchoElement.NEUTRAL, EchoElement.LIGHT],
            EchoType.VOID: [EchoElement.DARK, EchoElement.NEUTRAL],
            EchoType.FLORA: [EchoElement.EARTH, EchoElement.WATER, EchoElement.LIGHT],
            EchoType.ELEMENTAL: list(EchoElement),
        }
        
        return random.choice(type_elements[echo_type])
    
    
    @staticmethod
    def generate_ability(echo_type: EchoType) -> Dict:
        """
        Generate primary ability for Echo
        
        Args:
            echo_type: Type of Echo
            
        Returns:
            Dict: Ability definition
        """
        abilities = ABILITY_POOL.get(echo_type, [])
        if not abilities:
            return {'name': 'Basic Ability', 'effect': 'none', 'power': 1.0}
        
        return random.choice(abilities).copy()
    
    
    @staticmethod
    def generate_moves(echo_type: EchoType, level: int, count: int = 4) -> List[Dict]:
        """
        Generate move set for Echo
        
        Args:
            echo_type: Type of Echo
            level: Echo level (affects available moves)
            count: Number of moves (default 4)
            
        Returns:
            List[Dict]: List of moves
        """
        available_moves = MOVE_POOL.get(echo_type, []).copy()
        
        if not available_moves:
            available_moves = [{'name': 'Tackle', 'type': 'physical', 'power': 40, 'accuracy': 100}]
        
        # Limit moves based on level (roughly 1 per 20 levels)
        max_moves = min(count, max(1, level // 20 + 1))
        
        # Always include at least one move
        selected = random.sample(available_moves, min(max_moves, len(available_moves)))
        
        return [move.copy() for move in selected]
    
    
    @staticmethod
    def generate_gender() -> str:
        """
        Generate Echo gender
        
        Returns:
            str: 'male', 'female', or 'unknown'
        """
        roll = random.randint(1, 100)
        if roll <= 50:
            return 'male'
        elif roll <= 90:
            return 'female'
        else:
            return 'unknown'
    
    
    @staticmethod
    def generate_nature() -> str:
        """
        Generate Echo nature (affects stat growth)
        
        Returns:
            str: Nature name
        """
        natures = [
            'Hardy', 'Lonely', 'Brave', 'Adamant', 'Naughty',
            'Bold', 'Docile', 'Relaxed', 'Timid', 'Hasty',
            'Serious', 'Calm', 'Gentle', 'Sassy', 'Careful',
            'Quirky', 'Shy', 'Quiet', 'Rash', 'Lax',
        ]
        return random.choice(natures)
    
    
    @staticmethod
    def spawn_echo(level: int = None, echo_type: EchoType = None) -> Echo:
        """
        Spawn a complete Echo with all generated attributes
        
        Args:
            level: Echo level (1-100). Random if None
            echo_type: Force specific type. Random if None
            
        Returns:
            Echo: Generated Echo creature
        """
        # Generate level if not provided
        if level is None:
            level = random.randint(1, 50)  # Typical spawn range
        else:
            level = max(1, min(100, level))  # Clamp to 1-100
        
        # Generate type if not provided
        if echo_type is None:
            echo_type = random.choice(list(EchoType))
        
        # Generate other attributes
        rarity = EchoGenerator.generate_rarity()
        is_shiny = EchoGenerator.generate_shiny(rarity)
        name = EchoGenerator.generate_name(echo_type, is_shiny)
        element = EchoGenerator.generate_element(echo_type)
        stats = EchoGenerator.generate_stats(echo_type, rarity, level)
        ability = EchoGenerator.generate_ability(echo_type)
        moves = EchoGenerator.generate_moves(echo_type, level)
        gender = EchoGenerator.generate_gender()
        nature = EchoGenerator.generate_nature()
        
        # Create Echo instance
        echo = Echo(
            id=str(uuid.uuid4()),
            name=name,
            echo_type=echo_type,
            element=element,
            rarity=rarity,
            level=level,
            base_stats=stats,
            current_stats=EchoStats(
                hp=stats.hp,
                atk=stats.atk,
                def_=stats.def_,
                sp_atk=stats.sp_atk,
                sp_def=stats.sp_def,
                spd=stats.spd,
            ),
            ability=ability,
            moves=moves,
            gender=gender,
            nature=nature,
            experience=0,
            captured_at=datetime.utcnow(),
            is_shiny=is_shiny,
        )
        
        return echo
    
    
    @staticmethod
    def spawn_wild_encounter(player_level: int) -> List[Echo]:
        """
        Generate wild Echo encounter based on player level
        
        Args:
            player_level: Player's current level
            
        Returns:
            List[Echo]: 1-3 wild Echoes
        """
        # Encounter size
        encounter_size = random.choices([1, 2, 3], weights=[50, 35, 15])[0]
        
        # Level variance (±5-10 levels from player)
        variance = random.randint(-10, 10)
        encounter_level = max(1, min(100, player_level + variance))
        
        echoes = []
        for _ in range(encounter_size):
            # Slight variation per Echo
            level_var = random.randint(-2, 2)
            echo = EchoGenerator.spawn_echo(
                level=max(1, encounter_level + level_var)
            )
            echoes.append(echo)
        
        return echoes
    
    
    @staticmethod
    def spawn_boss_echo(difficulty: str = 'normal') -> Echo:
        """
        Generate a boss-tier Echo
        
        Args:
            difficulty: 'easy', 'normal', 'hard', 'legendary'
            
        Returns:
            Echo: Boss Echo with enhanced stats
        """
        level_map = {
            'easy': 20,
            'normal': 35,
            'hard': 50,
            'legendary': 80,
        }
        
        level = level_map.get(difficulty, 35)
        
        # Ensure legendary rarity for hard+ bosses
        echo_type = random.choice(list(EchoType))
        echo = EchoGenerator.spawn_echo(level=level, echo_type=echo_type)
        
        if difficulty in ['hard', 'legendary']:
            # Boost stats
            multiplier = 1.5 if difficulty == 'hard' else 2.0
            echo.base_stats.hp = int(echo.base_stats.hp * multiplier)
            echo.base_stats.atk = int(echo.base_stats.atk * multiplier)
            echo.base_stats.sp_atk = int(echo.base_stats.sp_atk * multiplier)
            
            # Force rare+ rarity
            if echo.rarity not in [EchoRarity.RARE, EchoRarity.EPIC, EchoRarity.LEGENDARY]:
                echo.rarity = random.choice([EchoRarity.RARE, EchoRarity.EPIC])
        
        return echo


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def evolve_echo(echo: Echo) -> Echo:
    """
    Evolve Echo to next form (increase level, boost stats)
    
    Args:
        echo: Echo to evolve
        
    Returns:
        Echo: Evolved Echo
    """
    evolved = Echo(
        id=echo.id,
        name=f"Evolved {echo.name}",
        echo_type=echo.echo_type,
        element=echo.element,
        rarity=echo.rarity,
        level=min(100, echo.level + 10),
        base_stats=EchoGenerator.generate_stats(
            echo.echo_type,
            echo.rarity,
            min(100, echo.level + 10)
        ),
        current_stats=EchoStats(
            hp=int(echo.current_stats.hp * 1.3),
            atk=int(echo.current_stats.atk * 1.25),
            def_=int(echo.current_stats.def_ * 1.25),
            sp_atk=int(echo.current_stats.sp_atk * 1.3),
            sp_def=int(echo.current_stats.sp_def * 1.25),
            spd=int(echo.current_stats.spd * 1.2),
        ),
        ability=echo.ability,
        moves=echo.moves + EchoGenerator.generate_moves(echo.echo_type, echo.level + 10, 1),
        gender=echo.gender,
        nature=echo.nature,
        experience=echo.experience,
        captured_at=echo.captured_at,
        is_shiny=echo.is_shiny,
    )
    
    return evolved


def calculate_experience_gained(player_level: int, echo_level: int, echo_rarity: EchoRarity) -> int:
    """
    Calculate experience gained from defeating Echo
    
    Args:
        player_level: Player's current level
        echo_level: Defeated Echo's level
        echo_rarity: Echo's rarity
        
    Returns:
        int: Experience points gained
    """
    base_exp = 100
    
    # Level bonus (higher level enemies give more exp)
    level_bonus = echo_level * 2
    
    # Rarity multiplier
    rarity_mult = RARITY_MULTIPLIERS[echo_rarity]
    
    # Difficulty bonus (if Echo was higher level)
    difficulty_mult = max(1.0, 1 + (echo_level - player_level) * 0.05)
    
    return int(base_exp + level_bonus * rarity_mult * difficulty_mult)
