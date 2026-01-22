"""
ChronoRift Bonding Engine
Echo bonding progression system with friendship mechanics and stat boosts
"""

import random
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class BondLevel(Enum):
    """Echo bond progression stages"""
    STRANGER = "stranger"           # 0-19 bond
    ACQUAINTANCE = "acquaintance"   # 20-39 bond
    FRIEND = "friend"               # 40-79 bond
    CLOSE_FRIEND = "close_friend"   # 80-119 bond
    BEST_FRIEND = "best_friend"     # 120-159 bond
    SOULBOUND = "soulbound"         # 160-199 bond
    KINDRED_SPIRIT = "kindred_spirit"  # 200+ bond


class BondActivityType(Enum):
    """Actions that affect bonding"""
    BATTLE_VICTORY = "battle_victory"
    LEVEL_UP = "level_up"
    EVOLUTION = "evolution"
    BOND_ITEM_GIFT = "bond_item_gift"
    REST_TOGETHER = "rest_together"
    CAMPING = "camping"
    EXPLORATION = "exploration"
    TRAINING = "training"
    DEFEAT = "defeat"                # Negative
    FAINT = "faint"                  # Negative
    NEGLECT = "neglect"              # Negative


class BondMilestone(Enum):
    """Bond level milestones"""
    FIRST_BATTLE = "first_battle"       # 5 bond
    INITIAL_TRUST = "initial_trust"     # 20 bond
    FRIENDSHIP_FORMED = "friendship_formed"  # 40 bond
    CLOSE_BOND = "close_bond"           # 80 bond
    BEST_FRIEND_UNLOCKED = "best_friend_unlocked"  # 120 bond
    SOULBOUND = "soulbound"             # 160 bond
    PERFECT_BOND = "perfect_bond"       # 200+ bond


# Bond point modifications
BOND_CHANGES = {
    BondActivityType.BATTLE_VICTORY: 3,
    BondActivityType.LEVEL_UP: 2,
    BondActivityType.EVOLUTION: 10,
    BondActivityType.BOND_ITEM_GIFT: 5,
    BondActivityType.REST_TOGETHER: 1,
    BondActivityType.CAMPING: 2,
    BondActivityType.EXPLORATION: 1,
    BondActivityType.TRAINING: 1,
    BondActivityType.DEFEAT: -1,
    BondActivityType.FAINT: -5,
    BondActivityType.NEGLECT: -1,  # Per day not used
}

# Bond level stat multipliers
BOND_STAT_MULTIPLIERS = {
    BondLevel.STRANGER: 1.0,
    BondLevel.ACQUAINTANCE: 1.02,
    BondLevel.FRIEND: 1.05,
    BondLevel.CLOSE_FRIEND: 1.08,
    BondLevel.BEST_FRIEND: 1.10,
    BondLevel.SOULBOUND: 1.13,
    BondLevel.KINDRED_SPIRIT: 1.15,
}

# Bond critical hit rate bonus
BOND_CRITICAL_BONUS = {
    BondLevel.STRANGER: 0.0,
    BondLevel.ACQUAINTANCE: 0.01,
    BondLevel.FRIEND: 0.03,
    BondLevel.CLOSE_FRIEND: 0.05,
    BondLevel.BEST_FRIEND: 0.08,
    BondLevel.SOULBOUND: 0.10,
    BondLevel.KINDRED_SPIRIT: 0.15,
}

# Experience scaling based on bond
BOND_EXPERIENCE_MULTIPLIER = {
    BondLevel.STRANGER: 1.0,
    BondLevel.ACQUAINTANCE: 1.05,
    BondLevel.FRIEND: 1.10,
    BondLevel.CLOSE_FRIEND: 1.15,
    BondLevel.BEST_FRIEND: 1.20,
    BondLevel.SOULBOUND: 1.25,
    BondLevel.KINDRED_SPIRIT: 1.30,
}

# Max bond points
MAX_BOND = 255

# Days until neglect penalty applies
NEGLECT_THRESHOLD_DAYS = 3


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class BondMemory:
    """Memorable Echo bonding event"""
    timestamp: datetime
    activity_type: BondActivityType
    bond_change: int
    description: str
    location: Optional[str] = None


@dataclass
class EchoBond:
    """Echo bonding state and progression"""
    echo_id: str
    character_id: str
    bond_points: int = 0
    bond_level: BondLevel = BondLevel.STRANGER
    last_interaction: datetime = field(default_factory=datetime.utcnow)
    last_activity: Optional[BondActivityType] = None
    memories: List[BondMemory] = field(default_factory=list)
    
    # Milestone tracking
    milestones_reached: List[BondMilestone] = field(default_factory=list)
    
    # Bond features unlocked
    can_evolve_by_bond: bool = False
    synchronization_level: float = 0.0  # 0.0-1.0 (affects move accuracy/power)
    
    # Bond stats
    battles_fought_together: int = 0
    distance_traveled_together: float = 0.0  # In-game units
    victories_together: int = 0
    
    def current_bond_level(self) -> BondLevel:
        """Get current bond level based on bond points"""
        if self.bond_points < 20:
            return BondLevel.STRANGER
        elif self.bond_points < 40:
            return BondLevel.ACQUAINTANCE
        elif self.bond_points < 80:
            return BondLevel.FRIEND
        elif self.bond_points < 120:
            return BondLevel.CLOSE_FRIEND
        elif self.bond_points < 160:
            return BondLevel.BEST_FRIEND
        elif self.bond_points < 200:
            return BondLevel.SOULBOUND
        else:
            return BondLevel.KINDRED_SPIRIT


# ============================================================================
# BONDING ENGINE
# ============================================================================

class BondingEngine:
    """Echo bonding progression and stat enhancement system"""
    
    @staticmethod
    def initialize_bond(echo_id: str, character_id: str) -> EchoBond:
        """
        Create new bond between player and Echo
        
        Args:
            echo_id: Echo's unique ID
            character_id: Player's character ID
            
        Returns:
            EchoBond: New bonding relationship
        """
        bond = EchoBond(
            echo_id=echo_id,
            character_id=character_id,
            bond_points=0,
            bond_level=BondLevel.STRANGER,
            last_interaction=datetime.utcnow(),
        )
        
        return bond
    
    
    @staticmethod
    def add_bond_points(
        bond: EchoBond,
        activity: BondActivityType,
        multiplier: float = 1.0,
        description: str = ""
    ) -> int:
        """
        Add bond points from activity
        
        Args:
            bond: Echo bond
            activity: Activity type
            multiplier: Bonus multiplier (e.g., 1.5x for special item)
            description: Activity description for memory
            
        Returns:
            int: Points gained
        """
        base_points = BOND_CHANGES.get(activity, 0)
        points_gained = int(base_points * multiplier)
        
        # Clamp bond points to max
        previous_points = bond.bond_points
        bond.bond_points = min(MAX_BOND, bond.bond_points + points_gained)
        
        # Update state
        bond.last_interaction = datetime.utcnow()
        bond.last_activity = activity
        
        # Check for level up
        old_level = BondingEngine._get_level_for_points(previous_points)
        new_level = BondingEngine._get_level_for_points(bond.bond_points)
        
        if new_level != old_level:
            bond.bond_level = new_level
            BondingEngine._check_milestones(bond, new_level)
        
        # Update synchronization
        bond.synchronization_level = bond.bond_points / MAX_BOND
        
        # Record memory
        memory = BondMemory(
            timestamp=datetime.utcnow(),
            activity_type=activity,
            bond_change=points_gained,
            description=description or activity.value
        )
        bond.memories.append(memory)
        
        # Keep only recent 50 memories
        if len(bond.memories) > 50:
            bond.memories = bond.memories[-50:]
        
        return points_gained
    
    
    @staticmethod
    def record_battle_victory(bond: EchoBond, enemy_level: int) -> None:
        """
        Record battle victory for bonding
        
        Args:
            bond: Echo bond
            enemy_level: Defeated enemy level
        """
        multiplier = 1.0 + (enemy_level / 100)  # Stronger enemies = more bond
        BondingEngine.add_bond_points(
            bond,
            BondActivityType.BATTLE_VICTORY,
            multiplier=multiplier,
            description=f"Victory against level {enemy_level} enemy"
        )
        
        bond.battles_fought_together += 1
        bond.victories_together += 1
    
    
    @staticmethod
    def record_faint(bond: EchoBond) -> None:
        """
        Record Echo fainting (negative bond)
        
        Args:
            bond: Echo bond
        """
        BondingEngine.add_bond_points(
            bond,
            BondActivityType.FAINT,
            description="Echo fainted in battle"
        )
    
    
    @staticmethod
    def record_level_up(bond: EchoBond, new_level: int) -> None:
        """
        Record Echo level up
        
        Args:
            bond: Echo bond
            new_level: New level achieved
        """
        multiplier = 1.0 + (new_level / 100)
        BondingEngine.add_bond_points(
            bond,
            BondActivityType.LEVEL_UP,
            multiplier=multiplier,
            description=f"Reached level {new_level}"
        )
    
    
    @staticmethod
    def record_evolution(bond: EchoBond, old_name: str, new_name: str) -> None:
        """
        Record Echo evolution
        
        Args:
            bond: Echo bond
            old_name: Previous Echo form
            new_name: New evolved form
        """
        BondingEngine.add_bond_points(
            bond,
            BondActivityType.EVOLUTION,
            description=f"{old_name} evolved into {new_name}"
        )
    
    
    @staticmethod
    def gift_bond_item(bond: EchoBond, item_name: str, rarity: str = "common") -> int:
        """
        Gift bond item to Echo
        
        Args:
            bond: Echo bond
            item_name: Name of bond item
            rarity: Item rarity (common, uncommon, rare, epic, legendary)
            
        Returns:
            int: Bond points gained
        """
        rarity_mult = {
            'common': 1.0,
            'uncommon': 1.5,
            'rare': 2.5,
            'epic': 4.0,
            'legendary': 8.0,
        }.get(rarity, 1.0)
        
        return BondingEngine.add_bond_points(
            bond,
            BondActivityType.BOND_ITEM_GIFT,
            multiplier=rarity_mult,
            description=f"Received {rarity} bond item: {item_name}"
        )
    
    
    @staticmethod
    def get_stat_bonus(bond: EchoBond) -> Dict[str, float]:
        """
        Calculate stat bonuses from bonding
        
        Args:
            bond: Echo bond
            
        Returns:
            Dict: Stat multipliers by stat name
        """
        level = bond.current_bond_level()
        multiplier = BOND_STAT_MULTIPLIERS.get(level, 1.0)
        
        return {
            'hp': multiplier,
            'atk': multiplier,
            'def': multiplier,
            'sp_atk': multiplier,
            'sp_def': multiplier,
            'spd': multiplier,
        }
    
    
    @staticmethod
    def get_critical_bonus(bond: EchoBond) -> float:
        """
        Get critical hit rate bonus from bonding
        
        Args:
            bond: Echo bond
            
        Returns:
            float: Additional critical rate
        """
        level = bond.current_bond_level()
        return BOND_CRITICAL_BONUS.get(level, 0.0)
    
    
    @staticmethod
    def get_experience_multiplier(bond: EchoBond) -> float:
        """
        Get experience gain multiplier from bonding
        
        Args:
            bond: Echo bond
            
        Returns:
            float: Experience multiplier
        """
        level = bond.current_bond_level()
        return BOND_EXPERIENCE_MULTIPLIER.get(level, 1.0)
    
    
    @staticmethod
    def check_neglect_penalty(bond: EchoBond) -> int:
        """
        Check for neglect penalty and apply if needed
        
        Args:
            bond: Echo bond
            
        Returns:
            int: Penalty points if applied, 0 otherwise
        """
        days_since_interaction = (datetime.utcnow() - bond.last_interaction).days
        
        if days_since_interaction >= NEGLECT_THRESHOLD_DAYS:
            # 1 point per day over threshold
            penalty_days = days_since_interaction - NEGLECT_THRESHOLD_DAYS
            penalty = min(5, penalty_days)  # Max 5 point penalty
            
            BondingEngine.add_bond_points(
                bond,
                BondActivityType.NEGLECT,
                multiplier=penalty,
                description=f"Neglected for {days_since_interaction} days"
            )
            
            return penalty
        
        return 0
    
    
    @staticmethod
    def _get_level_for_points(points: int) -> BondLevel:
        """Get bond level for given points"""
        if points < 20:
            return BondLevel.STRANGER
        elif points < 40:
            return BondLevel.ACQUAINTANCE
        elif points < 80:
            return BondLevel.FRIEND
        elif points < 120:
            return BondLevel.CLOSE_FRIEND
        elif points < 160:
            return BondLevel.BEST_FRIEND
        elif points < 200:
            return BondLevel.SOULBOUND
        else:
            return BondLevel.KINDRED_SPIRIT
    
    
    @staticmethod
    def _check_milestones(bond: EchoBond, level: BondLevel) -> None:
        """Check for milestone achievements"""
        if bond.bond_points >= 5 and BondMilestone.FIRST_BATTLE not in bond.milestones_reached:
            bond.milestones_reached.append(BondMilestone.FIRST_BATTLE)
        
        if level == BondLevel.ACQUAINTANCE and BondMilestone.INITIAL_TRUST not in bond.milestones_reached:
            bond.milestones_reached.append(BondMilestone.INITIAL_TRUST)
        
        if level == BondLevel.FRIEND and BondMilestone.FRIENDSHIP_FORMED not in bond.milestones_reached:
            bond.milestones_reached.append(BondMilestone.FRIENDSHIP_FORMED)
        
        if level == BondLevel.CLOSE_FRIEND and BondMilestone.CLOSE_BOND not in bond.milestones_reached:
            bond.milestones_reached.append(BondMilestone.CLOSE_BOND)
            bond.can_evolve_by_bond = True
        
        if level == BondLevel.BEST_FRIEND and BondMilestone.BEST_FRIEND_UNLOCKED not in bond.milestones_reached:
            bond.milestones_reached.append(BondMilestone.BEST_FRIEND_UNLOCKED)
        
        if level == BondLevel.SOULBOUND and BondMilestone.SOULBOUND not in bond.milestones_reached:
            bond.milestones_reached.append(BondMilestone.SOULBOUND)
        
        if bond.bond_points >= 200 and BondMilestone.PERFECT_BOND not in bond.milestones_reached:
            bond.milestones_reached.append(BondMilestone.PERFECT_BOND)


# ============================================================================
# BOND UTILITY FUNCTIONS
# ============================================================================

def get_bond_description(bond: EchoBond) -> str:
    """
    Generate human-readable bond description
    
    Args:
        bond: Echo bond
        
    Returns:
        str: Description of bond status
    """
    level = bond.current_bond_level()
    level_name = {
        BondLevel.STRANGER: "just met",
        BondLevel.ACQUAINTANCE: "starting to know each other",
        BondLevel.FRIEND: "becoming good friends",
        BondLevel.CLOSE_FRIEND: "very close friends",
        BondLevel.BEST_FRIEND: "best friends",
        BondLevel.SOULBOUND: "soulbound companions",
        BondLevel.KINDRED_SPIRIT: "perfectly bonded",
    }
    
    return f"Bond Level {level.value.replace('_', ' ').title()} - {level_name[level]}"


def evolve_by_bond(bond: EchoBond) -> bool:
    """
    Check if Echo can evolve by bond level
    
    Args:
        bond: Echo bond
        
    Returns:
        bool: True if conditions met
    """
    level = bond.current_bond_level()
    return level in [
        BondLevel.CLOSE_FRIEND,
        BondLevel.BEST_FRIEND,
        BondLevel.SOULBOUND,
        BondLevel.KINDRED_SPIRIT,
    ]


def calculate_bond_touch_accuracy(bond: EchoBond, base_accuracy: float) -> float:
    """
    Calculate move accuracy boost from bond synchronization
    
    Args:
        bond: Echo bond
        base_accuracy: Base accuracy of move
        
    Returns:
        float: Adjusted accuracy
    """
    # Higher bond = better accuracy (up to 20% boost at max)
    bonus = bond.synchronization_level * 0.20
    adjusted = base_accuracy * (1.0 + bonus)
    
    return min(1.0, adjusted)  # Cap at 100%


def get_bond_stats_breakdown(bond: EchoBond) -> Dict[str, str]:
    """
    Get detailed bond statistics
    
    Args:
        bond: Echo bond
        
    Returns:
        Dict: Formatted statistics
    """
    return {
        'bond_level': bond.current_bond_level().value,
        'bond_points': f"{bond.bond_points}/{MAX_BOND}",
        'synchronization': f"{bond.synchronization_level * 100:.1f}%",
        'battles_together': str(bond.battles_fought_together),
        'victories': str(bond.victories_together),
        'distance_traveled': f"{bond.distance_traveled_together:.1f} units",
        'last_interaction': bond.last_interaction.isoformat(),
        'memories': str(len(bond.memories)),
        'milestones': ", ".join([m.value for m in bond.milestones_reached]) or "None yet",
    }
