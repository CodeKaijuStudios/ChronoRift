"""
ChronoRift Social Routes
Handles guilds, factions, chat, social interactions, and player relationships
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import uuid

from app.models import db, Guild, Faction, Riftwalker, Message, GuildMember, FactionMember
from app.schemas import guild_schema, guilds_schema, faction_schema, message_schema, messages_schema
from app.utils.decorators import validate_json, rate_limit


social_bp = Blueprint('social', __name__, url_prefix='/api/social')


# ============================================================================
# GUILD MANAGEMENT
# ============================================================================

@social_bp.route('/guilds', methods=['POST'])
@jwt_required()
@validate_json
def create_guild():
    """
    Create a new guild
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "guild_name": "string (3-50 chars)",
        "description": "string",
        "color_primary": "string (hex color)",
        "logo_url": "string (optional)"
    }
    
    Response:
    {
        "success": bool,
        "message": "string",
        "data": {
            "guild_id": "uuid",
            "guild_name": "string",
            "leader_id": "uuid",
            "member_count": 1,
            "created_at": "ISO timestamp"
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        data = request.get_json()
        
        # Validation
        guild_name = data.get('guild_name', '').strip()
        if not guild_name or len(guild_name) < 3 or len(guild_name) > 50:
            return jsonify({
                'success': False,
                'message': 'Guild name must be between 3 and 50 characters'
            }), 400
        
        # Check for duplicate name
        existing = Guild.query.filter_by(name=guild_name).first()
        if existing:
            return jsonify({
                'success': False,
                'message': 'Guild name already taken'
            }), 409
        
        # Create guild
        guild = Guild(
            id=uuid.uuid4(),
            name=guild_name,
            description=data.get('description', ''),
            leader_id=player_id,
            logo_url=data.get('logo_url'),
            color_primary=data.get('color_primary', '#3182ce'),
            member_count=1,
            max_members=100
        )
        
        db.session.add(guild)
        db.session.flush()
        
        # Add leader as member
        member = GuildMember(
            id=uuid.uuid4(),
            guild_id=guild.id,
            character_id=player_id,
            role='leader',
            joined_at=datetime.utcnow()
        )
        
        db.session.add(member)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Guild {guild_name} created successfully',
            'data': guild_schema.dump(guild)
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Guild creation failed: {str(e)}'
        }), 500


@social_bp.route('/guilds', methods=['GET'])
def list_guilds():
    """
    List guilds with filtering
    
    Query Parameters:
    search - string (guild name search)
    level_min - int (minimum guild level)
    member_count_min - int
    limit - int (default 50, max 100)
    offset - int (default 0)
    
    Response:
    {
        "success": bool,
        "data": [
            {
                "id": "uuid",
                "name": "string",
                "description": "string",
                "leader_id": "uuid",
                "member_count": int,
                "guild_level": int,
                "color": "string",
                "created_at": "ISO timestamp"
            }
        ],
        "pagination": {...}
    }
    """
    try:
        query = Guild.query
        
        # Apply filters
        search = request.args.get('search', type=str)
        if search:
            query = query.filter(Guild.name.ilike(f'%{search}%'))
        
        level_min = request.args.get('level_min', type=int)
        if level_min:
            query = query.filter(Guild.guild_level >= level_min)
        
        member_min = request.args.get('member_count_min', type=int)
        if member_min:
            query = query.filter(Guild.member_count >= member_min)
        
        # Pagination
        limit = min(request.args.get('limit', 50, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        
        total = query.count()
        guilds = query.order_by(Guild.guild_level.desc(), Guild.member_count.desc()).limit(limit).offset(offset).all()
        
        return jsonify({
            'success': True,
            'data': guilds_schema.dump(guilds),
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to list guilds: {str(e)}'
        }), 500


@social_bp.route('/guilds/<guild_id>', methods=['GET'])
def get_guild_details(guild_id):
    """
    Get detailed guild information
    
    URL Parameters:
    guild_id - UUID of guild
    
    Response:
    {
        "success": bool,
        "data": {
            "id": "uuid",
            "name": "string",
            "description": "string",
            "leader_id": "uuid",
            "leader_name": "string",
            "member_count": int,
            "max_members": int,
            "guild_level": int,
            "treasury": int,
            "perks": [...],
            "created_at": "ISO timestamp",
            "recruitment_open": bool
        }
    }
    """
    try:
        guild = Guild.query.get(guild_id)
        
        if not guild:
            return jsonify({
                'success': False,
                'message': 'Guild not found'
            }), 404
        
        leader = Riftwalker.query.get(guild.leader_id)
        
        return jsonify({
            'success': True,
            'data': {
                **guild_schema.dump(guild),
                'leader_name': leader.character_name if leader else 'Unknown',
                'recruitment_open': guild.member_count < guild.max_members
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve guild: {str(e)}'
        }), 500


@social_bp.route('/guilds/<guild_id>/join', methods=['POST'])
@jwt_required()
def join_guild(guild_id):
    """
    Request to join a guild
    
    Headers:
    Authorization: Bearer {access_token}
    
    Response:
    {
        "success": bool,
        "message": "string",
        "data": {
            "guild_id": "uuid",
            "guild_name": "string",
            "member_count": int
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        
        guild = Guild.query.get(guild_id)
        if not guild:
            return jsonify({
                'success': False,
                'message': 'Guild not found'
            }), 404
        
        # Check if already member
        existing = GuildMember.query.filter_by(guild_id=guild_id, character_id=player_id).first()
        if existing:
            return jsonify({
                'success': False,
                'message': 'Already a guild member'
            }), 409
        
        # Check capacity
        if guild.member_count >= guild.max_members:
            return jsonify({
                'success': False,
                'message': 'Guild is full'
            }), 400
        
        # Add member
        member = GuildMember(
            id=uuid.uuid4(),
            guild_id=guild_id,
            character_id=player_id,
            role='member',
            joined_at=datetime.utcnow()
        )
        
        guild.member_count += 1
        
        db.session.add(member)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Joined guild {guild.name}',
            'data': {
                'guild_id': str(guild.id),
                'guild_name': guild.name,
                'member_count': guild.member_count
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to join guild: {str(e)}'
        }), 500


@social_bp.route('/guilds/<guild_id>/leave', methods=['POST'])
@jwt_required()
def leave_guild(guild_id):
    """
    Leave current guild
    
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
        
        guild = Guild.query.get(guild_id)
        if not guild:
            return jsonify({
                'success': False,
                'message': 'Guild not found'
            }), 404
        
        member = GuildMember.query.filter_by(guild_id=guild_id, character_id=player_id).first()
        if not member:
            return jsonify({
                'success': False,
                'message': 'Not a guild member'
            }), 400
        
        if member.role == 'leader':
            return jsonify({
                'success': False,
                'message': 'Leader cannot leave. Transfer leadership first.'
            }), 403
        
        db.session.delete(member)
        guild.member_count = max(0, guild.member_count - 1)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Left guild {guild.name}'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to leave guild: {str(e)}'
        }), 500


@social_bp.route('/guilds/<guild_id>/members', methods=['GET'])
def get_guild_members(guild_id):
    """
    Get guild member list
    
    URL Parameters:
    guild_id - UUID of guild
    
    Query Parameters:
    role - string (leader, officer, member)
    limit - int (default 50)
    offset - int (default 0)
    
    Response:
    {
        "success": bool,
        "data": [
            {
                "character_id": "uuid",
                "character_name": "string",
                "role": "string",
                "level": int,
                "joined_at": "ISO timestamp",
                "contribution_points": int
            }
        ]
    }
    """
    try:
        query = GuildMember.query.filter_by(guild_id=guild_id)
        
        # Apply role filter
        role = request.args.get('role', type=str)
        if role:
            query = query.filter_by(role=role)
        
        # Pagination
        limit = min(request.args.get('limit', 50, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        
        members = query.order_by(GuildMember.role.desc()).limit(limit).offset(offset).all()
        
        members_data = []
        for member in members:
            character = Riftwalker.query.get(member.character_id)
            if character:
                members_data.append({
                    'character_id': str(member.character_id),
                    'character_name': character.character_name,
                    'role': member.role,
                    'level': character.level,
                    'joined_at': member.joined_at.isoformat(),
                    'contribution_points': member.contribution_points or 0
                })
        
        return jsonify({
            'success': True,
            'data': members_data
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve members: {str(e)}'
        }), 500


# ============================================================================
# FACTION OPERATIONS
# ============================================================================

@social_bp.route('/factions', methods=['GET'])
def list_factions():
    """
    List all factions
    
    Query Parameters:
    alignment - string (lawful, neutral, chaotic)
    limit - int (default 50)
    
    Response:
    {
        "success": bool,
        "data": [
            {
                "id": "uuid",
                "name": "string",
                "description": "string",
                "alignment": "string",
                "member_count": int,
                "total_influence": int,
                "color": "string",
                "is_at_war": bool
            }
        ]
    }
    """
    try:
        query = Faction.query.filter_by(is_active=True)
        
        # Apply alignment filter
        alignment = request.args.get('alignment', type=str)
        if alignment:
            query = query.filter_by(alignment=alignment)
        
        limit = min(request.args.get('limit', 50, type=int), 100)
        
        factions = query.order_by(Faction.total_influence.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'data': factions_schema.dump(factions) if hasattr(self, 'factions_schema') else [faction_schema.dump(f) for f in factions]
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to list factions: {str(e)}'
        }), 500


@social_bp.route('/factions/<faction_id>', methods=['GET'])
def get_faction_details(faction_id):
    """
    Get faction details with member info
    
    URL Parameters:
    faction_id - UUID of faction
    
    Response:
    {
        "success": bool,
        "data": {
            "id": "uuid",
            "name": "string",
            "description": "string",
            "ideology": "string",
            "alignment": "string",
            "member_count": int,
            "total_influence": int,
            "leader_id": "uuid",
            "leader_name": "string",
            "council_members": int,
            "rifts_sealed": int,
            "total_battles_won": int,
            "at_war": bool,
            "war_opponent": "string or null"
        }
    }
    """
    try:
        faction = Faction.query.get(faction_id)
        
        if not faction:
            return jsonify({
                'success': False,
                'message': 'Faction not found'
            }), 404
        
        leader = Riftwalker.query.get(faction.leader_id) if faction.leader_id else None
        opponent = Faction.query.get(faction.war_against_faction_id) if faction.war_against_faction_id else None
        
        return jsonify({
            'success': True,
            'data': {
                **faction_schema.dump(faction),
                'leader_name': leader.character_name if leader else 'Vacant',
                'council_members': len(faction.council_member_ids or []),
                'war_opponent': opponent.name if opponent else None
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve faction: {str(e)}'
        }), 500


# ============================================================================
# CHAT & MESSAGING
# ============================================================================

@social_bp.route('/chat/guild/<guild_id>', methods=['GET'])
@jwt_required()
def get_guild_chat(guild_id):
    """
    Get guild chat messages
    
    Headers:
    Authorization: Bearer {access_token}
    
    URL Parameters:
    guild_id - UUID of guild
    
    Query Parameters:
    limit - int (default 50, max 100)
    offset - int (default 0)
    
    Response:
    {
        "success": bool,
        "data": [
            {
                "id": "uuid",
                "sender_id": "uuid",
                "sender_name": "string",
                "content": "string",
                "created_at": "ISO timestamp"
            }
        ]
    }
    """
    try:
        player_id = get_jwt_identity()
        
        # Verify player is guild member
        member = GuildMember.query.filter_by(guild_id=guild_id, character_id=player_id).first()
        if not member:
            return jsonify({
                'success': False,
                'message': 'Not a guild member'
            }), 403
        
        # Get messages
        limit = min(request.args.get('limit', 50, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        
        messages = Message.query.filter_by(
            guild_id=guild_id,
            message_type='guild'
        ).order_by(Message.created_at.desc()).limit(limit).offset(offset).all()
        
        return jsonify({
            'success': True,
            'data': messages_schema.dump(messages[::-1])  # Reverse for chronological order
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve chat: {str(e)}'
        }), 500


@social_bp.route('/chat/guild/<guild_id>/send', methods=['POST'])
@jwt_required()
@validate_json
@rate_limit(limit=30, window=60)
def send_guild_message(guild_id):
    """
    Send message to guild chat
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "content": "string (max 500 chars)"
    }
    
    Response:
    {
        "success": bool,
        "data": {
            "message_id": "uuid",
            "sender_name": "string",
            "content": "string",
            "created_at": "ISO timestamp"
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        
        # Verify guild membership
        member = GuildMember.query.filter_by(guild_id=guild_id, character_id=player_id).first()
        if not member:
            return jsonify({
                'success': False,
                'message': 'Not a guild member'
            }), 403
        
        data = request.get_json()
        content = data.get('content', '').strip()
        
        if not content or len(content) > 500:
            return jsonify({
                'success': False,
                'message': 'Message must be 1-500 characters'
            }), 400
        
        sender = Riftwalker.query.get(player_id)
        
        message = Message(
            id=uuid.uuid4(),
            sender_id=player_id,
            guild_id=guild_id,
            message_type='guild',
            content=content,
            created_at=datetime.utcnow()
        )
        
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'message_id': str(message.id),
                'sender_name': sender.character_name,
                'content': message.content,
                'created_at': message.created_at.isoformat()
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to send message: {str(e)}'
        }), 500


@social_bp.route('/messages/direct', methods=['GET'])
@jwt_required()
def get_direct_messages():
    """
    Get direct messages with a user
    
    Headers:
    Authorization: Bearer {access_token}
    
    Query Parameters:
    user_id - uuid (conversation partner)
    limit - int (default 50)
    
    Response:
    {
        "success": bool,
        "data": [...]
    }
    """
    try:
        player_id = get_jwt_identity()
        user_id = request.args.get('user_id', type=str)
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User ID required'
            }), 400
        
        limit = min(request.args.get('limit', 50, type=int), 100)
        
        messages = Message.query.filter(
            Message.message_type == 'direct',
            ((Message.sender_id == player_id) & (Message.recipient_id == user_id)) |
            ((Message.sender_id == user_id) & (Message.recipient_id == player_id))
        ).order_by(Message.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'data': messages_schema.dump(messages[::-1])
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve messages: {str(e)}'
        }), 500


@social_bp.route('/messages/direct/send', methods=['POST'])
@jwt_required()
@validate_json
@rate_limit(limit=40, window=60)
def send_direct_message():
    """
    Send direct message to player
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "recipient_id": "uuid",
        "content": "string (max 500 chars)"
    }
    
    Response:
    {
        "success": bool,
        "data": {
            "message_id": "uuid",
            "recipient_id": "uuid",
            "sent_at": "ISO timestamp"
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        data = request.get_json()
        
        recipient_id = data.get('recipient_id')
        content = data.get('content', '').strip()
        
        if not recipient_id or not content or len(content) > 500:
            return jsonify({
                'success': False,
                'message': 'Valid recipient and message required'
            }), 400
        
        # Verify recipient exists
        recipient = Riftwalker.query.get(recipient_id)
        if not recipient:
            return jsonify({
                'success': False,
                'message': 'Recipient not found'
            }), 404
        
        message = Message(
            id=uuid.uuid4(),
            sender_id=player_id,
            recipient_id=recipient_id,
            message_type='direct',
            content=content,
            created_at=datetime.utcnow()
        )
        
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'message_id': str(message.id),
                'recipient_id': str(recipient_id),
                'sent_at': message.created_at.isoformat()
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to send message: {str(e)}'
        }), 500


# ============================================================================
# SOCIAL STATISTICS & LEADERBOARDS
# ============================================================================

@social_bp.route('/leaderboards/guilds', methods=['GET'])
def get_guild_leaderboard():
    """
    Get guild leaderboard by level/members
    
    Query Parameters:
    limit - int (default 50)
    
    Response:
    {
        "success": bool,
        "data": [
            {
                "rank": int,
                "guild_name": "string",
                "guild_level": int,
                "member_count": int,
                "leader_name": "string"
            }
        ]
    }
    """
    try:
        limit = min(request.args.get('limit', 50, type=int), 100)
        
        guilds = Guild.query.order_by(
            Guild.guild_level.desc(),
            Guild.member_count.desc()
        ).limit(limit).all()
        
        leaderboard = [
            {
                'rank': i + 1,
                'guild_name': guild.name,
                'guild_level': guild.guild_level,
                'member_count': guild.member_count,
                'leader_id': str(guild.leader_id),
                'treasury': guild.treasury_balance
            }
            for i, guild in enumerate(guilds)
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


@social_bp.route('/player/<player_id>/profile', methods=['GET'])
def get_player_profile(player_id):
    """
    Get player's public profile
    
    URL Parameters:
    player_id - UUID of player
    
    Response:
    {
        "success": bool,
        "data": {
            "character_id": "uuid",
            "character_name": "string",
            "level": int,
            "guild_id": "uuid or null",
            "guild_name": "string or null",
            "faction_id": "uuid or null",
            "faction_name": "string or null",
            "total_battles": int,
            "win_rate": float,
            "created_at": "ISO timestamp"
        }
    }
    """
    try:
        player = Riftwalker.query.get(player_id)
        
        if not player:
            return jsonify({
                'success': False,
                'message': 'Player not found'
            }), 404
        
        guild = Guild.query.get(player.guild_id) if player.guild_id else None
        faction = Faction.query.get(player.faction_id) if player.faction_id else None
        
        return jsonify({
            'success': True,
            'data': {
                'character_id': str(player.id),
                'character_name': player.character_name,
                'level': player.level,
                'guild_id': str(player.guild_id) if player.guild_id else None,
                'guild_name': guild.name if guild else None,
                'faction_id': str(player.faction_id) if player.faction_id else None,
                'faction_name': faction.name if faction else None,
                'exploration_points': player.exploration_points or 0,
                'created_at': player.created_at.isoformat() if player.created_at else None
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve profile: {str(e)}'
        }), 500
