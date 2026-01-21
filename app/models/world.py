"""
ChronoRift World Model
Represents the game world, rifts, and environmental state
"""

from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import uuid
import random

from app.models import db


class World(db.Model):
    """
    World Model - Global Game State
    
    Tracks the overall state of the game world, including
    global events, environmental changes, and world mutations.
    """
    
    __tablename__ = 'world'
    
    # Primary Key
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    
    # World State
    current_season = db.Column(db.String(50), default='spring', nullable=False)
    world_stability = db.Column(db.Float, default=1.0, nullable=False)  # 0.0 - 2.0
    dimensional_rifts_count = db.Column(db.Integer, default=0, nullable=False)
    corrupted_zones_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Global Events
    active_event = db.Column(db.String(200), nullable=True)
    event_progress = db.Column(db.Float, default=0.0, nullable=False)  # 0.0 - 1.0
    event_start_time = db.Column(db.DateTime, nullable=True)
    event_end_time = db.Column(db.DateTime, nullable=True)
    
    # Faction Control
    dominant_faction = db.Column(db.String(50), nullable=True)
    faction_control_percentage = db.Column(JSONB, default={}, nullable=False)  # {'faction_name': percentage}
    
    # Environmental Data
    temporal_distortion_level = db.Column(db.Float, default=0.0, nullable=False)  # 0.0 - 1.0
    void_energy_level = db.Column(db.Float, default=0.0, nullable=False)
    dimensional_echo_density = db.Column(db.Float, default=0.5, nullable=False)  # Affects spawn rates
    
    # Economic State
    global_inflation_rate = db.Column(db.Float, default=1.0, nullable=False)
    market_sentiment = db.Column(db.String(20), default='neutral', nullable=False)  # bullish, neutral, bearish
    rare_echo_market_value = db.Column(db.Integer, default=5000, nullable=False)
    
    # Metadata
    metadata = db.Column(JSONB, default={}, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_mutation = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    zones = db.relationship('Zone', back_populates='world', cascade='all, delete-orphan')
    rifts = db.relationship('Rift', back_populates='world', cascade='all, delete-orphan')
    
    def __repr__(self) -> str:
        return f'<World Season={self.current_season} Stability={self.world_stability}>'
    
    def to_dict(self) -> dict:
        """Convert World to dictionary representation"""
        return {
            'id': str(self.id),
            'current_season': self.current_season,
            'world_stability': self.world_stability,
            'dimensional_rifts_count': self.dimensional_rifts_count,
            'corrupted_zones_count': self.corrupted_zones_count,
            'active_event': self.active_event,
            'event_progress': self.event_progress,
            'dominant_faction': self.dominant_faction,
            'temporal_distortion_level': self.temporal_distortion_level,
            'void_energy_level': self.void_energy_level,
            'dimensional_echo_density': self.dimensional_echo_density,
            'global_inflation_rate': self.global_inflation_rate,
            'market_sentiment': self.market_sentiment,
            'zones_count': len(self.zones),
            'rifts_count': len(self.rifts)
        }
    
    def mutate_world(self) -> None:
        """Apply random mutations to the world state"""
        # Stability fluctuates
        stability_change = random.uniform(-0.15, 0.15)
        self.world_stability = max(0.0, min(2.0, self.world_stability + stability_change))
        
        # Temporal distortion increases with low stability
        if self.world_stability < 0.5:
            self.temporal_distortion_level = min(1.0, self.temporal_distortion_level + 0.1)
        elif self.world_stability > 1.5:
            self.temporal_distortion_level = max(0.0, self.temporal_distortion_level - 0.05)
        
        # Void energy fluctuates
        self.void_energy_level = max(0.0, min(1.0, self.void_energy_level + random.uniform(-0.1, 0.1)))
        
        # Echo density affects spawn rates
        self.dimensional_echo_density = max(0.1, min(2.0, self.dimensional_echo_density + random.uniform(-0.05, 0.05)))
        
        # Market sentiment based on world state
        if self.world_stability > 1.5:
            self.market_sentiment = 'bullish'
        elif self.world_stability < 0.5:
            self.market_sentiment = 'bearish'
        else:
            self.market_sentiment = 'neutral'
        
        self.last_mutation = datetime.utcnow()
    
    def progress_event(self, amount: float) -> bool:
        """
        Progress the current event
        
        Args:
            amount: Progress amount (0.0 - 1.0)
            
        Returns:
            True if event completed, False otherwise
        """
        if not self.active_event:
            return False
        
        self.event_progress = min(1.0, self.event_progress + amount)
        
        if self.event_progress >= 1.0:
            self.complete_event()
            return True
        
        return False
    
    def complete_event(self) -> None:
        """Mark the current event as completed"""
        self.active_event = None
        self.event_progress = 0.0
        self.event_start_time = None
        self.event_end_time = None
    
    def start_new_event(self, event_name: str, duration_hours: int = 24) -> None:
        """
        Start a new global event
        
        Args:
            event_name: Name of the event
            duration_hours: Duration of the event in hours
        """
        self.active_event = event_name
        self.event_progress = 0.0
        self.event_start_time = datetime.utcnow()
        self.event_end_time = datetime.utcnow() + timedelta(hours=duration_hours)


class Zone(db.Model):
    """
    Zone Model - Regional World Division
    
    The world is divided into zones, each with unique characteristics,
    Echo spawns, and rift density.
    """
    
    __tablename__ = 'zones'
    
    # Primary Key
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    
    # World Reference
    world_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('world.id'),
        nullable=False,
        index=True
    )
    
    # Zone Information
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    zone_type = db.Column(
        db.String(50),
        nullable=False
    )  # forest, desert, mountain, cave, city, underwater, dimensional_rift
    
    # Visual Properties
    background_url = db.Column(db.String(500), nullable=True)
    background_color = db.Column(db.String(7), nullable=True)  # Hex color
    
    # Geography & Coordinates
    region = db.Column(db.String(100), nullable=False)  # Northern Wastes, Temporal Caverns, etc.
    x_coordinate = db.Column(db.Integer, nullable=False)
    y_coordinate = db.Column(db.Integer, nullable=False)
    recommended_level = db.Column(db.Integer, default=1, nullable=False)
    
    # Ecological Data
    temperature = db.Column(db.String(50), nullable=True)  # Hot, Cold, Moderate
    precipitation = db.Column(db.String(50), nullable=True)  # High, Low, Moderate
    primary_element = db.Column(db.String(20), nullable=True)  # Fire, Water, Earth, Wind, etc.
    
    # Rift Properties
    rift_density = db.Column(db.Float, default=0.3, nullable=False)  # 0.0 - 1.0
    base_rift_spawn_time = db.Column(db.Integer, default=300, nullable=False)  # seconds
    max_rifts_concurrent = db.Column(db.Integer, default=10, nullable=False)
    
    # Echo Spawning
    spawn_pool = db.Column(ARRAY(UUID(as_uuid=True)), default=[], nullable=False)  # Echo IDs that spawn here
    spawn_rates = db.Column(JSONB, default={}, nullable=False)  # {echo_id: rate}
    
    # State & Corruption
    corruption_level = db.Column(db.Float, default=0.0, nullable=False)  # 0.0 - 1.0
    is_corrupted = db.Column(db.Boolean, default=False, nullable=False, index=True)
    corruption_spread_rate = db.Column(db.Float, default=0.01, nullable=False)
    
    # Faction Control
    controlling_faction_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('factions.id'),
        nullable=True
    )
    faction_control_percentage = db.Column(db.Float, default=0.0, nullable=False)  # 0.0 - 100.0
    
    # Resources & Activities
    available_activities = db.Column(ARRAY(db.String(50)), default=[], nullable=False)
    # Examples: exploration, fishing, mining, monster_hunting, shrine_praying
    
    # Metadata
    metadata = db.Column(JSONB, default={}, nullable=False)
    lore = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    world = db.relationship('World', back_populates='zones')
    rifts = db.relationship('Rift', back_populates='zone', cascade='all, delete-orphan')
    controlling_faction = db.relationship('Faction')
    
    def __repr__(self) -> str:
        return f'<Zone {self.name} ({self.zone_type})>'
    
    def to_dict(self, include_echoes: bool = False) -> dict:
        """Convert Zone to dictionary representation"""
        data = {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'zone_type': self.zone_type,
            'region': self.region,
            'coordinates': {'x': self.x_coordinate, 'y': self.y_coordinate},
            'recommended_level': self.recommended_level,
            'rift_density': self.rift_density,
            'corruption_level': self.corruption_level,
            'is_corrupted': self.is_corrupted,
            'controlling_faction': self.controlling_faction.name if self.controlling_faction else None,
            'faction_control': self.faction_control_percentage,
            'background_color': self.background_color,
            'available_activities': self.available_activities
        }
        
        if include_echoes:
            data['spawn_pool'] = [str(echo_id) for echo_id in self.spawn_pool]
        
        return data
    
    def spread_corruption(self) -> None:
        """Spread corruption in the zone"""
        if not self.is_corrupted:
            return
        
        # Corruption spreads gradually
        self.corruption_level = min(1.0, self.corruption_level + self.corruption_spread_rate)
    
    def heal_corruption(self, amount: float) -> None:
        """
        Reduce corruption in the zone
        
        Args:
            amount: Amount to heal (0.0 - 1.0)
        """
        self.corruption_level = max(0.0, self.corruption_level - amount)
        
        if self.corruption_level == 0.0:
            self.is_corrupted = False
    
    def update_faction_control(self, faction_id: UUID, percentage: float) -> None:
        """
        Update faction control of the zone
        
        Args:
            faction_id: UUID of the faction
            percentage: Control percentage (0.0 - 100.0)
        """
        self.controlling_faction_id = faction_id
        self.faction_control_percentage = max(0.0, min(100.0, percentage))
    
    def get_echo_spawn_rate(self, echo_id: UUID) -> float:
        """
        Get the spawn rate for a specific Echo in this zone
        
        Args:
            echo_id: UUID of the Echo
            
        Returns:
            Spawn rate multiplier
        """
        return self.spawn_rates.get(str(echo_id), 0.0)
    
    def can_spawn_rift(self) -> bool:
        """Check if a rift can spawn in this zone"""
        return random.random() < self.rift_density


class Rift(db.Model):
    """
    Rift Model - Dimensional Tear
    
    Rifts are unstable tears in reality that spawn Echoes
    and can be stabilized or manipulated by players.
    """
    
    __tablename__ = 'rifts'
    
    # Primary Key
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    
    # World & Zone Reference
    world_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('world.id'),
        nullable=False,
        index=True
    )
    zone_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('zones.id'),
        nullable=False,
        index=True
    )
    
    # Rift Properties
    name = db.Column(db.String(100), nullable=False)
    rift_type = db.Column(
        db.String(50),
        default='standard',
        nullable=False
    )  # standard, temporal, void, chaotic, resonant
    stability = db.Column(db.Float, default=0.5, nullable=False)  # 0.0 - 1.0
    power_level = db.Column(db.Integer, default=10, nullable=False)  # Difficulty multiplier
    
    # Dimensional Properties
    dimensional_affinity = db.Column(db.String(20), nullable=False)  # temporal, spatial, ethereal, etc.
    energy_level = db.Column(db.Float, default=1.0, nullable=False)  # 0.0 - 2.0
    
    # Location & Coordinates
    x_coordinate = db.Column(db.Float, nullable=False)
    y_coordinate = db.Column(db.Float, nullable=False)
    
    # Echo Information
    spawned_echoes = db.relationship('Echo', secondary='rift_echoes', back_populates='spawned_in_rifts')
    primary_echo_type = db.Column(db.String(100), nullable=True)  # Most common Echo type in this rift
    echo_variety = db.Column(db.Integer, default=3, nullable=False)  # Number of different Echo types
    
    # State & Lifecycle
    state = db.Column(
        db.String(20),
        default='active',
        nullable=False,
        index=True
    )  # active, destabilizing, collapsing, sealed
    stability_decay_rate = db.Column(db.Float, default=0.01, nullable=False)
    
    # Temporal Properties
    spawn_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    expected_collapse_time = db.Column(db.DateTime, nullable=False)
    actual_collapse_time = db.Column(db.DateTime, nullable=True)
    
    # Player Interaction
    visit_count = db.Column(db.Integer, default=0, nullable=False)
    stabilization_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Rewards
    stability_reward = db.Column(db.Integer, default=100, nullable=False)
    exploration_reward = db.Column(db.Integer, default=50, nullable=False)
    
    # Metadata
    metadata = db.Column(JSONB, default={}, nullable=False)
    lore = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    world = db.relationship('World', back_populates='rifts')
    zone = db.relationship('Zone', back_populates='rifts')
    
    def __repr__(self) -> str:
        return f'<Rift {self.name} (Power: {self.power_level})>'
    
    def to_dict(self, include_echoes: bool = False) -> dict:
        """Convert Rift to dictionary representation"""
        data = {
            'id': str(self.id),
            'name': self.name,
            'zone_id': str(self.zone_id),
            'rift_type': self.rift_type,
            'stability': self.stability,
            'power_level': self.power_level,
            'dimensional_affinity': self.dimensional_affinity,
            'energy_level': self.energy_level,
            'coordinates': {'x': self.x_coordinate, 'y': self.y_coordinate},
            'state': self.state,
            'visit_count': self.visit_count,
            'stabilization_count': self.stabilization_count,
            'rewards': {
                'stability': self.stability_reward,
                'exploration': self.exploration_reward
            },
            'spawn_time': self.spawn_time.isoformat() if self.spawn_time else None,
            'expected_collapse': self.expected_collapse_time.isoformat() if self.expected_collapse_time else None
        }
        
        if include_echoes:
            data['spawned_echoes'] = [str(echo.id) for echo in self.spawned_echoes]
        
        return data
    
    def decay_stability(self) -> None:
        """Decay rift stability over time"""
        self.stability = max(0.0, self.stability - self.stability_decay_rate)
        
        if self.stability < 0.3:
            self.state = 'destabilizing'
        elif self.stability <= 0.0:
            self.state = 'collapsing'
            self.actual_collapse_time = datetime.utcnow()
    
    def stabilize(self, amount: float = 0.1) -> None:
        """
        Stabilize the rift
        
        Args:
            amount: Amount to stabilize (0.0 - 1.0)
        """
        self.stability = min(1.0, self.stability + amount)
        self.stabilization_count += 1
        
        if self.stability > 0.5:
            self.state = 'active'
    
    def open_rift(self, amount: float = 0.2) -> None:
        """
        Open/enlarge the rift (increase energy)
        
        Args:
            amount: Amount to open
        """
        self.energy_level = min(2.0, self.energy_level + amount)
        self.power_level = int(10 + (self.energy_level - 1.0) * 50)
        self.stability = max(0.0, self.stability - 0.05)  # Opening increases instability
    
    def record_visit(self) -> None:
        """Record a player visit to the rift"""
        self.visit_count += 1
    
    def is_collapsing(self) -> bool:
        """Check if rift is actively collapsing"""
        return self.state == 'collapsing' or datetime.utcnow() > self.expected_collapse_time
    
    def is_sealed(self) -> bool:
        """Check if rift is sealed"""
        return self.state == 'sealed'
