"""
ChronoRift Echo Model
Represents dimensional creatures that Riftwalkers can bond with
"""

from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import uuid

from app.models import db


class Echo(db.Model):
    """
    Echo Model - Dimensional Creature
    
    Echoes are rare creatures that leak through from collapsed alternate timelines.
    Each Echo has unique abilities, stats, and personality traits.
    """
    
    __tablename__ = 'echoes'
    
    # Primary Key
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    
    # Basic Information
    name = db.Column(db.String(64), nullable=False, index=True)
    species = db.Column(db.String(64), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    lore = db.Column(db.Text, nullable=True)
    
    # Visual & Design
    sprite_url = db.Column(db.String(500), nullable=False)
    icon_url = db.Column(db.String(500), nullable=True)
    color_primary = db.Column(db.String(7), nullable=True)  # Hex color
    color_secondary = db.Column(db.String(7), nullable=True)  # Hex color
    silhouette = db.Column(db.String(20), nullable=False)  # Shape identifier for visuals
    
    # Dimensional Properties
    dimensional_affinity = db.Column(
        db.String(20),
        nullable=False,
        index=True
    )  # temporal, spatial, ethereal, primordial, quantum, void
    dimensional_origin = db.Column(db.String(200), nullable=True)  # Timeline it came from
    rift_rarity = db.Column(
        db.String(20),
        default='common',
        nullable=False,
        index=True
    )  # common, uncommon, rare, epic, legendary
    
    # Combat Stats (Base stats - scale with level and bonding)
    base_hp = db.Column(db.Integer, default=50, nullable=False)
    base_attack = db.Column(db.Integer, default=10, nullable=False)
    base_defense = db.Column(db.Integer, default=10, nullable=False)
    base_speed = db.Column(db.Integer, default=10, nullable=False)
    base_special_attack = db.Column(db.Integer, default=10, nullable=False)
    base_special_defense = db.Column(db.Integer, default=10, nullable=False)
    
    # Growth Rates (how much stats scale per level)
    hp_growth = db.Column(db.Float, default=1.1, nullable=False)
    attack_growth = db.Column(db.Float, default=1.05, nullable=False)
    defense_growth = db.Column(db.Float, default=1.05, nullable=False)
    speed_growth = db.Column(db.Float, default=1.03, nullable=False)
    special_attack_growth = db.Column(db.Float, default=1.05, nullable=False)
    special_defense_growth = db.Column(db.Float, default=1.05, nullable=False)
    
    # Personality & Traits
    personality_traits = db.Column(ARRAY(db.String(50)), default=[], nullable=False)
    # Examples: aggressive, timid, curious, loyal, mischievous, ancient, protective
    
    # Bonding Information
    bonding_difficulty = db.Column(db.Integer, default=5, nullable=False)  # 1-10 scale
    bonding_description = db.Column(db.Text, nullable=True)
    bond_unlock_level = db.Column(db.Integer, default=5, nullable=False)  # Level needed to unlock special ability
    
    # Abilities & Skills
    ability_name = db.Column(db.String(64), nullable=True)
    ability_description = db.Column(db.Text, nullable=True)
    ability_type = db.Column(db.String(20), nullable=True)  # attack, defense, support, utility
    ability_power = db.Column(db.Integer, default=50, nullable=True)
    ability_accuracy = db.Column(db.Float, default=1.0, nullable=True)  # 0.0 - 2.0
    ability_cooldown = db.Column(db.Integer, default=2, nullable=True)  # turns
    
    # Secondary Ability (unlocked at higher bond levels)
    secondary_ability_name = db.Column(db.String(64), nullable=True)
    secondary_ability_description = db.Column(db.Text, nullable=True)
    secondary_ability_type = db.Column(db.String(20), nullable=True)
    secondary_ability_power = db.Column(db.Integer, default=70, nullable=True)
    secondary_ability_unlock_bond_level = db.Column(db.Integer, default=8, nullable=True)
    
    # Type Effectiveness
    strong_against = db.Column(ARRAY(db.String(20)), default=[], nullable=False)  # Dimensional affinities
    weak_to = db.Column(ARRAY(db.String(20)), default=[], nullable=False)
    resists = db.Column(ARRAY(db.String(20)), default=[], nullable=False)
    
    # Rarity & Spawning
    spawn_zones = db.Column(ARRAY(db.String(100)), default=[], nullable=False)
    spawn_probability = db.Column(db.Float, default=0.1, nullable=False)  # 0.0 - 1.0
    max_level = db.Column(db.Integer, default=100, nullable=False)
    evolution_chain = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('echoes.id'),
        nullable=True
    )  # ID of evolved form, if applicable
    
    # Capture Information
    capture_exp_reward = db.Column(db.Integer, default=100, nullable=False)
    capture_currency_reward = db.Column(db.Integer, default=50, nullable=False)
    pokedex_entry = db.Column(db.Integer, nullable=True, unique=True)  # Dex number
    
    # Economic Value
    market_value = db.Column(db.Integer, default=500, nullable=False)
    resale_multiplier = db.Column(db.Float, default=0.7, nullable=False)  # Percentage of market value
    breeding_value = db.Column(db.Integer, default=0, nullable=False)  # Cost to breed (0 = not breedable)
    
    # Ecological Data
    diet = db.Column(db.String(50), nullable=True)  # What it feeds on
    habitat = db.Column(db.String(100), nullable=True)
    lifespan = db.Column(db.String(50), nullable=True)
    
    # Metadata
    is_legendary = db.Column(db.Boolean, default=False, nullable=False, index=True)
    is_event_exclusive = db.Column(db.Boolean, default=False, nullable=False)
    requires_special_item = db.Column(db.String(100), nullable=True)  # Item needed to capture
    
    # JSON data for extensibility
    metadata = db.Column(JSONB, default={}, nullable=False)
    balance_notes = db.Column(db.Text, nullable=True)  # Developer notes
    
    # Statistics & Tracking
    total_captured = db.Column(db.Integer, default=0, nullable=False)
    times_bonded = db.Column(db.Integer, default=0, nullable=False)
    average_bonding_level = db.Column(db.Float, default=0.0, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    riftwalkers = db.relationship(
        'Riftwalker',
        secondary='riftwalker_echoes',
        back_populates='echoes'
    )
    bondings = db.relationship('Bonding', back_populates='echo', cascade='all, delete-orphan')
    evolutions = db.relationship('Echo', remote_side=[evolution_chain])
    spawned_in_rifts = db.relationship('Rift', secondary='rift_echoes', back_populates='spawned_echoes')
    
    def __repr__(self) -> str:
        return f'<Echo {self.name} ({self.species})>'
    
    def to_dict(self, include_metadata: bool = False) -> dict:
        """
        Convert Echo to dictionary representation
        
        Args:
            include_metadata: Include developer metadata
            
        Returns:
            Dictionary representation of Echo
        """
        data = {
            'id': str(self.id),
            'name': self.name,
            'species': self.species,
            'description': self.description,
            'lore': self.lore,
            'sprite_url': self.sprite_url,
            'icon_url': self.icon_url,
            'silhouette': self.silhouette,
            'dimensional_affinity': self.dimensional_affinity,
            'dimensional_origin': self.dimensional_origin,
            'rift_rarity': self.rift_rarity,
            'personality_traits': self.personality_traits,
            'bonding_difficulty': self.bonding_difficulty,
            'ability': {
                'name': self.ability_name,
                'description': self.ability_description,
                'type': self.ability_type,
                'power': self.ability_power,
                'accuracy': self.ability_accuracy,
                'cooldown': self.ability_cooldown
            },
            'secondary_ability': {
                'name': self.secondary_ability_name,
                'description': self.secondary_ability_description,
                'type': self.secondary_ability_type,
                'power': self.secondary_ability_power,
                'unlock_bond_level': self.secondary_ability_unlock_bond_level
            },
            'base_stats': {
                'hp': self.base_hp,
                'attack': self.base_attack,
                'defense': self.base_defense,
                'speed': self.base_speed,
                'special_attack': self.base_special_attack,
                'special_defense': self.base_special_defense
            },
            'growth_rates': {
                'hp': self.hp_growth,
                'attack': self.attack_growth,
                'defense': self.defense_growth,
                'speed': self.speed_growth,
                'special_attack': self.special_attack_growth,
                'special_defense': self.special_defense_growth
            },
            'type_effectiveness': {
                'strong_against': self.strong_against,
                'weak_to': self.weak_to,
                'resists': self.resists
            },
            'spawn_zones': self.spawn_zones,
            'spawn_probability': self.spawn_probability,
            'max_level': self.max_level,
            'capture_rewards': {
                'exp': self.capture_exp_reward,
                'currency': self.capture_currency_reward
            },
            'market_value': self.market_value,
            'is_legendary': self.is_legendary,
            'is_event_exclusive': self.is_event_exclusive,
            'total_captured': self.total_captured,
            'times_bonded': self.times_bonded,
            'average_bonding_level': self.average_bonding_level
        }
        
        if include_metadata:
            data.update({
                'metadata': self.metadata,
                'balance_notes': self.balance_notes,
                'requires_special_item': self.requires_special_item,
                'breeding_value': self.breeding_value
            })
        
        return data
    
    def calculate_stats_at_level(self, level: int) -> dict:
        """
        Calculate Echo stats at a specific level
        
        Args:
            level: The level to calculate stats for
            
        Returns:
            Dictionary of stats at the given level
        """
        level_multiplier = level / 100  # Scale from 1 to 100
        
        return {
            'hp': int(self.base_hp * (self.hp_growth ** level_multiplier)),
            'attack': int(self.base_attack * (self.attack_growth ** level_multiplier)),
            'defense': int(self.base_defense * (self.defense_growth ** level_multiplier)),
            'speed': int(self.base_speed * (self.speed_growth ** level_multiplier)),
            'special_attack': int(self.base_special_attack * (self.special_attack_growth ** level_multiplier)),
            'special_defense': int(self.base_special_defense * (self.special_defense_growth ** level_multiplier))
        }
    
    def get_effective_damage_multiplier(self, opponent_affinity: str) -> float:
        """
        Get damage multiplier against an opponent of specific affinity
        
        Args:
            opponent_affinity: The dimensional affinity of the opponent
            
        Returns:
            Damage multiplier (1.0 = neutral, 2.0 = super effective, 0.5 = not very effective)
        """
        if opponent_affinity in self.strong_against:
            return 2.0  # Super effective
        elif opponent_affinity in self.weak_to:
            return 0.5  # Not very effective
        elif opponent_affinity in self.resists:
            return 0.75  # Resists
        else:
            return 1.0  # Normal damage
    
    def get_ability_at_bond_level(self, bond_level: int) -> dict:
        """
        Get the appropriate ability for an Echo at a specific bond level
        
        Args:
            bond_level: The bonding level
            
        Returns:
            Dictionary containing ability information
        """
        if bond_level >= self.secondary_ability_unlock_bond_level and self.secondary_ability_name:
            return {
                'name': self.secondary_ability_name,
                'description': self.secondary_ability_description,
                'type': self.secondary_ability_type,
                'power': self.secondary_ability_power,
                'accuracy': 1.0,
                'cooldown': 3,
                'is_secondary': True
            }
        else:
            return {
                'name': self.ability_name,
                'description': self.ability_description,
                'type': self.ability_type,
                'power': self.ability_power,
                'accuracy': self.ability_accuracy,
                'cooldown': self.ability_cooldown,
                'is_secondary': False
            }
    
    def is_capturable_with_item(self, item_name: str = None) -> bool:
        """
        Check if Echo can be captured with a specific item
        
        Args:
            item_name: Name of the item being used to capture
            
        Returns:
            True if Echo can be captured, False otherwise
        """
        if not self.requires_special_item:
            return True
        
        if item_name is None:
            return False
        
        return item_name.lower() == self.requires_special_item.lower()
    
    def update_capture_stats(self, bond_level: int) -> None:
        """
        Update capture statistics when Echo is bonded
        
        Args:
            bond_level: The bonding level achieved
        """
        self.times_bonded += 1
        
        if self.times_bonded > 0:
            # Update average bonding level
            self.average_bonding_level = (
                (self.average_bonding_level * (self.times_bonded - 1) + bond_level) /
                self.times_bonded
            )
    
    def increment_capture_count(self) -> None:
        """Increment the total number of times this Echo has been captured"""
        self.total_captured += 1
    
    def get_rarity_color(self) -> str:
        """Get color associated with rarity"""
        rarity_colors = {
            'common': '#808080',      # Gray
            'uncommon': '#00FF00',    # Green
            'rare': '#0000FF',        # Blue
            'epic': '#A020F0',        # Purple
            'legendary': '#FFA500'    # Orange
        }
        return rarity_colors.get(self.rift_rarity, '#FFFFFF')
    
    def can_evolve(self) -> bool:
        """Check if this Echo has an evolution"""
        return self.evolution_chain is not None
    
    def get_evolution(self) -> 'Echo':
        """Get the evolution of this Echo"""
        if self.evolution_chain:
            return Echo.query.get(self.evolution_chain)
        return None


# Association table for Rift-Echo relationship
rift_echoes = db.Table(
    'rift_echoes',
    db.Column('rift_id', UUID(as_uuid=True), db.ForeignKey('rifts.id'), primary_key=True),
    db.Column('echo_id', UUID(as_uuid=True), db.ForeignKey('echoes.id'), primary_key=True)
)
