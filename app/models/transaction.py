"""
ChronoRift Transaction Model
Represents trading, economy, and financial transactions in the game
"""

from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from enum import Enum
import uuid

from app.models import db


class TransactionType(Enum):
    """Transaction types in the economy"""
    PLAYER_TRADE = 'player_trade'           # Direct P2P trade
    MARKETPLACE_SALE = 'marketplace_sale'   # Marketplace listing sale
    MARKETPLACE_BUY = 'marketplace_buy'     # Marketplace purchase
    FACTION_TRANSFER = 'faction_transfer'   # Faction treasury transfer
    GUILD_TRANSFER = 'guild_transfer'       # Guild treasury transfer
    NPC_VENDOR = 'npc_vendor'              # Trading with NPC vendors
    ECHO_CAPTURE_REWARD = 'echo_reward'     # Echo capture rewards
    BATTLE_REWARD = 'battle_reward'         # Battle victory rewards
    QUEST_REWARD = 'quest_reward'           # Quest completion rewards
    CRAFTING_COST = 'crafting_cost'         # Item crafting expense
    REPAIR_COST = 'repair_cost'             # Equipment repair expense
    TAX_PAYMENT = 'tax_payment'             # Faction/marketplace taxes
    REFUND = 'refund'                       # Transaction refund
    ADMIN_ADJUSTMENT = 'admin_adjustment'   # Admin-made adjustments


class TransactionStatus(Enum):
    """Status of a transaction"""
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    DISPUTED = 'disputed'


class CurrencyType(Enum):
    """Types of currency in ChronoRift"""
    CHRONONS = 'chronons'           # Primary in-game currency
    ESSENCE = 'essence'            # Premium currency
    FACTION_MARKS = 'faction_marks' # Faction-specific currency
    REALM_TOKENS = 'realm_tokens'   # Dimensional realm currency


class Transaction(db.Model):
    """
    Transaction Model - Economy Transactions
    
    Tracks all financial transactions including:
    - Player-to-player trades
    - Marketplace buy/sell orders
    - NPC transactions
    - Rewards from activities
    - Faction/Guild transfers
    """
    
    __tablename__ = 'transactions'
    
    # Primary Key
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    
    # Parties Involved
    initiator_id = db.Column(UUID(as_uuid=True), db.ForeignKey('riftwalkers.id'), nullable=False, index=True)
    recipient_id = db.Column(UUID(as_uuid=True), db.ForeignKey('riftwalkers.id'), nullable=True, index=True)
    
    # Related Entities (optional)
    faction_id = db.Column(UUID(as_uuid=True), db.ForeignKey('factions.id'), nullable=True)
    guild_id = db.Column(UUID(as_uuid=True), db.ForeignKey('guilds.id'), nullable=True)
    marketplace_listing_id = db.Column(UUID(as_uuid=True), nullable=True)  # Reference to marketplace listing
    
    # Transaction Details
    transaction_type = db.Column(
        db.String(50),
        nullable=False,
        index=True
    )  # TransactionType value
    
    status = db.Column(
        db.String(20),
        default='completed',
        nullable=False,
        index=True
    )  # TransactionStatus value
    
    # Currency Exchange
    currency_type = db.Column(
        db.String(30),
        nullable=False
    )  # CurrencyType value
    
    amount = db.Column(db.BigInteger, nullable=False)  # Amount of currency
    
    # Items (if applicable)
    items_involved = db.Column(JSONB, default={}, nullable=False)
    # {item_id: quantity, ...}
    
    # Fees & Taxes
    tax_amount = db.Column(db.BigInteger, default=0, nullable=False)
    tax_percentage = db.Column(db.Float, default=0.0, nullable=False)  # 0.0-100.0
    transaction_fee = db.Column(db.BigInteger, default=0, nullable=False)
    fee_recipient_id = db.Column(UUID(as_uuid=True), nullable=True)  # Who receives the fee
    
    # Net Amount
    net_amount = db.Column(db.BigInteger, nullable=False)  # amount - fees - taxes
    
    # Exchange Rate (for different currency types)
    exchange_rate = db.Column(db.Float, default=1.0, nullable=False)
    source_currency = db.Column(db.String(30), nullable=True)
    target_currency = db.Column(db.String(30), nullable=True)
    
    # Trade Details
    trade_partner_id = db.Column(UUID(as_uuid=True), nullable=True)  # For P2P trades
    items_given = db.Column(JSONB, default={}, nullable=False)  # {item_id: quantity}
    items_received = db.Column(JSONB, default={}, nullable=False)  # {item_id: quantity}
    
    # Marketplace Details
    listing_price = db.Column(db.BigInteger, nullable=True)
    listing_quantity = db.Column(db.Integer, nullable=True)
    quantity_purchased = db.Column(db.Integer, nullable=True)
    
    # Description & Notes
    description = db.Column(db.String(500), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Metadata
    metadata = db.Column(JSONB, default={}, nullable=False)
    
    # Dispute Information
    is_disputed = db.Column(db.Boolean, default=False, nullable=False, index=True)
    dispute_reason = db.Column(db.Text, nullable=True)
    dispute_raised_at = db.Column(db.DateTime, nullable=True)
    dispute_resolved_at = db.Column(db.DateTime, nullable=True)
    dispute_resolution = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    initiator = db.relationship('Riftwalker', foreign_keys=[initiator_id], back_populates='sent_transactions')
    recipient = db.relationship('Riftwalker', foreign_keys=[recipient_id], back_populates='received_transactions')
    faction = db.relationship('Faction', foreign_keys=[faction_id])
    guild = db.relationship('Guild', foreign_keys=[guild_id])
    
    def __repr__(self) -> str:
        return f'<Transaction {self.transaction_type} {self.amount} {self.currency_type}>'
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert Transaction to dictionary representation
        
        Args:
            include_sensitive: Include internal details
            
        Returns:
            Dictionary representation of Transaction
        """
        data = {
            'id': str(self.id),
            'type': self.transaction_type,
            'status': self.status,
            'currency': self.currency_type,
            'amount': self.amount,
            'net_amount': self.net_amount,
            'tax_amount': self.tax_amount,
            'fee_amount': self.transaction_fee,
            'initiator_id': str(self.initiator_id),
            'recipient_id': str(self.recipient_id) if self.recipient_id else None,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'description': self.description,
            'is_disputed': self.is_disputed
        }
        
        if include_sensitive:
            data.update({
                'items_given': self.items_given,
                'items_received': self.items_received,
                'exchange_rate': self.exchange_rate,
                'metadata': self.metadata
            })
        
        return data
    
    def calculate_fees_and_taxes(self, base_tax_rate: float = 0.05) -> None:
        """
        Calculate transaction fees and taxes
        
        Args:
            base_tax_rate: Base tax rate as decimal (0.05 = 5%)
        """
        self.tax_percentage = base_tax_rate * 100
        self.tax_amount = int(self.amount * base_tax_rate)
        
        # Transaction fee (1% of amount)
        self.transaction_fee = int(self.amount * 0.01)
        
        # Calculate net amount
        self.net_amount = self.amount - self.tax_amount - self.transaction_fee
    
    def complete_transaction(self) -> bool:
        """
        Mark transaction as completed
        
        Returns:
            True if successful
        """
        if self.status != 'pending':
            return False
        
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        return True
    
    def fail_transaction(self, reason: str = None) -> bool:
        """
        Mark transaction as failed
        
        Args:
            reason: Reason for failure
            
        Returns:
            True if successful
        """
        if self.status not in ['pending', 'completed']:
            return False
        
        self.status = 'failed'
        if reason:
            self.notes = reason
        
        return True
    
    def raise_dispute(self, reason: str) -> bool:
        """
        Raise a dispute on the transaction
        
        Args:
            reason: Reason for dispute
            
        Returns:
            True if successful
        """
        if self.is_disputed:
            return False
        
        self.is_disputed = True
        self.status = 'disputed'
        self.dispute_reason = reason
        self.dispute_raised_at = datetime.utcnow()
        
        return True
    
    def resolve_dispute(self, resolution: str, refund: bool = False) -> bool:
        """
        Resolve a dispute
        
        Args:
            resolution: Resolution details
            refund: Whether to issue refund
            
        Returns:
            True if successful
        """
        if not self.is_disputed:
            return False
        
        self.dispute_resolved_at = datetime.utcnow()
        self.dispute_resolution = resolution
        
        if refund:
            self.status = 'refund'
        else:
            self.status = 'completed'
        
        return True


class MarketplaceListing(db.Model):
    """
    Marketplace Listing Model
    
    Player-created marketplace listings for buying/selling items
    """
    
    __tablename__ = 'marketplace_listings'
    
    # Primary Key
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    
    # Seller Information
    seller_id = db.Column(UUID(as_uuid=True), db.ForeignKey('riftwalkers.id'), nullable=False, index=True)
    seller_faction_id = db.Column(UUID(as_uuid=True), db.ForeignKey('factions.id'), nullable=True)
    
    # Item Details
    item_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)  # Reference to Item model
    item_name = db.Column(db.String(200), nullable=False)
    item_description = db.Column(db.Text, nullable=True)
    item_rarity = db.Column(db.String(50), nullable=False)  # common, uncommon, rare, legendary
    
    # Listing Details
    quantity = db.Column(db.Integer, nullable=False, default=1)
    quantity_remaining = db.Column(db.Integer, nullable=False, default=1)
    quantity_sold = db.Column(db.Integer, default=0, nullable=False)
    
    # Pricing
    unit_price = db.Column(db.BigInteger, nullable=False)
    currency_type = db.Column(db.String(30), nullable=False)  # CurrencyType value
    total_price = db.Column(db.BigInteger, nullable=False)  # unit_price * quantity
    
    # Listing Status
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    listing_type = db.Column(db.String(20), nullable=False)  # 'buy' or 'sell'
    
    # Expiration
    expires_at = db.Column(db.DateTime, nullable=True, index=True)
    auto_renew = db.Column(db.Boolean, default=False, nullable=False)
    renewal_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Filters & Requirements
    minimum_reputation = db.Column(db.Integer, default=0, nullable=False)
    faction_exclusive = db.Column(UUID(as_uuid=True), nullable=True)  # Only sell to this faction
    requires_faction_rank = db.Column(db.String(50), nullable=True)  # Minimum faction rank
    
    # Statistics
    total_views = db.Column(db.Integer, default=0, nullable=False)
    total_interactions = db.Column(db.Integer, default=0, nullable=False)
    
    # Metadata
    metadata = db.Column(JSONB, default={}, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    delisted_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    seller = db.relationship('Riftwalker', back_populates='marketplace_listings')
    seller_faction = db.relationship('Faction')
    purchases = db.relationship('Transaction', foreign_keys='Transaction.marketplace_listing_id')
    
    def __repr__(self) -> str:
        return f'<MarketplaceListing {self.item_name} x{self.quantity}>'
    
    def to_dict(self) -> dict:
        """Convert MarketplaceListing to dictionary"""
        return {
            'id': str(self.id),
            'item_name': self.item_name,
            'item_rarity': self.item_rarity,
            'quantity': self.quantity_remaining,
            'unit_price': self.unit_price,
            'currency': self.currency_type,
            'total_price': self.total_price,
            'seller_id': str(self.seller_id),
            'is_active': self.is_active,
            'listing_type': self.listing_type,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'views': self.total_views,
            'quantity_sold': self.quantity_sold
        }
    
    def update_quantity(self, amount: int) -> bool:
        """
        Update available quantity
        
        Args:
            amount: Amount to reduce from available quantity
            
        Returns:
            True if successful, False if insufficient quantity
        """
        if amount > self.quantity_remaining:
            return False
        
        self.quantity_remaining -= amount
        self.quantity_sold += amount
        
        if self.quantity_remaining <= 0:
            self.is_active = False
        
        return True
    
    def record_interaction(self) -> None:
        """Record user interaction with listing"""
        self.total_interactions += 1
    
    def record_view(self) -> None:
        """Record view of listing"""
        self.total_views += 1


class EconomySnapshot(db.Model):
    """
    Economy Snapshot Model
    
    Periodic snapshots of economy state for analysis
    """
    
    __tablename__ = 'economy_snapshots'
    
    # Primary Key
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    
    # Time Period
    snapshot_date = db.Column(db.DateTime, nullable=False, index=True)
    period = db.Column(db.String(20), nullable=False)  # 'hourly', 'daily', 'weekly', 'monthly'
    
    # Currency Statistics
    total_currency_in_circulation = db.Column(db.BigInteger, default=0, nullable=False)
    currency_type = db.Column(db.String(30), nullable=False)
    
    # Transaction Statistics
    total_transactions = db.Column(db.Integer, default=0, nullable=False)
    total_transaction_volume = db.Column(db.BigInteger, default=0, nullable=False)
    average_transaction_size = db.Column(db.BigInteger, default=0, nullable=False)
    
    # Marketplace Statistics
    total_active_listings = db.Column(db.Integer, default=0, nullable=False)
    total_items_listed = db.Column(db.Integer, default=0, nullable=False)
    marketplace_volume = db.Column(db.BigInteger, default=0, nullable=False)
    
    # Player Economy
    total_player_wealth = db.Column(db.BigInteger, default=0, nullable=False)
    average_player_wealth = db.Column(db.BigInteger, default=0, nullable=False)
    gini_coefficient = db.Column(db.Float, default=0.0, nullable=False)  # Wealth inequality
    
    # Price Index
    price_index = db.Column(db.Float, default=100.0, nullable=False)  # Base 100
    price_change_percent = db.Column(db.Float, default=0.0, nullable=False)
    
    # Item Category Prices
    item_category_prices = db.Column(JSONB, default={}, nullable=False)
    # {category: average_price}
    
    # Faction Economy
    total_faction_wealth = db.Column(db.BigInteger, default=0, nullable=False)
    faction_economic_distribution = db.Column(JSONB, default={}, nullable=False)
    # {faction_id: total_wealth}
    
    # Market Health Indicators
    liquidity_index = db.Column(db.Float, default=0.0, nullable=False)  # 0-1
    market_volatility = db.Column(db.Float, default=0.0, nullable=False)  # 0-1
    
    # Metadata
    metadata = db.Column(JSONB, default={}, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f'<EconomySnapshot {self.period} {self.snapshot_date.date()}>'
    
    def to_dict(self) -> dict:
        """Convert EconomySnapshot to dictionary"""
        return {
            'id': str(self.id),
            'date': self.snapshot_date.isoformat(),
            'period': self.period,
            'total_transactions': self.total_transactions,
            'transaction_volume': self.total_transaction_volume,
            'active_listings': self.total_active_listings,
            'price_index': self.price_index,
            'liquidity': self.liquidity_index,
            'volatility': self.market_volatility,
            'gini_coefficient': self.gini_coefficient
        }


class PriceHistory(db.Model):
    """
    Price History Model
    
    Tracks historical prices of items for market analysis
    """
    
    __tablename__ = 'price_history'
    
    # Primary Key
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    
    # Item Reference
    item_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    item_name = db.Column(db.String(200), nullable=False)
    item_category = db.Column(db.String(100), nullable=False, index=True)
    
    # Price Data
    price_min = db.Column(db.BigInteger, nullable=False)
    price_max = db.Column(db.BigInteger, nullable=False)
    price_average = db.Column(db.BigInteger, nullable=False)
    price_median = db.Column(db.BigInteger, nullable=False)
    
    # Volume Data
    transaction_count = db.Column(db.Integer, default=0, nullable=False)
    transaction_volume = db.Column(db.BigInteger, default=0, nullable=False)
    items_traded = db.Column(db.Integer, default=0, nullable=False)
    
    # Currency Type
    currency_type = db.Column(db.String(30), nullable=False)
    
    # Time Period
    period_start = db.Column(db.DateTime, nullable=False, index=True)
    period_end = db.Column(db.DateTime, nullable=False)
    period_type = db.Column(db.String(20), nullable=False)  # 'hourly', 'daily', 'weekly'
    
    # Trend Analysis
    price_trend = db.Column(db.String(20), nullable=False)  # 'up', 'down', 'stable'
    price_change_percent = db.Column(db.Float, default=0.0, nullable=False)
    
    # Metadata
    metadata = db.Column(JSONB, default={}, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f'<PriceHistory {self.item_name} {self.period_start.date()}>'
    
    def to_dict(self) -> dict:
        """Convert PriceHistory to dictionary"""
        return {
            'id': str(self.id),
            'item_name': self.item_name,
            'category': self.item_category,
            'price_min': self.price_min,
            'price_max': self.price_max,
            'price_average': self.price_average,
            'price_median': self.price_median,
            'transaction_count': self.transaction_count,
            'items_traded': self.items_traded,
            'trend': self.price_trend,
            'change_percent': self.price_change_percent,
            'period_type': self.period_type
        }
