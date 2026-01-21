"""
ChronoRift Riftwalker Model
Represents player characters in the game world
"""

from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.models import db


class Riftwalker(db.Model):
    """
    Riftwalker Model - Player Character
    
    A Riftwalker is a rare individual capable of bonding with Echoes.
    This model represents all player character data.
    """
    
    __tablename__ = 'riftwalkers'
    
    # Primary Key
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    
    # Authentication & Account
    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    
    # Profile Information
    display_name = db.Column(db.String(64), nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    
    # Game Progression
    level = db.Column(db.Integer, default=1, nullable=False, index=True)
    experience = db.Column(db.BigInteger, default=0, nullable=False)
    experience_to_next_level = db.Column(db.BigInteger, default=1000, nullable=False)
    
    # Currency & Resources
    temporal_fragments = db.Column(db.BigInteger, default=1000, nullable=False)  # Primary currency
    dimensional_essence = db.Column(db.BigInteger, default=0, nullable=False)    # Premium currency
    
    # Faction & Alignment
    faction_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('factions.id'),
        nullable=True,
        index=True
    )
    faction_reputation = db.Column(db.Integer, default=0, nullable=False)
    alignment = db.Column(
        db.String(20),
        default='neutral',
        nullable=False
    )  # neutral, harmonist, singularist, voidseer
    
    # Guild Membership
    guild_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('guilds.id'),
        nullable=True,
        index=True
    )
    guild_role = db.Column(
        db.String(20),
        default='member',
        nullable=False
    )  # member, officer, leader
    
    # Stats & Attributes
    max_health = db.Column(db.Integer, default=100, nullable=False)
    current_health = db.Column(db.Integer, default=100, nullable=False)
    max_mana = db.Column(db.Integer, default=50, nullable=False)
    current_mana = db.Column(db.Integer, default=50, nullable=False)
    
    # Combat Stats
    attack = db.Column(db.Integer, default=10, nullable=False)
    defense = db.Column(db.Integer, default=10, nullable=False)
    speed = db.Column(db.Integer, default=10, nullable=False)
    special_attack = db.Column(db.Integer, default=10, nullable=False)
    special_defense = db.Column(db.Integer, default=10, nullable=False)
    
    # Combat Record
    battles_won = db.Column(db.Integer, default=0, nullable=False)
    battles_lost = db.Column(db.Integer, default=0, nullable=False)
    battles_total = db.Column(db.Integer, default=0, nullable=False)
    win_rate = db.Column(db.Float, default=0.0, nullable=False)
    
    # Sanctuary (Player Base)
    sanctuary_level = db.Column(db.Integer, default=1, nullable=False)
    sanctuary_data = db.Column(JSONB, default={}, nullable=False)  # Customization, storage, etc.
    
    # Game Preferences
    language = db.Column(db.String(10), default='en', nullable=False)
    timezone = db.Column(db.String(50), default='UTC', nullable=False)
    push_notifications_enabled = db.Column(db.Boolean, default=True, nullable=False)
    email_notifications_enabled = db.Column(db.Boolean, default=True, nullable=False)
    pvp_enabled = db.Column(db.Boolean, default=True, nullable=False)
    
    # Social Preferences
    allow_friend_requests = db.Column(db.Boolean, default=True, nullable=False)
    allow_trade_requests = db.Column(db.Boolean, default=True, nullable=False)
    allow_guild_invites = db.Column(db.Boolean, default=True, nullable=False)
    privacy_level = db.Column(
        db.String(20),
        default='public',
        nullable=False
    )  # public, friends_only, private
    
    # Account Security
    two_factor_enabled = db.Column(db.Boolean, default=False, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    last_logout = db.Column(db.DateTime, nullable=True)
    
    # Moderation
    is_banned = db.Column(db.Boolean, default=False, nullable=False)
    ban_reason = db.Column(db.Text, nullable=True)
    ban_until = db.Column(db.DateTime, nullable=True)
    is_muted = db.Column(db.Boolean, default=False, nullable=False)
    mute_until = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)
    
    # Relationships
    faction = db.relationship('Faction', back_populates='riftwalkers')
    guild = db.relationship('Guild', back_populates='members')
    echoes = db.relationship('Echo', secondary='riftwalker_echoes', back_populates='riftwalkers')
    bonded_echoes = db.relationship('Bonding', back_populates='riftwalker')
    friends = db.relationship(
        'Riftwalker',
        secondary='friendships',
        primaryjoin='Riftwalker.id==friendships.c.riftwalker_id_1',
        secondaryjoin='Riftwalker.id==friendships.c.riftwalker_id_2',
        backref='friend_of'
    )
    transactions = db.relationship('Transaction', back_populates='riftwalker', cascade='all, delete-orphan')
    battles = db.relationship('Battle', back_populates='riftwalker', cascade='all, delete-orphan')
    chat_messages = db.relationship('ChatMessage', back_populates='sender', cascade='all, delete-orphan')
    
    def __repr__(self) -> str:
        return f'<Riftwalker {self.username} (Level {self.level})>'
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert Riftwalker to dictionary representation
        
        Args:
            include_sensitive: Include password hash and sensitive data
            
        Returns:
            Dictionary representation of Riftwalker
        """
        data = {
            'id': str(self.id),
            'username': self.username,
            'display_name': self.display_name,
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'level': self.level,
            'experience': self.experience,
            'temporal_fragments': self.temporal_fragments,
            'dimensional_essence': self.dimensional_essence,
            'faction_id': str(self.faction_id) if self.faction_id else None,
            'faction_name': self.faction.name if self.faction else None,
            'faction_reputation': self.faction_reputation,
            'alignment': self.alignment,
            'guild_id': str(self.guild_id) if self.guild_id else None,
            'guild_role': self.guild_role,
            'level': self.level,
            'health': {
                'current': self.current_health,
                'max': self.max_health
            },
            'mana': {
                'current': self.current_mana,
                'max': self.max_mana
            },
            'stats': {
                'attack': self.attack,
                'defense': self.defense,
                'speed': self.speed,
                'special_attack': self.special_attack,
                'special_defense': self.special_defense
            },
            'battles': {
                'won': self.battles_won,
                'lost': self.battles_lost,
                'total': self.battles_total,
                'win_rate': self.win_rate
            },
            'sanctuary_level': self.sanctuary_level,
            'pvp_enabled': self.pvp_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            data.update({
                'email': self.email,
                'is_active': self.is_active,
                'is_verified': self.is_verified,
                'two_factor_enabled': self.two_factor_enabled,
                'last_login': self.last_login.isoformat() if self.last_login else None,
                'last_logout': self.last_logout.isoformat() if self.last_logout else None,
                'is_banned': self.is_banned,
                'is_muted': self.is_muted
            })
        
        return data
    
    def add_experience(self, amount: int) -> bool:
        """
        Add experience to Riftwalker
        
        Args:
            amount: Experience to add
            
        Returns:
            True if leveled up, False otherwise
        """
        self.experience += amount
        leveled_up = False
        
        while self.experience >= self.experience_to_next_level:
            self.level_up()
            leveled_up = True
        
        return leveled_up
    
    def level_up(self) -> None:
        """Level up the Riftwalker"""
        self.experience -= self.experience_to_next_level
        self.level += 1
        
        # Recalculate experience needed for next level
        # Formula: 1000 * (level ^ 1.5)
        self.experience_to_next_level = int(1000 * (self.level ** 1.5))
        
        # Increase stats on level up
        stat_increase = 2 + (self.level // 10)  # 2 base + bonus every 10 levels
        self.max_health += 10 + stat_increase
        self.max_mana += 5 + (stat_increase // 2)
        self.attack += stat_increase
        self.defense += stat_increase
        self.speed += 1
        self.special_attack += stat_increase
        self.special_defense += stat_increase
        
        # Restore health and mana on level up
        self.current_health = self.max_health
        self.current_mana = self.max_mana
    
    def add_currency(self, temporal_fragments: int = 0, dimensional_essence: int = 0) -> None:
        """
        Add currency to Riftwalker
        
        Args:
            temporal_fragments: Amount of primary currency to add
            dimensional_essence: Amount of premium currency to add
        """
        if temporal_fragments > 0:
            self.temporal_fragments += temporal_fragments
        if dimensional_essence > 0:
            self.dimensional_essence += dimensional_essence
    
    def remove_currency(self, temporal_fragments: int = 0, dimensional_essence: int = 0) -> bool:
        """
        Remove currency from Riftwalker
        
        Args:
            temporal_fragments: Amount of primary currency to remove
            dimensional_essence: Amount of premium currency to remove
            
        Returns:
            True if successful, False if insufficient currency
        """
        if temporal_fragments > self.temporal_fragments or dimensional_essence > self.dimensional_essence:
            return False
        
        if temporal_fragments > 0:
            self.temporal_fragments -= temporal_fragments
        if dimensional_essence > 0:
            self.dimensional_essence -= dimensional_essence
        
        return True
    
    def heal(self, amount: int = None) -> None:
        """
        Heal the Riftwalker
        
        Args:
            amount: Amount to heal (defaults to max health)
        """
        if amount is None:
            self.current_health = self.max_health
        else:
            self.current_health = min(self.current_health + amount, self.max_health)
    
    def take_damage(self, amount: int) -> None:
        """
        Take damage
        
        Args:
            amount: Damage to take
        """
        self.current_health = max(self.current_health - amount, 0)
    
    def restore_mana(self, amount: int = None) -> None:
        """
        Restore mana
        
        Args:
            amount: Amount to restore (defaults to max mana)
        """
        if amount is None:
            self.current_mana = self.max_mana
        else:
            self.current_mana = min(self.current_mana + amount, self.max_mana)
    
    def use_mana(self, amount: int) -> bool:
        """
        Use mana
        
        Args:
            amount: Amount to use
            
        Returns:
            True if successful, False if insufficient mana
        """
        if amount > self.current_mana:
            return False
        
        self.current_mana -= amount
        return True
    
    def add_friend(self, friend: 'Riftwalker') -> bool:
        """
        Add a friend
        
        Args:
            friend: Riftwalker to add as friend
            
        Returns:
            True if successful, False if already friends
        """
        if friend in self.friends:
            return False
        
        self.friends.append(friend)
        return True
    
    def remove_friend(self, friend: 'Riftwalker') -> bool:
        """
        Remove a friend
        
        Args:
            friend: Riftwalker to remove as friend
            
        Returns:
            True if successful, False if not friends
        """
        if friend not in self.friends:
            return False
        
        self.friends.remove(friend)
        return True
    
    def is_friend_with(self, other: 'Riftwalker') -> bool:
        """
        Check if friend with another Riftwalker
        
        Args:
            other: Riftwalker to check
            
        Returns:
            True if friends, False otherwise
        """
        return other in self.friends
    
    def update_stats_from_echoes(self) -> None:
        """Update Riftwalker stats based on equipped Echoes"""
        # Reset stats to base
        base_attack = 10
        base_defense = 10
        base_speed = 10
        base_special_attack = 10
        base_special_defense = 10
        
        # Add bonuses from equipped Echoes
        for bonding in self.bonded_echoes:
            if bonding.is_active:
                echo = bonding.echo
                # Stats scale with Echo level and bonding level
                level_multiplier = 1 + (echo.level * 0.05)
                bonding_multiplier = 1 + (bonding.bonding_level * 0.1)
                
                base_attack += int(echo.attack * level_multiplier * bonding_multiplier)
                base_defense += int(echo.defense * level_multiplier * bonding_multiplier)
                base_speed += int(echo.speed * level_multiplier * bonding_multiplier)
                base_special_attack += int(echo.special_attack * level_multiplier * bonding_multiplier)
                base_special_defense += int(echo.special_defense * level_multiplier * bonding_multiplier)
        
        self.attack = base_attack
        self.defense = base_defense
        self.speed = base_speed
        self.special_attack = base_special_attack
        self.special_defense = base_special_defense
    
    def ban(self, reason: str, hours: int = 0) -> None:
        """
        Ban the Riftwalker
        
        Args:
            reason: Reason for ban
            hours: Hours to ban (0 = permanent)
        """
        self.is_banned = True
        self.ban_reason = reason
        
        if hours > 0:
            from datetime import timedelta
            self.ban_until = datetime.utcnow() + timedelta(hours=hours)
    
    def unban(self) -> None:
        """Unban the Riftwalker"""
        self.is_banned = False
        self.ban_reason = None
        self.ban_until = None
    
    def mute(self, hours: int = 1) -> None:
        """
        Mute the Riftwalker
        
        Args:
            hours: Hours to mute (default: 1)
        """
        from datetime import timedelta
        self.is_muted = True
        self.mute_until = datetime.utcnow() + timedelta(hours=hours)
    
    def unmute(self) -> None:
        """Unmute the Riftwalker"""
        self.is_muted = False
        self.mute_until = None
    
    def is_banned_now(self) -> bool:
        """Check if currently banned"""
        if not self.is_banned:
            return False
        
        if self.ban_until is None:
            return True  # Permanent ban
        
        if datetime.utcnow() > self.ban_until:
            self.unban()
            return False
        
        return True
    
    def is_muted_now(self) -> bool:
        """Check if currently muted"""
        if not self.is_muted:
            return False
        
        if datetime.utcnow() > self.mute_until:
            self.unmute()
            return False
        
        return True


# Association table for Riftwalker-Echo many-to-many relationship
riftwalker_echoes = db.Table(
    'riftwalker_echoes',
    db.Column('riftwalker_id', UUID(as_uuid=True), db.ForeignKey('riftwalkers.id'), primary_key=True),
    db.Column('echo_id', UUID(as_uuid=True), db.ForeignKey('echoes.id'), primary_key=True)
)

# Association table for friendships
friendships = db.Table(
    'friendships',
    db.Column('riftwalker_id_1', UUID(as_uuid=True), db.ForeignKey('riftwalkers.id'), primary_key=True),
    db.Column('riftwalker_id_2', UUID(as_uuid=True), db.ForeignKey('riftwalkers.id'), primary_key=True)
)
