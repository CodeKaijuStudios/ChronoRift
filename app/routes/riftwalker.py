"""
ChronoRift Riftwalker Routes
Handles character management, progression, and player data
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import uuid

from app.models import db, Riftwalker, Faction, Guild, Item, Inventory
from app.schemas import riftwalker_schema, riftwalkers_schema
from app.utils.decorators import validate_json, admin_required


riftwalker_bp = Blueprint('riftwalker', __name__, url_prefix='/api/riftwalkers')


# ============================================================================
# CHARACTER CREATION & MANAGEMENT
# ============================================================================

@riftwalker_bp.route('', methods=['POST'])
@jwt_required()
@validate_json
def create_character():
    """
    Create a new character for the current player
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "character_name": "string (3-50 chars)",
        "class": "string (warrior, rogue, mage, paladin)",
        "appearance": {
            "skin_tone": "string",
            "hair_color": "string",
            "eye_color": "string"
        }
    }
    
    Response:
    {
        "success": bool,
        "message": "string",
        "data": {
            "id": "uuid",
            "character_name": "string",
            "class": "string",
            "level": 1,
            "experience": 0,
            "created_at": "ISO timestamp"
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        data = request.get_json()
        
        # Validation
        if not data.get('character_name') or len(data['character_name']) < 3 or len(data['character_name']) > 50:
            return jsonify({
                'success': False,
                'message': 'Character name must be between 3 and 50 characters'
            }), 400
        
        valid_classes = ['warrior', 'rogue', 'mage', 'paladin']
        if data.get('class') not in valid_classes:
            return jsonify({
                'success': False,
                'message': f'Invalid class. Must be one of: {", ".join(valid_classes)}'
            }), 400
        
        # Check for duplicate name
        existing = Riftwalker.query.filter_by(character_name=data['character_name']).first()
        if existing:
            return jsonify({
                'success': False,
                'message': 'Character name already taken'
            }), 409
        
        # Create character with class-specific stats
        class_stats = {
            'warrior': {'health': 150, 'mana': 20, 'strength': 18, 'intelligence': 8},
            'rogue': {'health': 80, 'mana': 30, 'agility': 18, 'strength': 12},
            'mage': {'health': 60, 'mana': 100, 'intelligence': 18, 'wisdom': 16},
            'paladin': {'health': 120, 'mana': 60, 'strength': 16, 'wisdom': 14}
        }
        
        stats = class_stats[data['class']]
        
        new_character = Riftwalker(
            id=uuid.uuid4(),
            user_id=player_id,
            character_name=data['character_name'],
            class_type=data['class'],
            level=1,
            experience=0,
            health=stats['health'],
            max_health=stats['health'],
            mana=stats.get('mana', 50),
            max_mana=stats.get('mana', 50),
            strength=stats.get('strength', 10),
            agility=stats.get('agility', 10),
            intelligence=stats.get('intelligence', 10),
            wisdom=stats.get('wisdom', 10),
            constitution=stats.get('constitution', 10),
            appearance=data.get('appearance', {}),
            is_active=True
        )
        
        db.session.add(new_character)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Character created successfully',
            'data': riftwalker_schema.dump(new_character)
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Character creation failed: {str(e)}'
        }), 500


@riftwalker_bp.route('/<character_id>', methods=['GET'])
@jwt_required()
def get_character(character_id):
    """
    Get character details
    
    Headers:
    Authorization: Bearer {access_token}
    
    URL Parameters:
    character_id - UUID of character
    
    Response:
    {
        "success": bool,
        "data": {
            "id": "uuid",
            "character_name": "string",
            "class": "string",
            "level": int,
            "experience": int,
            "health": int,
            "mana": int,
            "faction_id": "uuid or null",
            "guild_id": "uuid or null",
            "stats": {...},
            "created_at": "ISO timestamp"
        }
    }
    """
    try:
        character = Riftwalker.query.get(character_id)
        
        if not character:
            return jsonify({
                'success': False,
                'message': 'Character not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': riftwalker_schema.dump(character)
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve character: {str(e)}'
        }), 500


@riftwalker_bp.route('/<character_id>', methods=['PUT'])
@jwt_required()
@validate_json
def update_character(character_id):
    """
    Update character profile
    
    Headers:
    Authorization: Bearer {access_token}
    
    URL Parameters:
    character_id - UUID of character
    
    Request Body:
    {
        "display_name": "string (optional)",
        "bio": "string (optional)",
        "appearance": {
            "skin_tone": "string (optional)",
            "hair_color": "string (optional)"
        }
    }
    
    Response:
    {
        "success": bool,
        "message": "string",
        "data": {...}
    }
    """
    try:
        player_id = get_jwt_identity()
        character = Riftwalker.query.get(character_id)
        
        if not character:
            return jsonify({
                'success': False,
                'message': 'Character not found'
            }), 404
        
        # Verify ownership
        if str(character.user_id) != player_id:
            return jsonify({
                'success': False,
                'message': 'Unauthorized'
            }), 403
        
        data = request.get_json()
        
        if 'display_name' in data:
            character.display_name = data['display_name']
        
        if 'bio' in data:
            character.bio = data['bio']
        
        if 'appearance' in data:
            character.appearance = {**character.appearance, **data['appearance']}
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Character updated',
            'data': riftwalker_schema.dump(character)
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Character update failed: {str(e)}'
        }), 500


@riftwalker_bp.route('/<character_id>/delete', methods=['POST'])
@jwt_required()
@validate_json
def delete_character(character_id):
    """
    Delete/retire a character
    
    Headers:
    Authorization: Bearer {access_token}
    
    URL Parameters:
    character_id - UUID of character
    
    Request Body:
    {
        "confirmation": "DELETE" (required for safety)
    }
    
    Response:
    {
        "success": bool,
        "message": "string"
    }
    """
    try:
        player_id = get_jwt_identity()
        character = Riftwalker.query.get(character_id)
        
        if not character:
            return jsonify({
                'success': False,
                'message': 'Character not found'
            }), 404
        
        if str(character.user_id) != player_id:
            return jsonify({
                'success': False,
                'message': 'Unauthorized'
            }), 403
        
        data = request.get_json()
        if data.get('confirmation') != 'DELETE':
            return jsonify({
                'success': False,
                'message': 'Deletion confirmation required'
            }), 400
        
        # Soft delete
        character.is_active = False
        character.deleted_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Character deleted'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Character deletion failed: {str(e)}'
        }), 500


# ============================================================================
# CHARACTER PROGRESSION
# ============================================================================

@riftwalker_bp.route('/<character_id>/experience', methods=['POST'])
@jwt_required()
@validate_json
def add_experience(character_id):
    """
    Add experience to character (admin/system endpoint)
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "amount": int,
        "source": "string (quest, battle, exploration, etc)"
    }
    
    Response:
    {
        "success": bool,
        "data": {
            "experience": int,
            "level": int,
            "level_up": bool
        }
    }
    """
    try:
        character = Riftwalker.query.get(character_id)
        
        if not character:
            return jsonify({
                'success': False,
                'message': 'Character not found'
            }), 404
        
        data = request.get_json()
        amount = data.get('amount', 0)
        source = data.get('source', 'unknown')
        
        if amount <= 0:
            return jsonify({
                'success': False,
                'message': 'Experience amount must be positive'
            }), 400
        
        old_level = character.level
        character.experience += amount
        
        # Level up calculation (simplified: 1000 exp per level)
        experience_for_next_level = (character.level + 1) * 1000
        level_up = False
        
        while character.experience >= experience_for_next_level:
            character.level += 1
            character.experience -= experience_for_next_level
            experience_for_next_level = (character.level + 1) * 1000
            level_up = True
            
            # Stat increases on level up
            character.max_health += 10
            character.health = character.max_health
            character.max_mana += 5
            character.mana = character.max_mana
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'experience': character.experience,
                'level': character.level,
                'level_up': level_up,
                'previous_level': old_level
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Experience update failed: {str(e)}'
        }), 500


@riftwalker_bp.route('/<character_id>/level', methods=['GET'])
def get_level_info(character_id):
    """
    Get character level and progression info
    
    URL Parameters:
    character_id - UUID of character
    
    Response:
    {
        "success": bool,
        "data": {
            "level": int,
            "experience": int,
            "experience_for_next_level": int,
            "progress_percentage": float
        }
    }
    """
    try:
        character = Riftwalker.query.get(character_id)
        
        if not character:
            return jsonify({
                'success': False,
                'message': 'Character not found'
            }), 404
        
        exp_for_next = (character.level + 1) * 1000
        progress = (character.experience / exp_for_next * 100) if exp_for_next > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'level': character.level,
                'experience': character.experience,
                'experience_for_next_level': exp_for_next,
                'progress_percentage': min(100.0, progress)
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve level info: {str(e)}'
        }), 500


# ============================================================================
# CHARACTER STATS & ABILITIES
# ============================================================================

@riftwalker_bp.route('/<character_id>/stats', methods=['GET'])
def get_character_stats(character_id):
    """
    Get character combat and attribute stats
    
    URL Parameters:
    character_id - UUID of character
    
    Response:
    {
        "success": bool,
        "data": {
            "health": int,
            "max_health": int,
            "mana": int,
            "max_mana": int,
            "strength": int,
            "agility": int,
            "intelligence": int,
            "wisdom": int,
            "constitution": int,
            "armor_class": int,
            "dodge_chance": float
        }
    }
    """
    try:
        character = Riftwalker.query.get(character_id)
        
        if not character:
            return jsonify({
                'success': False,
                'message': 'Character not found'
            }), 404
        
        # Calculate derived stats
        armor_class = 10 + (character.agility - 10) // 2
        dodge_chance = (character.agility * 0.5) + (character.level * 0.2)
        
        return jsonify({
            'success': True,
            'data': {
                'health': character.health,
                'max_health': character.max_health,
                'mana': character.mana,
                'max_mana': character.max_mana,
                'strength': character.strength,
                'agility': character.agility,
                'intelligence': character.intelligence,
                'wisdom': character.wisdom,
                'constitution': character.constitution,
                'armor_class': armor_class,
                'dodge_chance': min(95.0, dodge_chance)
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve stats: {str(e)}'
        }), 500


@riftwalker_bp.route('/<character_id>/abilities', methods=['GET'])
def get_abilities(character_id):
    """
    Get character abilities based on class
    
    URL Parameters:
    character_id - UUID of character
    
    Response:
    {
        "success": bool,
        "data": [
            {
                "id": "uuid",
                "name": "string",
                "description": "string",
                "cooldown": int,
                "cost": int
            }
        ]
    }
    """
    try:
        character = Riftwalker.query.get(character_id)
        
        if not character:
            return jsonify({
                'success': False,
                'message': 'Character not found'
            }), 404
        
        # TODO: Fetch abilities based on character class and level
        # abilities = Ability.query.filter_by(class_type=character.class_type).filter(
        #     Ability.required_level <= character.level
        # ).all()
        
        return jsonify({
            'success': True,
            'data': []
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve abilities: {str(e)}'
        }), 500


# ============================================================================
# FACTION MANAGEMENT
# ============================================================================

@riftwalker_bp.route('/<character_id>/faction/join', methods=['POST'])
@jwt_required()
@validate_json
def join_faction(character_id):
    """
    Join a faction
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "faction_id": "uuid"
    }
    
    Response:
    {
        "success": bool,
        "message": "string",
        "data": {
            "faction_id": "uuid",
            "faction_name": "string",
            "rank": "string"
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        character = Riftwalker.query.get(character_id)
        
        if not character:
            return jsonify({
                'success': False,
                'message': 'Character not found'
            }), 404
        
        if str(character.user_id) != player_id:
            return jsonify({
                'success': False,
                'message': 'Unauthorized'
            }), 403
        
        data = request.get_json()
        faction_id = data.get('faction_id')
        
        faction = Faction.query.get(faction_id)
        if not faction:
            return jsonify({
                'success': False,
                'message': 'Faction not found'
            }), 404
        
        if character.faction_id:
            return jsonify({
                'success': False,
                'message': 'Character already in a faction'
            }), 409
        
        # Add character to faction
        faction.add_member(character)
        character.faction_id = faction.id
        character.guild_role = 'member'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Joined {faction.name}',
            'data': {
                'faction_id': str(faction.id),
                'faction_name': faction.name,
                'rank': 'Initiate'
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to join faction: {str(e)}'
        }), 500


@riftwalker_bp.route('/<character_id>/faction/leave', methods=['POST'])
@jwt_required()
def leave_faction(character_id):
    """
    Leave current faction
    
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
        character = Riftwalker.query.get(character_id)
        
        if not character:
            return jsonify({
                'success': False,
                'message': 'Character not found'
            }), 404
        
        if str(character.user_id) != player_id:
            return jsonify({
                'success': False,
                'message': 'Unauthorized'
            }), 403
        
        if not character.faction_id:
            return jsonify({
                'success': False,
                'message': 'Character not in a faction'
            }), 400
        
        faction = Faction.query.get(character.faction_id)
        if faction:
            faction.remove_member(character)
        
        character.faction_id = None
        character.guild_role = None
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Left faction'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to leave faction: {str(e)}'
        }), 500


# ============================================================================
# INVENTORY & EQUIPMENT
# ============================================================================

@riftwalker_bp.route('/<character_id>/inventory', methods=['GET'])
@jwt_required()
def get_inventory(character_id):
    """
    Get character inventory
    
    Headers:
    Authorization: Bearer {access_token}
    
    URL Parameters:
    character_id - UUID of character
    
    Response:
    {
        "success": bool,
        "data": {
            "slots_used": int,
            "slots_total": int,
            "items": [
                {
                    "id": "uuid",
                    "name": "string",
                    "quantity": int,
                    "rarity": "string"
                }
            ]
        }
    }
    """
    try:
        character = Riftwalker.query.get(character_id)
        
        if not character:
            return jsonify({
                'success': False,
                'message': 'Character not found'
            }), 404
        
        # TODO: Fetch inventory items
        # inventory = Inventory.query.filter_by(character_id=character_id).all()
        
        return jsonify({
            'success': True,
            'data': {
                'slots_used': 0,
                'slots_total': 20,
                'items': []
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve inventory: {str(e)}'
        }), 500


@riftwalker_bp.route('/<character_id>/equipment', methods=['GET'])
def get_equipment(character_id):
    """
    Get character equipped items
    
    URL Parameters:
    character_id - UUID of character
    
    Response:
    {
        "success": bool,
        "data": {
            "head": {...},
            "chest": {...},
            "hands": {...},
            "legs": {...},
            "feet": {...},
            "main_hand": {...},
            "off_hand": {...}
        }
    }
    """
    try:
        character = Riftwalker.query.get(character_id)
        
        if not character:
            return jsonify({
                'success': False,
                'message': 'Character not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'head': character.equipment_head,
                'chest': character.equipment_chest,
                'hands': character.equipment_hands,
                'legs': character.equipment_legs,
                'feet': character.equipment_feet,
                'main_hand': character.equipment_main_hand,
                'off_hand': character.equipment_off_hand
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve equipment: {str(e)}'
        }), 500


# ============================================================================
# CHARACTER LISTING & DISCOVERY
# ============================================================================

@riftwalker_bp.route('', methods=['GET'])
def list_characters():
    """
    List all active characters with optional filtering
    
    Query Parameters:
    level_min - int (minimum level)
    level_max - int (maximum level)
    class - string (filter by class)
    faction_id - uuid (filter by faction)
    limit - int (default 50, max 100)
    offset - int (default 0)
    
    Response:
    {
        "success": bool,
        "data": [
            {
                "id": "uuid",
                "character_name": "string",
                "class": "string",
                "level": int,
                "faction_id": "uuid or null"
            }
        ],
        "pagination": {
            "total": int,
            "limit": int,
            "offset": int
        }
    }
    """
    try:
        query = Riftwalker.query.filter_by(is_active=True)
        
        # Apply filters
        level_min = request.args.get('level_min', type=int)
        if level_min:
            query = query.filter(Riftwalker.level >= level_min)
        
        level_max = request.args.get('level_max', type=int)
        if level_max:
            query = query.filter(Riftwalker.level <= level_max)
        
        class_filter = request.args.get('class', type=str)
        if class_filter:
            query = query.filter_by(class_type=class_filter)
        
        faction_filter = request.args.get('faction_id', type=str)
        if faction_filter:
            query = query.filter_by(faction_id=faction_filter)
        
        # Pagination
        limit = min(request.args.get('limit', 50, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        
        total = query.count()
        characters = query.limit(limit).offset(offset).all()
        
        return jsonify({
            'success': True,
            'data': riftwalkers_schema.dump(characters),
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to list characters: {str(e)}'
        }), 500


@riftwalker_bp.route('/search', methods=['GET'])
def search_characters():
    """
    Search for characters by name
    
    Query Parameters:
    q - string (search query)
    limit - int (default 20, max 50)
    
    Response:
    {
        "success": bool,
        "data": [...]
    }
    """
    try:
        query_str = request.args.get('q', '', type=str)
        
        if len(query_str) < 2:
            return jsonify({
                'success': False,
                'message': 'Search query must be at least 2 characters'
            }), 400
        
        limit = min(request.args.get('limit', 20, type=int), 50)
        
        results = Riftwalker.query.filter(
            Riftwalker.character_name.ilike(f'%{query_str}%'),
            Riftwalker.is_active == True
        ).limit(limit).all()
        
        return jsonify({
            'success': True,
            'data': riftwalkers_schema.dump(results)
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Search failed: {str(e)}'
        }), 500


# ============================================================================
# LEADERBOARDS
# ============================================================================

@riftwalker_bp.route('/leaderboards/level', methods=['GET'])
def get_level_leaderboard():
    """
    Get character level leaderboard
    
    Query Parameters:
    limit - int (default 50, max 100)
    
    Response:
    {
        "success": bool,
        "data": [
            {
                "rank": int,
                "character_name": "string",
                "level": int,
                "experience": int
            }
        ]
    }
    """
    try:
        limit = min(request.args.get('limit', 50, type=int), 100)
        
        characters = Riftwalker.query.filter_by(is_active=True).order_by(
            Riftwalker.level.desc(),
            Riftwalker.experience.desc()
        ).limit(limit).all()
        
        leaderboard = [
            {
                'rank': i + 1,
                'character_name': char.character_name,
                'level': char.level,
                'experience': char.experience,
                'faction_id': str(char.faction_id) if char.faction_id else None
            }
            for i, char in enumerate(characters)
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


@riftwalker_bp.route('/leaderboards/faction', methods=['GET'])
def get_faction_leaderboard():
    """
    Get leaderboard by faction membership
    
    Response:
    {
        "success": bool,
        "data": [
            {
                "faction_id": "uuid",
                "faction_name": "string",
                "member_count": int,
                "average_level": float
            }
        ]
    }
    """
    try:
        factions = Faction.query.filter_by(is_active=True).order_by(
            Faction.member_count.desc()
        ).all()
        
        leaderboard = [
            {
                'faction_id': str(faction.id),
                'faction_name': faction.name,
                'member_count': faction.member_count,
                'average_level': faction.total_influence // max(faction.member_count, 1),
                'total_influence': faction.total_influence
            }
            for faction in factions
        ]
        
        return jsonify({
            'success': True,
            'data': leaderboard
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve faction leaderboard: {str(e)}'
        }), 500
