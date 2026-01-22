"""
ChronoRift Economy Routes
Handles trading, marketplace, currency exchange, and economic transactions
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import uuid
import math

from app.models import db, Riftwalker, Transaction, MarketplaceListing, EconomySnapshot, PriceHistory, Item
from app.schemas import transaction_schema, transactions_schema, marketplace_listing_schema, marketplace_listings_schema
from app.utils.decorators import validate_json, rate_limit


economy_bp = Blueprint('economy', __name__, url_prefix='/api/economy')


# ============================================================================
# CURRENCY & WALLET MANAGEMENT
# ============================================================================

@economy_bp.route('/wallet', methods=['GET'])
@jwt_required()
def get_wallet():
    """
    Get player's currency wallet
    
    Headers:
    Authorization: Bearer {access_token}
    
    Response:
    {
        "success": bool,
        "data": {
            "chronons": int,
            "essence": int,
            "faction_marks": int,
            "realm_tokens": int,
            "total_wealth": int,
            "last_transaction": "ISO timestamp or null"
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        player = Riftwalker.query.get(player_id)
        
        if not player:
            return jsonify({
                'success': False,
                'message': 'Player not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'chronons': player.chronons or 0,
                'essence': player.essence or 0,
                'faction_marks': player.faction_marks or 0,
                'realm_tokens': player.realm_tokens or 0,
                'total_wealth': (player.chronons or 0) + (player.essence or 0),
                'last_transaction': player.last_transaction.isoformat() if player.last_transaction else None
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve wallet: {str(e)}'
        }), 500


@economy_bp.route('/transfer', methods=['POST'])
@jwt_required()
@validate_json
@rate_limit(limit=20, window=3600)
def transfer_currency():
    """
    Transfer currency to another player
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "recipient_id": "uuid",
        "currency_type": "string (chronons, essence, faction_marks, realm_tokens)",
        "amount": int
    }
    
    Response:
    {
        "success": bool,
        "message": "string",
        "data": {
            "transaction_id": "uuid",
            "sender_balance": int,
            "recipient_balance": int,
            "amount": int,
            "fee_charged": int,
            "completed_at": "ISO timestamp"
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        sender = Riftwalker.query.get(player_id)
        
        if not sender:
            return jsonify({
                'success': False,
                'message': 'Sender not found'
            }), 404
        
        data = request.get_json()
        recipient_id = data.get('recipient_id')
        currency_type = data.get('currency_type', 'chronons')
        amount = data.get('amount', 0)
        
        # Validate amount
        if amount <= 0:
            return jsonify({
                'success': False,
                'message': 'Amount must be positive'
            }), 400
        
        # Get recipient
        recipient = Riftwalker.query.get(recipient_id)
        if not recipient:
            return jsonify({
                'success': False,
                'message': 'Recipient not found'
            }), 404
        
        # Check balance
        sender_balance_attr = currency_type
        if not hasattr(sender, sender_balance_attr) or getattr(sender, sender_balance_attr, 0) < amount:
            return jsonify({
                'success': False,
                'message': f'Insufficient {currency_type}'
            }), 400
        
        # Calculate fee (2% transfer fee)
        fee = max(1, int(amount * 0.02))
        total_deduction = amount + fee
        
        # Create transaction record
        transaction = Transaction(
            id=uuid.uuid4(),
            initiator_id=player_id,
            recipient_id=recipient_id,
            transaction_type='player_trade',
            status='completed',
            currency_type=currency_type,
            amount=amount,
            transaction_fee=fee,
            net_amount=amount,
            description=f'Transfer to {recipient.character_name}',
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        
        # Update balances
        setattr(sender, sender_balance_attr, getattr(sender, sender_balance_attr, 0) - total_deduction)
        setattr(recipient, sender_balance_attr, getattr(recipient, sender_balance_attr, 0) + amount)
        
        sender.last_transaction = datetime.utcnow()
        recipient.last_transaction = datetime.utcnow()
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Currency transferred successfully',
            'data': {
                'transaction_id': str(transaction.id),
                'sender_balance': getattr(sender, sender_balance_attr, 0),
                'recipient_balance': getattr(recipient, sender_balance_attr, 0),
                'amount': amount,
                'fee_charged': fee,
                'completed_at': transaction.completed_at.isoformat()
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Transfer failed: {str(e)}'
        }), 500


@economy_bp.route('/exchange', methods=['POST'])
@jwt_required()
@validate_json
def exchange_currency():
    """
    Exchange one currency type for another
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "source_currency": "string",
        "target_currency": "string",
        "source_amount": int
    }
    
    Response:
    {
        "success": bool,
        "data": {
            "source_amount": int,
            "target_amount": int,
            "exchange_rate": float,
            "fee_charged": int,
            "new_balances": {...}
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        player = Riftwalker.query.get(player_id)
        
        if not player:
            return jsonify({
                'success': False,
                'message': 'Player not found'
            }), 404
        
        data = request.get_json()
        source_currency = data.get('source_currency')
        target_currency = data.get('target_currency')
        source_amount = data.get('source_amount', 0)
        
        # Exchange rates (simplified, would be dynamic in production)
        exchange_rates = {
            'chronons_to_essence': 0.1,
            'essence_to_chronons': 10.0,
            'chronons_to_faction_marks': 0.05,
            'chronons_to_realm_tokens': 0.02
        }
        
        rate_key = f'{source_currency}_to_{target_currency}'
        if rate_key not in exchange_rates:
            return jsonify({
                'success': False,
                'message': 'Invalid currency exchange pair'
            }), 400
        
        exchange_rate = exchange_rates[rate_key]
        target_amount = int(source_amount * exchange_rate)
        fee = max(1, int(source_amount * 0.05))
        
        # Check balance
        if getattr(player, source_currency, 0) < (source_amount + fee):
            return jsonify({
                'success': False,
                'message': 'Insufficient source currency'
            }), 400
        
        # Update balances
        setattr(player, source_currency, getattr(player, source_currency, 0) - source_amount - fee)
        setattr(player, target_currency, getattr(player, target_currency, 0) + target_amount)
        
        # Create transaction
        transaction = Transaction(
            id=uuid.uuid4(),
            initiator_id=player_id,
            transaction_type='player_trade',
            status='completed',
            source_currency=source_currency,
            target_currency=target_currency,
            amount=source_amount,
            transaction_fee=fee,
            exchange_rate=exchange_rate,
            net_amount=target_amount,
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'source_amount': source_amount,
                'target_amount': target_amount,
                'exchange_rate': exchange_rate,
                'fee_charged': fee,
                'new_balances': {
                    'chronons': player.chronons or 0,
                    'essence': player.essence or 0,
                    'faction_marks': player.faction_marks or 0,
                    'realm_tokens': player.realm_tokens or 0
                }
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Currency exchange failed: {str(e)}'
        }), 500


# ============================================================================
# MARKETPLACE LISTINGS
# ============================================================================

@economy_bp.route('/listings', methods=['GET'])
def list_marketplace_items():
    """
    List marketplace listings with filtering
    
    Query Parameters:
    item_name - string (partial match search)
    rarity - string (common, uncommon, rare, legendary)
    price_min - int
    price_max - int
    currency - string (chronons, essence)
    seller_id - uuid (filter by seller)
    limit - int (default 50, max 100)
    offset - int (default 0)
    
    Response:
    {
        "success": bool,
        "data": [
            {
                "id": "uuid",
                "item_name": "string",
                "item_rarity": "string",
                "quantity": int,
                "unit_price": int,
                "currency_type": "string",
                "seller_id": "uuid",
                "seller_name": "string",
                "created_at": "ISO timestamp",
                "expires_at": "ISO timestamp or null",
                "views": int
            }
        ],
        "pagination": {...}
    }
    """
    try:
        query = MarketplaceListing.query.filter_by(is_active=True)
        
        # Apply filters
        item_name = request.args.get('item_name', type=str)
        if item_name:
            query = query.filter(MarketplaceListing.item_name.ilike(f'%{item_name}%'))
        
        rarity = request.args.get('rarity', type=str)
        if rarity:
            query = query.filter_by(item_rarity=rarity)
        
        price_min = request.args.get('price_min', type=int)
        if price_min:
            query = query.filter(MarketplaceListing.unit_price >= price_min)
        
        price_max = request.args.get('price_max', type=int)
        if price_max:
            query = query.filter(MarketplaceListing.unit_price <= price_max)
        
        currency = request.args.get('currency', type=str)
        if currency:
            query = query.filter_by(currency_type=currency)
        
        # Pagination
        limit = min(request.args.get('limit', 50, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        
        total = query.count()
        listings = query.order_by(MarketplaceListing.created_at.desc()).limit(limit).offset(offset).all()
        
        return jsonify({
            'success': True,
            'data': marketplace_listings_schema.dump(listings),
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to list marketplace items: {str(e)}'
        }), 500


@economy_bp.route('/listings', methods=['POST'])
@jwt_required()
@validate_json
@rate_limit(limit=30, window=3600)
def create_listing():
    """
    Create a marketplace listing
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "item_id": "uuid",
        "item_name": "string",
        "item_rarity": "string (common, uncommon, rare, legendary)",
        "quantity": int,
        "unit_price": int,
        "currency_type": "string (chronons, essence)",
        "listing_duration_hours": int (default 168),
        "description": "string (optional)"
    }
    
    Response:
    {
        "success": bool,
        "message": "string",
        "data": {
            "listing_id": "uuid",
            "item_name": "string",
            "quantity": int,
            "unit_price": int,
            "total_price": int,
            "expires_at": "ISO timestamp"
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        player = Riftwalker.query.get(player_id)
        
        if not player:
            return jsonify({
                'success': False,
                'message': 'Player not found'
            }), 404
        
        data = request.get_json()
        
        # Validate inputs
        if not data.get('item_name') or not data.get('quantity') or not data.get('unit_price'):
            return jsonify({
                'success': False,
                'message': 'Item name, quantity, and price required'
            }), 400
        
        listing_duration = data.get('listing_duration_hours', 168)
        expires_at = datetime.utcnow() + timedelta(hours=listing_duration)
        
        listing = MarketplaceListing(
            id=uuid.uuid4(),
            seller_id=player_id,
            item_id=data.get('item_id', uuid.uuid4()),
            item_name=data['item_name'],
            item_description=data.get('description'),
            item_rarity=data.get('item_rarity', 'common'),
            quantity=data['quantity'],
            quantity_remaining=data['quantity'],
            unit_price=data['unit_price'],
            currency_type=data.get('currency_type', 'chronons'),
            total_price=data['quantity'] * data['unit_price'],
            is_active=True,
            listing_type='sell',
            expires_at=expires_at,
            auto_renew=data.get('auto_renew', False),
            created_at=datetime.utcnow()
        )
        
        db.session.add(listing)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Listing created successfully',
            'data': marketplace_listing_schema.dump(listing)
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Listing creation failed: {str(e)}'
        }), 500


@economy_bp.route('/listings/<listing_id>', methods=['GET'])
def get_listing_details(listing_id):
    """
    Get detailed information about a marketplace listing
    
    URL Parameters:
    listing_id - UUID of listing
    
    Response:
    {
        "success": bool,
        "data": {
            "id": "uuid",
            "item_name": "string",
            "item_rarity": "string",
            "quantity_remaining": int,
            "unit_price": int,
            "total_price": int,
            "seller_id": "uuid",
            "seller_name": "string",
            "seller_reputation": float,
            "description": "string",
            "expires_at": "ISO timestamp",
            "views": int,
            "interactions": int
        }
    }
    """
    try:
        listing = MarketplaceListing.query.get(listing_id)
        
        if not listing:
            return jsonify({
                'success': False,
                'message': 'Listing not found'
            }), 404
        
        # Record view
        listing.record_view()
        db.session.commit()
        
        seller = Riftwalker.query.get(listing.seller_id)
        
        return jsonify({
            'success': True,
            'data': {
                **marketplace_listing_schema.dump(listing),
                'seller_name': seller.character_name if seller else 'Unknown',
                'seller_reputation': seller.reputation or 0.0 if seller else 0.0
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve listing: {str(e)}'
        }), 500


@economy_bp.route('/listings/<listing_id>/purchase', methods=['POST'])
@jwt_required()
@validate_json
@rate_limit(limit=50, window=3600)
def purchase_from_listing(listing_id):
    """
    Purchase items from marketplace listing
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "quantity": int
    }
    
    Response:
    {
        "success": bool,
        "message": "string",
        "data": {
            "transaction_id": "uuid",
            "items_purchased": int,
            "total_cost": int,
            "seller_received": int,
            "fee_charged": int
        }
    }
    """
    try:
        buyer_id = get_jwt_identity()
        buyer = Riftwalker.query.get(buyer_id)
        
        if not buyer:
            return jsonify({
                'success': False,
                'message': 'Buyer not found'
            }), 404
        
        listing = MarketplaceListing.query.get(listing_id)
        if not listing or not listing.is_active:
            return jsonify({
                'success': False,
                'message': 'Listing not found or inactive'
            }), 404
        
        data = request.get_json()
        quantity = data.get('quantity', 1)
        
        if quantity <= 0 or quantity > listing.quantity_remaining:
            return jsonify({
                'success': False,
                'message': f'Invalid quantity (available: {listing.quantity_remaining})'
            }), 400
        
        # Calculate cost
        total_cost = listing.unit_price * quantity
        fee = max(1, int(total_cost * 0.05))  # 5% marketplace fee
        seller_received = total_cost - fee
        
        # Check buyer balance
        currency_attr = listing.currency_type
        if getattr(buyer, currency_attr, 0) < total_cost:
            return jsonify({
                'success': False,
                'message': f'Insufficient {currency_attr}'
            }), 400
        
        # Get seller
        seller = Riftwalker.query.get(listing.seller_id)
        if not seller:
            return jsonify({
                'success': False,
                'message': 'Seller not found'
            }), 404
        
        # Process transaction
        transaction = Transaction(
            id=uuid.uuid4(),
            initiator_id=buyer_id,
            recipient_id=listing.seller_id,
            transaction_type='marketplace_sale',
            status='completed',
            currency_type=listing.currency_type,
            amount=total_cost,
            transaction_fee=fee,
            net_amount=seller_received,
            marketplace_listing_id=listing.id,
            items_given={},
            items_received={str(listing.item_id): quantity},
            listing_price=listing.unit_price,
            listing_quantity=listing.quantity,
            quantity_purchased=quantity,
            description=f'Purchased {quantity}x {listing.item_name}',
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        
        # Update balances
        setattr(buyer, currency_attr, getattr(buyer, currency_attr, 0) - total_cost)
        setattr(seller, currency_attr, getattr(seller, currency_attr, 0) + seller_received)
        
        # Update listing
        listing.update_quantity(quantity)
        listing.record_interaction()
        
        # Update player reputation
        seller.reputation = (seller.reputation or 0.0) + 0.1
        
        buyer.last_transaction = datetime.utcnow()
        seller.last_transaction = datetime.utcnow()
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Purchase completed successfully',
            'data': {
                'transaction_id': str(transaction.id),
                'items_purchased': quantity,
                'total_cost': total_cost,
                'seller_received': seller_received,
                'fee_charged': fee
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Purchase failed: {str(e)}'
        }), 500


@economy_bp.route('/listings/<listing_id>', methods=['DELETE'])
@jwt_required()
def cancel_listing(listing_id):
    """
    Cancel an active marketplace listing
    
    Headers:
    Authorization: Bearer {access_token}
    
    Response:
    {
        "success": bool,
        "message": "string"
    }
    """
    try:
        player_id = get_jwt_identity()
        
        listing = MarketplaceListing.query.get(listing_id)
        if not listing:
            return jsonify({
                'success': False,
                'message': 'Listing not found'
            }), 404
        
        if str(listing.seller_id) != player_id:
            return jsonify({
                'success': False,
                'message': 'Unauthorized'
            }), 403
        
        listing.is_active = False
        listing.delisted_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Listing cancelled'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Cancellation failed: {str(e)}'
        }), 500


# ============================================================================
# TRANSACTION HISTORY & ANALYTICS
# ============================================================================

@economy_bp.route('/transactions', methods=['GET'])
@jwt_required()
def get_transaction_history():
    """
    Get player's transaction history
    
    Headers:
    Authorization: Bearer {access_token}
    
    Query Parameters:
    transaction_type - string (filter)
    currency - string (filter)
    limit - int (default 50, max 100)
    offset - int (default 0)
    
    Response:
    {
        "success": bool,
        "data": [
            {
                "id": "uuid",
                "type": "string",
                "amount": int,
                "net_amount": int,
                "fee": int,
                "counterparty_id": "uuid or null",
                "created_at": "ISO timestamp"
            }
        ],
        "pagination": {...}
    }
    """
    try:
        player_id = get_jwt_identity()
        
        query = Transaction.query.filter(
            (Transaction.initiator_id == player_id) | (Transaction.recipient_id == player_id)
        )
        
        # Apply filters
        transaction_type = request.args.get('transaction_type', type=str)
        if transaction_type:
            query = query.filter_by(transaction_type=transaction_type)
        
        # Pagination
        limit = min(request.args.get('limit', 50, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        
        total = query.count()
        transactions = query.order_by(Transaction.created_at.desc()).limit(limit).offset(offset).all()
        
        return jsonify({
            'success': True,
            'data': transactions_schema.dump(transactions),
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve transactions: {str(e)}'
        }), 500


# ============================================================================
# ECONOMY STATISTICS & PRICING
# ============================================================================

@economy_bp.route('/statistics', methods=['GET'])
def get_economy_statistics():
    """
    Get global economy statistics
    
    Response:
    {
        "success": bool,
        "data": {
            "total_transactions": int,
            "total_volume": int,
            "active_listings": int,
            "average_item_price": float,
            "price_index": float,
            "market_health": "string (healthy, stable, volatile, crashed)"
        }
    }
    """
    try:
        # Get latest snapshot
        snapshot = EconomySnapshot.query.order_by(EconomySnapshot.snapshot_date.desc()).first()
        
        if not snapshot:
            snapshot = EconomySnapshot(
                id=uuid.uuid4(),
                snapshot_date=datetime.utcnow(),
                period='daily',
                currency_type='chronons'
            )
            db.session.add(snapshot)
            db.session.commit()
        
        # Determine market health
        if snapshot.market_volatility > 0.7:
            health = 'crashed'
        elif snapshot.market_volatility > 0.5:
            health = 'volatile'
        elif snapshot.liquidity_index > 0.7:
            health = 'healthy'
        else:
            health = 'stable'
        
        return jsonify({
            'success': True,
            'data': {
                'total_transactions': snapshot.total_transactions,
                'total_volume': snapshot.total_transaction_volume,
                'active_listings': snapshot.total_active_listings,
                'average_item_price': snapshot.average_transaction_size,
                'price_index': snapshot.price_index,
                'market_health': health,
                'liquidity_index': round(snapshot.liquidity_index, 3),
                'volatility': round(snapshot.market_volatility, 3),
                'last_updated': snapshot.created_at.isoformat()
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve statistics: {str(e)}'
        }), 500


@economy_bp.route('/price-history/<item_id>', methods=['GET'])
def get_item_price_history(item_id):
    """
    Get price history for an item
    
    URL Parameters:
    item_id - UUID of item
    
    Query Parameters:
    period - string (hourly, daily, weekly)
    limit - int (default 50)
    
    Response:
    {
        "success": bool,
        "data": [
            {
                "period": "ISO date or hour",
                "price_min": int,
                "price_max": int,
                "price_average": int,
                "transaction_count": int,
                "trend": "string (up, down, stable)"
            }
        ]
    }
    """
    try:
        period = request.args.get('period', 'daily', type=str)
        limit = min(request.args.get('limit', 50, type=int), 100)
        
        history = PriceHistory.query.filter_by(
            item_id=item_id,
            period_type=period
        ).order_by(PriceHistory.period_start.desc()).limit(limit).all()
        
        data = [
            {
                'period': h.period_start.isoformat(),
                'price_min': h.price_min,
                'price_max': h.price_max,
                'price_average': h.price_average,
                'transaction_count': h.transaction_count,
                'trend': h.price_trend,
                'change_percent': h.price_change_percent
            }
            for h in history
        ]
        
        return jsonify({
            'success': True,
            'data': data
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve price history: {str(e)}'
        }), 500


@economy_bp.route('/leaderboards/richest', methods=['GET'])
def get_richest_players():
    """
    Get leaderboard of richest players
    
    Query Parameters:
    limit - int (default 50, max 100)
    
    Response:
    {
        "success": bool,
        "data": [
            {
                "rank": int,
                "player_name": "string",
                "total_wealth": int,
                "chronons": int,
                "essence": int,
                "level": int
            }
        ]
    }
    """
    try:
        limit = min(request.args.get('limit', 50, type=int), 100)
        
        players = Riftwalker.query.filter_by(is_active=True).all()
        
        # Calculate total wealth and sort
        player_wealth = [
            {
                'player': p,
                'wealth': (p.chronons or 0) + (p.essence or 0) * 10  # Essence worth more
            }
            for p in players
        ]
        
        player_wealth.sort(key=lambda x: x['wealth'], reverse=True)
        
        leaderboard = [
            {
                'rank': i + 1,
                'player_name': pw['player'].character_name,
                'total_wealth': pw['wealth'],
                'chronons': pw['player'].chronons or 0,
                'essence': pw['player'].essence or 0,
                'level': pw['player'].level
            }
            for i, pw in enumerate(player_wealth[:limit])
        ]
        
        return jsonify({
            'success': True,
            'data': leaderboard
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve leaderboard: {str(e)}'
        }), 500

