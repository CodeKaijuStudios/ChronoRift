"""
ChronoRift Faction Model
Represents player factions and their influence on the game world
"""

from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import uuid

from app.models import db


class Faction(db.Model):
    """
    Faction Model - Player Factions
    
    Three competing factions shape the world:
    - Harmonists: Seek to seal all rifts and restore balance
    - Singularists: Study rifts to expand their power
    - Voidseers: Embrace the void and dimensional chaos
    """
    
    __tablename__ = 'factions'
    
    # Primary Key
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    
    # Basic Information
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    # harmonists, singularists, voidseers
    description = db.Column(db.Text, nullable=False)
    lore = db.Column(db.Text, nullable=True)
    
    # Visual Properties
    logo_url = db.Column(db.String(500), nullable=True)
    color_primary = db.Column(db.String(7), nullable=False)  # Hex color
    color_secondary = db.Column(db.String(7), nullable=True)  # Hex color
    symbol = db.Column(db.String(50), nullable=True)  # Unicode symbol or description
    
    # Ideology & Goals
    ideology = db.Column(db.Text, nullable=True)
    primary_goal = db.Column(db.String(200), nullable=True)
    alignment = db.Column(
        db.String(20),
        nullable=False
    )  # lawful, neutral, chaotic
    
    # Membership & Power
    member_count = db.Column(db.Integer, default=0, nullable=False)
    total_influence = db.Column(db.Integer, default=0, nullable=False)  # Cumulative power
    global_control_percentage = db.Column(db.Float, default=0.0, nullable=False)  # 0.0 - 100.0
    
    # Faction Rank System
    rank_names = db.Column(ARRAY(db.String(50)), default=[
        'Initiate', 'Member', 'Veteran', 'Leader', 'Sage', 'Archon'
    ], nullable=False)
    
    # Resources & Treasury
    treasury_balance = db.Column(db.BigInteger, default=100000, nullable=False)
    resource_points = db.Column(db.Integer, default=1000, nullable=False)
    
    # Reputation & Relations
    reputation_with_factions = db.Column(JSONB, default={}, nullable=False)
    # {faction_id: reputation_score}
    
    # Territory Control
    controlled_zones_count = db.Column(db.Integer, default=0, nullable=False)
    total_zone_coverage = db.Column(db.Float, default=0.0, nullable=False)  # Percentage
    
    # Statistics & Achievements
    total_battles_won = db.Column(db.Integer, default=0, nullable=False)
    total_battles_lost = db.Column(db.Integer, default=0, nullable=False)
    rifts_sealed = db.Column(db.Integer, default=0, nullable=False)
    rifts_opened = db.Column(db.Integer, default=0, nullable=False)
    echoes_controlled = db.Column(db.Integer, default=0, nullable=False)
    
    # Special Abilities & Perks
    faction_ability_name = db.Column(db.String(100), nullable=True)
    faction_ability_description = db.Column(db.Text, nullable=True)
    faction_ability_cooldown = db.Column(db.Integer, default=3600, nullable=True)  # seconds
    
    # Unlockable Content
    unlocked_echo_types = db.Column(ARRAY(UUID(as_uuid=True)), default=[], nullable=False)
    unlocked_items = db.Column(ARRAY(db.String(100)), default=[], nullable=False)
    unlocked_cosmetics = db.Column(ARRAY(db.String(100)), default=[], nullable=False)
    
    # Bonuses & Buffs
    exp_multiplier = db.Column(db.Float, default=1.0, nullable=False)
    currency_multiplier = db.Column(db.Float, default=1.0, nullable=False)
    echo_capture_bonus = db.Column(db.Float, default=0.0, nullable=False)  # Percentage
    rift_stabilization_bonus = db.Column(db.Float, default=0.0, nullable=False)  # Percentage
    
    # War & Conflict State
    is_at_war = db.Column(db.Boolean, default=False, nullable=False, index=True)
    war_against_faction_id = db.Column(UUID(as_uuid=True), db.ForeignKey('factions.id'), nullable=True)
    war_start_time = db.Column(db.DateTime, nullable=True)
    war_kills = db.Column(db.Integer, default=0, nullable=False)
    war_deaths = db.Column(db.Integer, default=0, nullable=False)
    
    # Governance
    leader_id = db.Column(UUID(as_uuid=True), db.ForeignKey('riftwalkers.id'), nullable=True)
    council_member_ids = db.Column(ARRAY(UUID(as_uuid=True)), default=[], nullable=False)
    founding_date = db.Column(db.DateTime, nullable=True)
    
    # Metadata
    metadata = db.Column(JSONB, default={}, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    members = db.relationship('Riftwalker', back_populates='faction', foreign_keys='Riftwalker.faction_id')
    controlled_zones = db.relationship('Zone', foreign_keys='Zone.controlling_faction_id')
    leader = db.relationship('Riftwalker', foreign_keys=[leader_id])
    wars = db.relationship(
        'Faction',
        secondary='faction_wars',
        primaryjoin='Faction.id==faction_wars.c.faction_id_1',
        secondaryjoin='Faction.id==faction_wars.c.faction_id_2',
        backref='enemies'
    )
    
    def __repr__(self) -> str:
        return f'<Faction {self.name} (Members: {self.member_count})>'
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert Faction to dictionary representation
        
        Args:
            include_sensitive: Include treasury and resource data
            
        Returns:
            Dictionary representation of Faction
        """
        data = {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'lore': self.lore,
            'logo_url': self.logo_url,
            'color_primary': self.color_primary,
            'color_secondary': self.color_secondary,
            'symbol': self.symbol,
            'ideology': self.ideology,
            'alignment': self.alignment,
            'member_count': self.member_count,
            'total_influence': self.total_influence,
            'global_control_percentage': self.global_control_percentage,
            'controlled_zones_count': self.controlled_zones_count,
            'is_at_war': self.is_at_war,
            'statistics': {
                'battles_won': self.total_battles_won,
                'battles_lost': self.total_battles_lost,
                'rifts_sealed': self.rifts_sealed,
                'rifts_opened': self.rifts_opened,
                'echoes_controlled': self.echoes_controlled
            },
            'bonuses': {
                'exp_multiplier': self.exp_multiplier,
                'currency_multiplier': self.currency_multiplier,
                'echo_capture_bonus': self.echo_capture_bonus,
                'rift_stabilization_bonus': self.rift_stabilization_bonus
            },
            'faction_ability': {
                'name': self.faction_ability_name,
                'description': self.faction_ability_description,
                'cooldown': self.faction_ability_cooldown
            }
        }
        
        if include_sensitive:
            data.update({
                'treasury_balance': self.treasury_balance,
                'resource_points': self.resource_points,
                'leader_id': str(self.leader_id) if self.leader_id else None,
                'council_members': [str(member_id) for member_id in self.council_member_ids]
            })
        
        return data
    
    def add_member(self, riftwalker: 'Riftwalker') -> bool:
        """
        Add a member to the faction
        
        Args:
            riftwalker: Riftwalker to add
            
        Returns:
            True if successful, False if already member
        """
        if riftwalker.faction_id == self.id:
            return False
        
        riftwalker.faction_id = self.id
        riftwalker.guild_role = 'member'
        self.member_count += 1
        
        return True
    
    def remove_member(self, riftwalker: 'Riftwalker') -> bool:
        """
        Remove a member from the faction
        
        Args:
            riftwalker: Riftwalker to remove
            
        Returns:
            True if successful, False if not member
        """
        if riftwalker.faction_id != self.id:
            return False
        
        riftwalker.faction_id = None
        self.member_count = max(0, self.member_count - 1)
        
        return True
    
    def add_influence(self, amount: int) -> None:
        """
        Add influence to the faction
        
        Args:
            amount: Amount of influence to add
        """
        self.total_influence += amount
        
        # Update global control percentage (simplified calculation)
        # In production, this would aggregate across all factions
        self.global_control_percentage = min(100.0, max(0.0, self.total_influence / 10000 * 100))
    
    def add_treasury(self, amount: int) -> None:
        """
        Add currency to faction treasury
        
        Args:
            amount: Amount to add
        """
        self.treasury_balance += amount
    
    def withdraw_treasury(self, amount: int) -> bool:
        """
        Withdraw currency from faction treasury
        
        Args:
            amount: Amount to withdraw
            
        Returns:
            True if successful, False if insufficient funds
        """
        if amount > self.treasury_balance:
            return False
        
        self.treasury_balance -= amount
        return True
    
    def add_resources(self, amount: int) -> None:
        """
        Add resource points to faction
        
        Args:
            amount: Amount of resource points
        """
        self.resource_points += amount
    
    def spend_resources(self, amount: int) -> bool:
        """
        Spend faction resource points
        
        Args:
            amount: Amount to spend
            
        Returns:
            True if successful, False if insufficient resources
        """
        if amount > self.resource_points:
            return False
        
        self.resource_points -= amount
        return True
    
    def declare_war(self, enemy_faction: 'Faction') -> bool:
        """
        Declare war on another faction
        
        Args:
            enemy_faction: Faction to declare war on
            
        Returns:
            True if successful, False if already at war
        """
        if self.is_at_war:
            return False
        
        self.is_at_war = True
        self.war_against_faction_id = enemy_faction.id
        self.war_start_time = datetime.utcnow()
        self.war_kills = 0
        self.war_deaths = 0
        
        # Update reputation
        if str(enemy_faction.id) not in self.reputation_with_factions:
            self.reputation_with_factions[str(enemy_faction.id)] = 0
        
        self.reputation_with_factions[str(enemy_faction.id)] -= 50
        
        return True
    
    def end_war(self, peace: bool = True) -> bool:
        """
        End the current war
        
        Args:
            peace: Whether it's a peace treaty (True) or defeat (False)
            
        Returns:
            True if successful, False if not at war
        """
        if not self.is_at_war:
            return False
        
        self.is_at_war = False
        self.war_against_faction_id = None
        self.war_start_time = None
        
        if peace:
            # Repair relations slightly
            if self.war_against_faction_id and str(self.war_against_faction_id) in self.reputation_with_factions:
                self.reputation_with_factions[str(self.war_against_faction_id)] += 25
        
        return True
    
    def record_battle_victory(self) -> None:
        """Record a battle victory"""
        self.total_battles_won += 1
        if self.is_at_war:
            self.war_kills += 1
            self.add_influence(50)
    
    def record_battle_defeat(self) -> None:
        """Record a battle defeat"""
        self.total_battles_lost += 1
        if self.is_at_war:
            self.war_deaths += 1
    
    def seal_rift(self) -> None:
        """Record rift sealing by faction members"""
        self.rifts_sealed += 1
        self.add_influence(25)
    
    def open_rift(self) -> None:
        """Record rift opening by faction members"""
        self.rifts_opened += 1
        self.add_influence(25)
    
    def control_echo(self, echo_count: int = 1) -> None:
        """
        Record faction control of Echoes
        
        Args:
            echo_count: Number of Echoes controlled
        """
        self.echoes_controlled += echo_count
        self.add_influence(echo_count * 10)
    
    def unlock_echo_type(self, echo_id: UUID) -> bool:
        """
        Unlock a new Echo type for the faction
        
        Args:
            echo_id: UUID of the Echo to unlock
            
        Returns:
            True if successful, False if already unlocked
        """
        if echo_id in self.unlocked_echo_types:
            return False
        
        self.unlocked_echo_types.append(echo_id)
        return True
    
    def set_leader(self, riftwalker: 'Riftwalker') -> bool:
        """
        Set faction leader
        
        Args:
            riftwalker: Riftwalker to set as leader
            
        Returns:
            True if successful
        """
        if riftwalker.faction_id != self.id:
            return False
        
        self.leader_id = riftwalker.id
        riftwalker.guild_role = 'leader'
        
        return True
    
    def add_council_member(self, riftwalker: 'Riftwalker') -> bool:
        """
        Add council member
        
        Args:
            riftwalker: Riftwalker to add to council
            
        Returns:
            True if successful, False if already council member
        """
        if riftwalker.faction_id != self.id:
            return False
        
        if riftwalker.id in self.council_member_ids:
            return False
        
        self.council_member_ids.append(riftwalker.id)
        riftwalker.guild_role = 'officer'
        
        return True
    
    def remove_council_member(self, riftwalker: 'Riftwalker') -> bool:
        """
        Remove council member
        
        Args:
            riftwalker: Riftwalker to remove from council
            
        Returns:
            True if successful, False if not council member
        """
        if riftwalker.id not in self.council_member_ids:
            return False
        
        self.council_member_ids.remove(riftwalker.id)
        riftwalker.guild_role = 'member'
        
        return True
    
    def get_reputation_with(self, other_faction: 'Faction') -> int:
        """
        Get reputation with another faction
        
        Args:
            other_faction: Faction to check reputation with
            
        Returns:
            Reputation score (-1000 to 1000)
        """
        return self.reputation_with_factions.get(str(other_faction.id), 0)
    
    def update_reputation_with(self, other_faction: 'Faction', amount: int) -> None:
        """
        Update reputation with another faction
        
        Args:
            other_faction: Faction to update reputation with
            amount: Amount to change reputation by
        """
        faction_key = str(other_faction.id)
        
        if faction_key not in self.reputation_with_factions:
            self.reputation_with_factions[faction_key] = 0
        
        self.reputation_with_factions[faction_key] = max(-1000, min(1000, 
            self.reputation_with_factions[faction_key] + amount
        ))


class Guild(db.Model):
    """
    Guild Model - Player Organizations
    
    Guilds are player-created organizations that control territory
    and manage Echo populations. Different from Factions.
    """
    
    __tablename__ = 'guilds'
    
    # Primary Key
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    
    # Basic Information
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=False)
    
    # Visual Properties
    logo_url = db.Column(db.String(500), nullable=True)
    banner_url = db.Column(db.String(500), nullable=True)
    color_primary = db.Column(db.String(7), nullable=False)  # Hex color
    
    # Leadership
    leader_id = db.Column(UUID(as_uuid=True), db.ForeignKey('riftwalkers.id'), nullable=False)
    
    # Membership
    member_count = db.Column(db.Integer, default=1, nullable=False)
    max_members = db.Column(db.Integer, default=100, nullable=False)
    
    # Resources
    treasury_balance = db.Column(db.BigInteger, default=0, nullable=False)
    resource_points = db.Column(db.Integer, default=0, nullable=False)
    
    # Territory
    controlled_zones = db.Column(ARRAY(UUID(as_uuid=True)), default=[], nullable=False)
    total_territory_control = db.Column(db.Float, default=0.0, nullable=False)
    
    # Statistics
    total_battles = db.Column(db.Integer, default=0, nullable=False)
    battles_won = db.Column(db.Integer, default=0, nullable=False)
    battles_lost = db.Column(db.Integer, default=0, nullable=False)
    
    # Guild Level & Perks
    guild_level = db.Column(db.Integer, default=1, nullable=False)
    perks = db.Column(ARRAY(db.String(100)), default=[], nullable=False)
    
    # Metadata
    metadata = db.Column(JSONB, default={}, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    disbanded_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    members = db.relationship('Riftwalker', back_populates='guild')
    leader = db.relationship('Riftwalker', foreign_keys=[leader_id])
    
    def __repr__(self) -> str:
        return f'<Guild {self.name}>'
    
    def to_dict(self) -> dict:
        """Convert Guild to dictionary representation"""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'logo_url': self.logo_url,
            'color_primary': self.color_primary,
            'leader_id': str(self.leader_id),
            'member_count': self.member_count,
            'max_members': self.max_members,
            'guild_level': self.guild_level,
            'treasury_balance': self.treasury_balance,
            'controlled_zones': len(self.controlled_zones),
            'statistics': {
                'total_battles': self.total_battles,
                'battles_won': self.battles_won,
                'battles_lost': self.battles_lost
            }
        }


# Association table for faction wars
faction_wars = db.Table(
    'faction_wars',
    db.Column('faction_id_1', UUID(as_uuid=True), db.ForeignKey('factions.id'), primary_key=True),
    db.Column('faction_id_2', UUID(as_uuid=True), db.ForeignKey('factions.id'), primary_key=True)
)
