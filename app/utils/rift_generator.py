"""
ChronoRift Rift Generator
Procedural rift spawning logic with dynamic difficulty and world state integration
"""

import random
import uuid
from enum import Enum
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import math

from app.utils.echo_generator import EchoGenerator, EchoRarity


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class RiftType(Enum):
    """Rift classification"""
    TEMPORAL = "temporal"       # Time distortion, time-based hazards
    SPATIAL = "spatial"         # Warped dimensions, maze-like
    CHAOS = "chaos"             # Unpredictable anomalies
    VOID = "void"               # Dark/corrupt energy
    ELEMENTAL = "elemental"     # Environmental hazards


class RiftSeverity(Enum):
    """Rift threat level"""
    MINOR = "minor"             # 1-2 weak Echoes
    MODERATE = "moderate"       # 2-4 common Echoes
    MAJOR = "major"             # 3-5 uncommon+ Echoes
    CATASTROPHIC = "catastrophic"  # 4-6 rare+ Echoes, boss


class RiftState(Enum):
    """Rift lifecycle state"""
    DORMANT = "dormant"         # Existing, not yet active
    ACTIVE = "active"           # Currently spawning, accepting players
    CLOSING = "closing"         # Being sealed/defeated
    SEALED = "sealed"           # Completed/closed


class RewardTier(Enum):
    """Loot tier for rift completion"""
    BRONZE = "bronze"           # Common drops
    SILVER = "silver"           # Uncommon drops
    GOLD = "gold"               # Rare drops
    PLATINUM = "platinum"       # Epic drops


# Rift spawn weight by world stability
STABILITY_SPAWN_MODIFIERS = {
    0.0: 5.0,   # Catastrophic stability = 5x more rifts
    0.2: 3.0,
    0.4: 2.0,
    0.6: 1.0,   # Normal stability
    0.8: 0.5,
    1.0: 0.1,   # Perfect stability = minimal rifts
}

# Echo spawn counts by severity
SEVERITY_SPAWN_COUNTS = {
    RiftSeverity.MINOR: (1, 2),
    RiftSeverity.MODERATE: (2, 4),
    RiftSeverity.MAJOR: (3, 5),
    RiftSeverity.CATASTROPHIC: (4, 6),
}

# Reward scaling by severity
REWARD_SCALING = {
    RiftSeverity.MINOR: 0.5,
    RiftSeverity.MODERATE: 1.0,
    RiftSeverity.MAJOR: 2.0,
    RiftSeverity.CATASTROPHIC: 4.0,
}

# Rift duration (minutes)
RIFT_DURATIONS = {
    RiftSeverity.MINOR: 10,
    RiftSeverity.MODERATE: 15,
    RiftSeverity.MAJOR: 20,
    RiftSeverity.CATASTROPHIC: 30,
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class RiftReward:
    """Rift completion rewards"""
    experience: int
    currency: int
    item_drops: List[Dict] = field(default_factory=list)
    rare_loot: Optional[Dict] = None
    bonus_multiplier: float = 1.0


@dataclass
class RiftEchoSpawn:
    """Echo spawn data within rift"""
    echo_id: str
    name: str
    level: int
    rarity: EchoRarity
    position: Tuple[float, float]  # x, y coordinates
    behavior: str                   # 'idle', 'aggressive', 'patrol'


@dataclass
class Rift:
    """Complete rift definition"""
    id: str
    rift_type: RiftType
    severity: RiftSeverity
    state: RiftState
    zone_id: str
    position: Tuple[float, float]      # x, y in zone
    radius: float                       # Rift affected area
    created_at: datetime
    expires_at: datetime
    spawned_echoes: List[RiftEchoSpawn] = field(default_factory=list)
    defeated_count: int = 0
    total_count: int = 0
    is_boss_rift: bool = False
    difficulty_multiplier: float = 1.0
    world_stability_when_spawned: float = 0.6


# ============================================================================
# RIFT GENERATOR
# ============================================================================

class RiftGenerator:
    """Procedural rift spawning system"""
    
    @staticmethod
    def calculate_spawn_rate(
        world_stability: float,
        active_rifts: int,
        player_count: int
    ) -> float:
        """
        Calculate probability of new rift spawning
        
        Args:
            world_stability: World stability value (0.0-1.0)
            active_rifts: Current number of active rifts
            player_count: Number of online players
            
        Returns:
            float: Spawn probability (0.0-1.0)
        """
        # Base spawn rate scales inversely with stability
        base_rate = 1.0 - world_stability
        
        # Stability modifier (exponential curve)
        closest_stability = min(STABILITY_SPAWN_MODIFIERS.keys(),
                               key=lambda x: abs(x - world_stability))
        stability_mult = STABILITY_SPAWN_MODIFIERS[closest_stability]
        
        # Active rift penalty (prevents spam)
        rift_penalty = 1.0 / (1.0 + active_rifts * 0.5)
        
        # Player scaling (more players = more rifts)
        player_scaling = 1.0 + (player_count - 1) * 0.1
        
        spawn_rate = base_rate * stability_mult * rift_penalty * player_scaling
        
        # Clamp to 0-1
        return max(0.0, min(1.0, spawn_rate))
    
    
    @staticmethod
    def generate_rift_type() -> RiftType:
        """
        Generate rift type with weighted probability
        
        Returns:
            RiftType: Generated rift type
        """
        weights = {
            RiftType.TEMPORAL: 25,
            RiftType.SPATIAL: 25,
            RiftType.CHAOS: 20,
            RiftType.VOID: 20,
            RiftType.ELEMENTAL: 10,
        }
        
        return random.choices(
            list(weights.keys()),
            weights=list(weights.values())
        )[0]
    
    
    @staticmethod
    def generate_severity(
        world_stability: float,
        player_level: int,
        active_rifts: int
    ) -> RiftSeverity:
        """
        Generate rift severity based on world state and player progression
        
        Args:
            world_stability: World stability (0.0-1.0)
            player_level: Average player level
            active_rifts: Number of active rifts (escalation factor)
            
        Returns:
            RiftSeverity: Generated severity
        """
        # Stability inversely affects severity
        stability_factor = 1.0 - world_stability
        
        # Active rift escalation
        escalation_bonus = active_rifts * 0.15
        
        # Combined difficulty modifier
        difficulty = stability_factor + escalation_bonus
        
        # Weighted severity selection
        if difficulty < 0.3:
            return random.choices(
                [RiftSeverity.MINOR, RiftSeverity.MODERATE],
                weights=[70, 30]
            )[0]
        elif difficulty < 0.6:
            return random.choices(
                [RiftSeverity.MODERATE, RiftSeverity.MAJOR],
                weights=[60, 40]
            )[0]
        else:
            return random.choices(
                [RiftSeverity.MAJOR, RiftSeverity.CATASTROPHIC],
                weights=[70, 30]
            )[0]
    
    
    @staticmethod
    def generate_rift_radius(severity: RiftSeverity) -> float:
        """
        Generate rift affected area radius
        
        Args:
            severity: Rift severity
            
        Returns:
            float: Radius in game units
        """
        base_radius = {
            RiftSeverity.MINOR: 50,
            RiftSeverity.MODERATE: 75,
            RiftSeverity.MAJOR: 100,
            RiftSeverity.CATASTROPHIC: 150,
        }
        
        radius = base_radius[severity]
        # Add ±10% variance
        variance = random.uniform(0.9, 1.1)
        return radius * variance
    
    
    @staticmethod
    def spawn_rift_echoes(
        rift_type: RiftType,
        severity: RiftSeverity,
        player_level: int,
        rift_position: Tuple[float, float],
        rift_radius: float,
        difficulty_multiplier: float = 1.0
    ) -> List[RiftEchoSpawn]:
        """
        Generate Echo spawns for rift
        
        Args:
            rift_type: Type of rift
            severity: Rift severity
            player_level: Player's level
            rift_position: Center position of rift
            rift_radius: Rift radius
            difficulty_multiplier: Stat/count multiplier
            
        Returns:
            List[RiftEchoSpawn]: Generated Echo spawns
        """
        min_count, max_count = SEVERITY_SPAWN_COUNTS[severity]
        
        # Adjust count by difficulty
        adjusted_count = int(random.randint(min_count, max_count) * difficulty_multiplier)
        adjusted_count = max(1, adjusted_count)  # At least one Echo
        
        # Determine Echo levels (±15% from player)
        level_variance = int(player_level * 0.15)
        
        echoes = []
        for i in range(adjusted_count):
            # Vary level per Echo
            echo_level = max(1, min(100, 
                player_level + random.randint(-level_variance, level_variance)
            ))
            
            # Force rarity based on severity
            rarity = RiftGenerator._get_rarity_for_severity(severity)
            
            # Spawn Echo
            echo = EchoGenerator.spawn_echo(level=echo_level)
            echo.rarity = rarity
            
            # Position within rift area
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, rift_radius * 0.8)
            x = rift_position[0] + distance * math.cos(angle)
            y = rift_position[1] + distance * math.sin(angle)
            
            # Behavior varies by rift type
            behavior = RiftGenerator._get_behavior_for_type(rift_type)
            
            spawn = RiftEchoSpawn(
                echo_id=echo.id,
                name=echo.name,
                level=echo.level,
                rarity=echo.rarity,
                position=(x, y),
                behavior=behavior
            )
            
            echoes.append(spawn)
        
        return echoes
    
    
    @staticmethod
    def _get_rarity_for_severity(severity: RiftSeverity) -> EchoRarity:
        """Determine guaranteed minimum rarity for severity"""
        rarity_map = {
            RiftSeverity.MINOR: random.choice([EchoRarity.COMMON, EchoRarity.UNCOMMON]),
            RiftSeverity.MODERATE: random.choice([EchoRarity.UNCOMMON, EchoRarity.RARE]),
            RiftSeverity.MAJOR: random.choice([EchoRarity.RARE, EchoRarity.EPIC]),
            RiftSeverity.CATASTROPHIC: random.choice([EchoRarity.EPIC, EchoRarity.LEGENDARY]),
        }
        return rarity_map[severity]
    
    
    @staticmethod
    def _get_behavior_for_type(rift_type: RiftType) -> str:
        """Determine Echo behavior based on rift type"""
        behavior_map = {
            RiftType.TEMPORAL: random.choice(['aggressive', 'patrol']),
            RiftType.SPATIAL: 'patrol',
            RiftType.CHAOS: 'aggressive',
            RiftType.VOID: random.choice(['aggressive', 'idle']),
            RiftType.ELEMENTAL: random.choice(['idle', 'patrol']),
        }
        return behavior_map[rift_type]
    
    
    @staticmethod
    def create_rift(
        zone_id: str,
        position: Tuple[float, float],
        player_level: int,
        world_stability: float,
        active_rifts: int,
        is_boss: bool = False
    ) -> Rift:
        """
        Create complete rift with all attributes
        
        Args:
            zone_id: Zone ID where rift spawns
            position: X, Y coordinates
            player_level: Player's level for scaling
            world_stability: World stability (0-1)
            active_rifts: Number of currently active rifts
            is_boss: Whether this is a boss rift
            
        Returns:
            Rift: Generated rift
        """
        rift_type = RiftGenerator.generate_rift_type()
        severity = RiftGenerator.generate_severity(world_stability, player_level, active_rifts)
        
        # Boss rifts force catastrophic severity
        if is_boss:
            severity = RiftSeverity.CATASTROPHIC
        
        radius = RiftGenerator.generate_rift_radius(severity)
        
        # Difficulty multiplier scales with severity and instability
        stability_mult = 1.0 + (1.0 - world_stability) * 0.5
        severity_mult = {
            RiftSeverity.MINOR: 0.8,
            RiftSeverity.MODERATE: 1.0,
            RiftSeverity.MAJOR: 1.3,
            RiftSeverity.CATASTROPHIC: 1.7,
        }[severity]
        difficulty_multiplier = stability_mult * severity_mult
        
        # Duration based on severity
        duration_minutes = RIFT_DURATIONS[severity]
        
        # Spawn Echoes
        echoes = RiftGenerator.spawn_rift_echoes(
            rift_type,
            severity,
            player_level,
            position,
            radius,
            difficulty_multiplier
        )
        
        total_count = len(echoes)
        
        # Create rift
        rift = Rift(
            id=str(uuid.uuid4()),
            rift_type=rift_type,
            severity=severity,
            state=RiftState.ACTIVE,
            zone_id=zone_id,
            position=position,
            radius=radius,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=duration_minutes),
            spawned_echoes=echoes,
            defeated_count=0,
            total_count=total_count,
            is_boss_rift=is_boss,
            difficulty_multiplier=difficulty_multiplier,
            world_stability_when_spawned=world_stability,
        )
        
        return rift
    
    
    @staticmethod
    def calculate_rewards(rift: Rift) -> RiftReward:
        """
        Calculate rewards for rift completion
        
        Args:
            rift: Completed rift
            
        Returns:
            RiftReward: Reward breakdown
        """
        # Base rewards scale with severity
        base_exp = 500
        base_currency = 250
        
        severity_mult = REWARD_SCALING[rift.severity]
        
        # Difficulty bonus
        difficulty_bonus = rift.difficulty_multiplier
        
        # Calculate totals
        experience = int(base_exp * severity_mult * difficulty_bonus)
        currency = int(base_currency * severity_mult * difficulty_bonus)
        
        # Item drops based on rarity
        item_drops = []
        for echo_spawn in rift.spawned_echoes:
            if random.random() < 0.3:  # 30% drop rate
                item = {
                    'type': 'echo_material',
                    'rarity': echo_spawn.rarity.value,
                    'value': int(50 * RARITY_MULTIPLIER.get(echo_spawn.rarity.value, 1.0))
                }
                item_drops.append(item)
        
        # Boss rifts grant rare loot
        rare_loot = None
        if rift.is_boss_rift and random.random() < 0.5:  # 50% for boss
            rare_loot = {
                'type': 'legendary_artifact',
                'name': f'Rift Artifact {random.randint(1000, 9999)}',
                'value': 5000,
                'rarity': 'legendary'
            }
        
        # Bonus multiplier for challenging rifts
        bonus_mult = 1.0 + (1.0 - rift.world_stability_when_spawned) * 0.3
        
        return RiftReward(
            experience=experience,
            currency=currency,
            item_drops=item_drops,
            rare_loot=rare_loot,
            bonus_multiplier=bonus_mult
        )
    
    
    @staticmethod
    def should_escalate_difficulty(
        active_rifts: int,
        defeated_rifts_today: int,
        average_completion_time: float  # minutes
    ) -> bool:
        """
        Determine if difficulty should escalate (dynamic difficulty)
        
        Args:
            active_rifts: Current active rift count
            defeated_rifts_today: Rifts completed today
            average_completion_time: Average time to complete
            
        Returns:
            bool: Whether to escalate
        """
        # Too many rifts active = escalate
        if active_rifts > 5:
            return True
        
        # Too many defeated = escalate
        if defeated_rifts_today > 20:
            return True
        
        # Completing too quickly = escalate
        if average_completion_time < 8:  # Under 8 minutes
            return True
        
        return False


# Rarity stat multipliers for loot
RARITY_MULTIPLIER = {
    'common': 1.0,
    'uncommon': 1.5,
    'rare': 2.5,
    'epic': 4.0,
    'legendary': 8.0,
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def check_rift_expiration(rift: Rift) -> bool:
    """
    Check if rift has expired
    
    Args:
        rift: Rift to check
        
    Returns:
        bool: True if expired
    """
    if datetime.utcnow() > rift.expires_at:
        return True
    return False


def update_rift_state(rift: Rift, echo_defeated: bool = False) -> None:
    """
    Update rift state based on progress
    
    Args:
        rift: Rift to update
        echo_defeated: Whether an Echo was just defeated
    """
    if echo_defeated:
        rift.defeated_count += 1
    
    # Check if all Echoes defeated
    if rift.defeated_count >= rift.total_count:
        rift.state = RiftState.CLOSING
    
    # Check expiration
    if check_rift_expiration(rift):
        rift.state = RiftState.SEALED


def get_rift_description(rift: Rift) -> str:
    """
    Generate human-readable rift description
    
    Args:
        rift: Rift to describe
        
    Returns:
        str: Description
    """
    type_names = {
        RiftType.TEMPORAL: "temporal anomaly",
        RiftType.SPATIAL: "dimensional rift",
        RiftType.CHAOS: "chaotic distortion",
        RiftType.VOID: "void rupture",
        RiftType.ELEMENTAL: "elemental surge",
    }
    
    severity_names = {
        RiftSeverity.MINOR: "Minor",
        RiftSeverity.MODERATE: "Moderate",
        RiftSeverity.MAJOR: "Major",
        RiftSeverity.CATASTROPHIC: "Catastrophic",
    }
    
    progress = f"{rift.defeated_count}/{rift.total_count}"
    
    return f"{severity_names[rift.severity]} {type_names[rift.rift_type]} - {progress} Echoes defeated"
