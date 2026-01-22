"""
ChronoRift World Mutator
Environmental changes, world state mutations, and anomaly effects
"""

import random
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class AnomalyType(Enum):
    """Types of environmental anomalies"""
    TIME_DISTORTION = "time_distortion"     # Time moves differently
    SPATIAL_WARPING = "spatial_warping"     # Movement/navigation affected
    ELEMENT_SURGE = "element_surge"         # Elemental damage in area
    GRAVITY_FLUX = "gravity_flux"           # Gravity changes
    TEMPORAL_ECHO = "temporal_echo"         # Echoes from past appear
    VOID_CORRUPTION = "void_corruption"     # Corruption spreads
    REALITY_FRACTURE = "reality_fracture"   # Stability breaks down


class EnvironmentEffect(Enum):
    """Persistent environmental effects"""
    RAIN = "rain"                   # Reduces accuracy, reduces fire damage
    STORM = "storm"                 # High winds, Thunder damage risk
    FOG = "fog"                     # Reduced visibility/accuracy
    VOLCANIC_ASH = "volcanic_ash"   # Fire damage, breath effects
    ACID_RAIN = "acid_rain"         # Continuous poison damage
    AURORA = "aurora"               # Light element bonus
    ECLIPSE = "eclipse"             # Dark element bonus
    BLIZZARD = "blizzard"           # Ice damage, movement penalty


class WorldStability(Enum):
    """World stability tier"""
    PERFECT = "perfect"             # 1.0 stability
    STABLE = "stable"               # 0.8-1.0 stability
    NORMAL = "normal"               # 0.6-0.8 stability
    UNSTABLE = "unstable"           # 0.4-0.6 stability
    CHAOTIC = "chaotic"             # 0.2-0.4 stability
    CATASTROPHIC = "catastrophic"   # 0.0-0.2 stability


class MutationSeverity(Enum):
    """Mutation severity level"""
    MINOR = "minor"                 # Small changes
    MODERATE = "moderate"           # Noticeable changes
    MAJOR = "major"                 # Significant changes
    CATACLYSMIC = "cataclysmic"     # World-altering


# Stability decay per day (world returns to baseline)
STABILITY_RECOVERY_RATE = 0.05  # 5% per day toward 0.6 baseline

# Anomaly effect magnitude by severity
ANOMALY_MAGNITUDE = {
    MutationSeverity.MINOR: 0.1,
    MutationSeverity.MODERATE: 0.25,
    MutationSeverity.MAJOR: 0.50,
    MutationSeverity.CATACLYSMIC: 1.0,
}

# Effect duration (hours)
EFFECT_DURATIONS = {
    AnomalyType.TIME_DISTORTION: (2, 8),
    AnomalyType.SPATIAL_WARPING: (1, 4),
    AnomalyType.ELEMENT_SURGE: (0.5, 2),
    AnomalyType.GRAVITY_FLUX: (1, 3),
    AnomalyType.TEMPORAL_ECHO: (1, 6),
    AnomalyType.VOID_CORRUPTION: (4, 24),
    AnomalyType.REALITY_FRACTURE: (2, 12),
}

# Environment effect benefits/drawbacks
ENVIRONMENT_MODIFIERS = {
    EnvironmentEffect.RAIN: {
        'accuracy': 0.85,
        'fire_damage': 0.75,
        'water_damage': 1.25,
        'visibility': 0.9,
    },
    EnvironmentEffect.STORM: {
        'accuracy': 0.70,
        'wind_damage': 1.50,
        'electric_damage': 1.25,
        'movement_speed': 0.85,
    },
    EnvironmentEffect.FOG: {
        'accuracy': 0.80,
        'visibility': 0.60,
        'ghost_effectiveness': 1.25,
    },
    EnvironmentEffect.VOLCANIC_ASH: {
        'fire_damage': 1.25,
        'breath_attacks': 1.15,
        'visibility': 0.75,
    },
    EnvironmentEffect.ACID_RAIN: {
        'poison_damage': 1.50,
        'metal_defense': 0.90,
        'continuous_damage': 5,  # Per turn
    },
    EnvironmentEffect.AURORA: {
        'light_damage': 1.25,
        'light_resistance': 1.15,
        'healing': 1.10,
    },
    EnvironmentEffect.ECLIPSE: {
        'dark_damage': 1.25,
        'dark_resistance': 1.15,
        'ghost_effectiveness': 1.20,
    },
    EnvironmentEffect.BLIZZARD: {
        'ice_damage': 1.50,
        'movement_speed': 0.70,
        'cold_resistance': 1.25,
    },
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Anomaly:
    """Active anomaly affecting world"""
    id: str
    anomaly_type: AnomalyType
    severity: MutationSeverity
    zone_id: str
    position: Tuple[float, float]     # x, y coordinates
    radius: float                      # Affected area
    created_at: datetime
    expires_at: datetime
    active: bool = True
    intensity: float = 1.0             # 0.0-1.0 current intensity


@dataclass
class EnvironmentalState:
    """Zone environmental conditions"""
    zone_id: str
    current_effect: Optional[EnvironmentEffect] = None
    effect_intensity: float = 1.0      # 0.0-1.0
    effect_expires_at: Optional[datetime] = None
    base_stability: float = 0.6        # Zone stability baseline
    current_stability: float = 0.6     # Real-time stability
    last_mutation: Optional[datetime] = None
    corruption_level: float = 0.0      # 0.0-1.0 void corruption


@dataclass
class WorldState:
    """Global world state"""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    global_stability: float = 0.6      # 0.0-1.0
    active_anomalies: List[Anomaly] = field(default_factory=list)
    zone_states: Dict[str, EnvironmentalState] = field(default_factory=dict)
    anomaly_count_today: int = 0
    rifts_open: int = 0
    days_since_last_mutation: int = 0


# ============================================================================
# WORLD MUTATOR ENGINE
# ============================================================================

class WorldMutator:
    """Environmental changes and world state mutation system"""
    
    @staticmethod
    def update_world_stability(
        world_state: WorldState,
        time_elapsed: float  # seconds
    ) -> None:
        """
        Update global world stability over time
        Returns toward baseline (0.6) naturally
        
        Args:
            world_state: Current world state
            time_elapsed: Time since last update (seconds)
        """
        hours_elapsed = time_elapsed / 3600
        
        # Baseline is 0.6 (normal/stable)
        baseline = 0.6
        distance_from_baseline = world_state.global_stability - baseline
        
        # Recover toward baseline
        recovery = STABILITY_RECOVERY_RATE * hours_elapsed
        if distance_from_baseline > 0:
            world_state.global_stability = max(baseline, world_state.global_stability - recovery)
        elif distance_from_baseline < 0:
            world_state.global_stability = min(baseline, world_state.global_stability + recovery)
        
        # Clamp to 0-1
        world_state.global_stability = max(0.0, min(1.0, world_state.global_stability))
    
    
    @staticmethod
    def mutate_anomaly(
        world_state: WorldState,
        zone_id: str,
        position: Tuple[float, float],
        player_level: int = 50
    ) -> Optional[Anomaly]:
        """
        Spawn anomaly in zone
        
        Args:
            world_state: Current world state
            zone_id: Zone where anomaly spawns
            position: x, y coordinates
            player_level: Player level (affects severity)
            
        Returns:
            Anomaly: Created anomaly, or None if spawn fails
        """
        # Check probability based on stability
        spawn_chance = 1.0 - world_state.global_stability
        if random.random() > spawn_chance:
            return None
        
        # Generate anomaly properties
        anomaly_type = random.choice(list(AnomalyType))
        
        # Severity scales with instability and player level
        stability_factor = 1.0 - world_state.global_stability
        level_factor = player_level / 100
        severity_roll = random.random() * (stability_factor + level_factor)
        
        if severity_roll < 0.25:
            severity = MutationSeverity.MINOR
        elif severity_roll < 0.50:
            severity = MutationSeverity.MODERATE
        elif severity_roll < 0.75:
            severity = MutationSeverity.MAJOR
        else:
            severity = MutationSeverity.CATACLYSMIC
        
        # Get duration
        min_dur, max_dur = EFFECT_DURATIONS.get(anomaly_type, (1, 4))
        duration_hours = random.uniform(min_dur, max_dur)
        
        # Create anomaly
        anomaly = Anomaly(
            id=str(random.randint(100000, 999999)),
            anomaly_type=anomaly_type,
            severity=severity,
            zone_id=zone_id,
            position=position,
            radius=50 + (ANOMALY_MAGNITUDE[severity] * 100),
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=duration_hours),
            intensity=ANOMALY_MAGNITUDE[severity],
        )
        
        world_state.active_anomalies.append(anomaly)
        world_state.anomaly_count_today += 1
        
        return anomaly
    
    
    @staticmethod
    def apply_environmental_effect(
        zone_state: EnvironmentalState,
        effect: EnvironmentEffect,
        duration_minutes: int = 30
    ) -> None:
        """
        Apply environmental effect to zone
        
        Args:
            zone_state: Zone environmental state
            effect: Effect type
            duration_minutes: Effect duration
        """
        zone_state.current_effect = effect
        zone_state.effect_intensity = 1.0
        zone_state.effect_expires_at = datetime.utcnow() + timedelta(minutes=duration_minutes)
    
    
    @staticmethod
    def get_environment_modifiers(zone_state: EnvironmentalState) -> Dict[str, float]:
        """
        Get all active modifier multipliers for zone
        
        Args:
            zone_state: Zone environmental state
            
        Returns:
            Dict: Modifier name -> multiplier
        """
        modifiers = {}
        
        if zone_state.current_effect:
            effect_mods = ENVIRONMENT_MODIFIERS.get(zone_state.current_effect, {})
            
            # Apply intensity scaling
            for key, value in effect_mods.items():
                if isinstance(value, (int, float)) and key not in ['continuous_damage']:
                    # Interpolate between 1.0 (no effect) and the value (full effect)
                    if value > 1.0:
                        modifiers[key] = 1.0 + ((value - 1.0) * zone_state.effect_intensity)
                    else:
                        modifiers[key] = 1.0 - ((1.0 - value) * zone_state.effect_intensity)
                else:
                    modifiers[key] = value
        
        # Stability-based accuracy reduction
        accuracy_penalty = (1.0 - zone_state.current_stability) * 0.15
        modifiers['accuracy'] = modifiers.get('accuracy', 1.0) * (1.0 - accuracy_penalty)
        
        return modifiers
    
    
    @staticmethod
    def update_anomalies(world_state: WorldState) -> List[Anomaly]:
        """
        Update active anomalies, remove expired ones
        
        Args:
            world_state: Current world state
            
        Returns:
            List: Anomalies that just expired
        """
        expired = []
        active = []
        
        for anomaly in world_state.active_anomalies:
            if datetime.utcnow() > anomaly.expires_at:
                anomaly.active = False
                expired.append(anomaly)
            else:
                # Fade intensity as expires_at approaches
                time_remaining = (anomaly.expires_at - datetime.utcnow()).total_seconds()
                total_duration = (anomaly.expires_at - anomaly.created_at).total_seconds()
                anomaly.intensity = max(0.0, time_remaining / total_duration)
                active.append(anomaly)
        
        world_state.active_anomalies = active
        return expired
    
    
    @staticmethod
    def induce_void_corruption(
        zone_state: EnvironmentalState,
        amount: float = 0.1
    ) -> None:
        """
        Increase zone corruption from void anomalies
        
        Args:
            zone_state: Zone to corrupt
            amount: Amount to increase (0-1)
        """
        zone_state.corruption_level = min(1.0, zone_state.corruption_level + amount)
        
        # Corruption reduces stability
        stability_penalty = zone_state.corruption_level * 0.3
        zone_state.current_stability = zone_state.base_stability * (1.0 - stability_penalty)
    
    
    @staticmethod
    def cleanse_corruption(
        zone_state: EnvironmentalState,
        amount: float = 0.05
    ) -> None:
        """
        Reduce zone corruption
        
        Args:
            zone_state: Zone to cleanse
            amount: Amount to reduce
        """
        zone_state.corruption_level = max(0.0, zone_state.corruption_level - amount)
        
        # Recalculate stability
        stability_penalty = zone_state.corruption_level * 0.3
        zone_state.current_stability = zone_state.base_stability * (1.0 - stability_penalty)
    
    
    @staticmethod
    def get_stability_tier(stability: float) -> WorldStability:
        """
        Get stability tier from value
        
        Args:
            stability: Stability value (0-1)
            
        Returns:
            WorldStability: Current tier
        """
        if stability >= 0.95:
            return WorldStability.PERFECT
        elif stability >= 0.8:
            return WorldStability.STABLE
        elif stability >= 0.6:
            return WorldStability.NORMAL
        elif stability >= 0.4:
            return WorldStability.UNSTABLE
        elif stability >= 0.2:
            return WorldStability.CHAOTIC
        else:
            return WorldStability.CATASTROPHIC
    
    
    @staticmethod
    def calculate_zone_difficulty_bonus(zone_state: EnvironmentalState) -> float:
        """
        Calculate difficulty multiplier for encounters in zone
        
        Args:
            zone_state: Zone environmental state
            
        Returns:
            float: Difficulty multiplier
        """
        # Instability increases difficulty
        instability = 1.0 - zone_state.current_stability
        
        # Corruption increases difficulty
        corruption_mult = 1.0 + (zone_state.corruption_level * 0.5)
        
        return 1.0 + (instability * 0.5) * corruption_mult


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_anomaly_description(anomaly: Anomaly) -> str:
    """
    Get human-readable anomaly description
    
    Args:
        anomaly: Anomaly to describe
        
    Returns:
        str: Description
    """
    type_names = {
        AnomalyType.TIME_DISTORTION: "temporal anomaly",
        AnomalyType.SPATIAL_WARPING: "spatial distortion",
        AnomalyType.ELEMENT_SURGE: "elemental surge",
        AnomalyType.GRAVITY_FLUX: "gravity fluctuation",
        AnomalyType.TEMPORAL_ECHO: "temporal echo",
        AnomalyType.VOID_CORRUPTION: "void corruption",
        AnomalyType.REALITY_FRACTURE: "reality fracture",
    }
    
    severity_names = {
        MutationSeverity.MINOR: "Minor",
        MutationSeverity.MODERATE: "Moderate",
        MutationSeverity.MAJOR: "Major",
        MutationSeverity.CATACLYSMIC: "Cataclysmic",
    }
    
    return f"{severity_names[anomaly.severity]} {type_names[anomaly.anomaly_type]} - {anomaly.intensity*100:.0f}% intensity"


def get_environment_description(zone_state: EnvironmentalState) -> str:
    """
    Get zone environmental description
    
    Args:
        zone_state: Zone state
        
    Returns:
        str: Description
    """
    if not zone_state.current_effect:
        return "Clear weather"
    
    effect_names = {
        EnvironmentEffect.RAIN: "Rainy",
        EnvironmentEffect.STORM: "Stormy",
        EnvironmentEffect.FOG: "Foggy",
        EnvironmentEffect.VOLCANIC_ASH: "Volcanic ash falling",
        EnvironmentEffect.ACID_RAIN: "Acid rain",
        EnvironmentEffect.AURORA: "Aurora borealis",
        EnvironmentEffect.ECLIPSE: "Solar eclipse",
        EnvironmentEffect.BLIZZARD: "Blizzard",
    }
    
    return effect_names.get(zone_state.current_effect, "Unknown weather")


def calculate_anomaly_threat_level(anomaly: Anomaly) -> int:
    """
    Calculate threat level (1-10) for anomaly
    
    Args:
        anomaly: Anomaly to evaluate
        
    Returns:
        int: Threat level 1-10
    """
    severity_points = {
        MutationSeverity.MINOR: 2,
        MutationSeverity.MODERATE: 4,
        MutationSeverity.MAJOR: 7,
        MutationSeverity.CATACLYSMIC: 10,
    }
    
    base_threat = severity_points.get(anomaly.severity, 5)
    
    # Void corruption is most dangerous
    if anomaly.anomaly_type == AnomalyType.VOID_CORRUPTION:
        base_threat = min(10, base_threat + 2)
    
    # Reality fracture is unpredictable
    if anomaly.anomaly_type == AnomalyType.REALITY_FRACTURE:
        base_threat = min(10, base_threat + 1)
    
    return min(10, max(1, int(base_threat)))
