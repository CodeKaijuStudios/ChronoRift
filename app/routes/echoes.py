"""
ChronoRift Echo Routes
Handles Echo collection, bonding, combat abilities, and echo management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import uuid

from app.models import db, Echo, EchoBond, Riftwalker, EchoAbility
from app.schemas import echo_schema, echoes_schema, echo_bond_schema
from app.utils.decorators import validate_json, rate_limit


echoes_bp = Blueprint('echoes', __name__, url_prefix='/api/echoes')


# ============================================================================
# ECHO COLLECTION & CAPTURE
# ============================================================================

@echoes_bp.route('/capture', methods=['POST'])
@jwt_required()
@validate_json
def capture_echo():
    """
    Capture/collect an Echo after battle encounter
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "echo_type_id": "uuid",
        "rarity": "string (common, uncommon, rare, legendary)",
        "health_percentage": float (0-100),
        "location": "string",
        "capture_method": "string (battle, trap, ritual, etc)"
    }
    
    Response:
    {
        "success": bool,
        "message": "string",
        "data": {
            "id": "uuid",
            "echo_type_name": "string",
            "rarity": "string",
            "level": 1,
            "experience": 0,
            "bond_level": 1,
            "captured_at": "ISO timestamp"
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        character = Riftwalker.query.get(player_id)
        
        if not character:
            return jsonify({
                'success': False,
                'message': 'Character not found'
            }), 404
        
        data = request.get_json()
        echo_type_id = data.get('echo_type_id')
        rarity = data.get('rarity', 'common')
        
        # Validate rarity
        valid_rarities = ['common', 'uncommon', 'rare', 'legendary', 'mythic']
        if rarity not in valid_rarities:
            return jsonify({
                'success': False,
                'message': f'Invalid rarity. Must be one of: {", ".join(valid_rarities)}'
            }), 400
        
        # Rarity-based stat modifiers
        rarity_modifiers = {
            'common': {'health': 1.0, 'attack': 1.0, 'defense': 1.0},
            'uncommon': {'health': 1.1, 'attack': 1.1, 'defense': 1.1},
            'rare': {'health': 1.25, 'attack': 1.25, 'defense': 1.25},
            'legendary': {'health': 1.5, 'attack': 1.5, 'defense': 1.5},
            'mythic': {'health': 1.75, 'attack': 1.75, 'defense': 1.75}
        }
        
        modifiers = rarity_modifiers.get(rarity, rarity_modifiers['common'])
        
        # Create new Echo instance
        new_echo = Echo(
            id=uuid.uuid4(),
            character_id=player_id,
            echo_type_id=echo_type_id,
            rarity=rarity,
            level=1,
            experience=0,
            health=int(50 * modifiers['health']),
            max_health=int(50 * modifiers['health']),
            attack=int(15 * modifiers['attack']),
            defense=int(10 * modifiers['defense']),
            speed=12,
            special_attack=int(15 * modifiers['attack']),
            special_defense=int(10 * modifiers['defense']),
            location_captured=data.get('location', 'Unknown'),
            capture_method=data.get('capture_method', 'battle'),
            current_health=int(50 * modifiers['health']) if data.get('health_percentage', 100) == 100 else int(50 * modifiers['health'] * (data.get('health_percentage', 100) / 100)),
            is_active=True
        )
        
        db.session.add(new_echo)
        db.session.flush()
        
        # Create initial bond record
        bond = EchoBond(
            id=uuid.uuid4(),
            echo_id=new_echo.id,
            character_id=player_id,
            bond_level=1,
            bond_experience=0,
            happiness=50,
            affection=0,
            trust=50
        )
        
        db.session.add(bond)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully captured {new_echo.echo_type_id}!',
            'data': echo_schema.dump(new_echo)
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Capture failed: {str(e)}'
        }), 500


@echoes_bp.route('/<character_id>/collection', methods=['GET'])
@jwt_required()
def get_collection(character_id):
    """
    Get all Echoes in character's collection
    
    Headers:
    Authorization: Bearer {access_token}
    
    URL Parameters:
    character_id - UUID of character
    
    Query Parameters:
    rarity - string (filter by rarity)
    element - string (filter by element)
    level_min - int
    level_max - int
    limit - int (default 50, max 100)
    offset - int (default 0)
    
    Response:
    {
        "success": bool,
        "data": [
            {
                "id": "uuid",
                "echo_type_id": "uuid",
                "rarity": "string",
                "level": int,
                "experience": int,
                "bond_level": int,
                "current_health": int,
                "max_health": int
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
        player_id = get_jwt_identity()
        
        query = Echo.query.filter_by(character_id=player_id, is_active=True)
        
        # Apply filters
        rarity = request.args.get('rarity', type=str)
        if rarity:
            query = query.filter_by(rarity=rarity)
        
        level_min = request.args.get('level_min', type=int)
        if level_min:
            query = query.filter(Echo.level >= level_min)
        
        level_max = request.args.get('level_max', type=int)
        if level_max:
            query = query.filter(Echo.level <= level_max)
        
        # Pagination
        limit = min(request.args.get('limit', 50, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        
        total = query.count()
        echoes = query.order_by(Echo.level.desc()).limit(limit).offset(offset).all()
        
        return jsonify({
            'success': True,
            'data': echoes_schema.dump(echoes),
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve collection: {str(e)}'
        }), 500


@echoes_bp.route('/<echo_id>', methods=['GET'])
def get_echo_details(echo_id):
    """
    Get detailed information about a specific Echo
    
    URL Parameters:
    echo_id - UUID of Echo
    
    Response:
    {
        "success": bool,
        "data": {
            "id": "uuid",
            "echo_type_id": "uuid",
            "echo_type_name": "string",
            "rarity": "string",
            "level": int,
            "experience": int,
            "stats": {
                "health": int,
                "attack": int,
                "defense": int,
                "speed": int,
                "special_attack": int,
                "special_defense": int
            },
            "bond_level": int,
            "happiness": int,
            "affection": int,
            "trust": int,
            "abilities": [...],
            "captured_at": "ISO timestamp"
        }
    }
    """
    try:
        echo = Echo.query.get(echo_id)
        
        if not echo:
            return jsonify({
                'success': False,
                'message': 'Echo not found'
            }), 404
        
        bond = EchoBond.query.filter_by(echo_id=echo_id).first()
        
        return jsonify({
            'success': True,
            'data': {
                **echo_schema.dump(echo),
                'bond_info': {
                    'bond_level': bond.bond_level if bond else 1,
                    'happiness': bond.happiness if bond else 50,
                    'affection': bond.affection if bond else 0,
                    'trust': bond.trust if bond else 50
                } if bond else None
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve Echo details: {str(e)}'
        }), 500


# ============================================================================
# ECHO BONDING & HAPPINESS
# ============================================================================

@echoes_bp.route('/<echo_id>/bond', methods=['GET'])
def get_bond_info(echo_id):
    """
    Get Echo bonding and happiness information
    
    URL Parameters:
    echo_id - UUID of Echo
    
    Response:
    {
        "success": bool,
        "data": {
            "echo_id": "uuid",
            "bond_level": int (1-10),
            "bond_experience": int,
            "experience_for_next_level": int,
            "happiness": int (0-100),
            "affection": int (0-100),
            "trust": int (0-100),
            "bond_milestones_unlocked": [...]
        }
    }
    """
    try:
        bond = EchoBond.query.filter_by(echo_id=echo_id).first()
        
        if not bond:
            return jsonify({
                'success': False,
                'message': 'Bond information not found'
            }), 404
        
        # Bond level progression (1000 exp per level)
        exp_for_next = (bond.bond_level + 1) * 1000
        
        # Determine bond milestones
        milestones = []
        if bond.bond_level >= 2:
            milestones.append('Echo learns new ability')
        if bond.bond_level >= 5:
            milestones.append('Echo color form unlocked')
        if bond.bond_level >= 8:
            milestones.append('Mega evolution available')
        if bond.bond_level >= 10:
            milestones.append('Perfect bond achieved')
        
        return jsonify({
            'success': True,
            'data': {
                'echo_id': str(echo_id),
                'bond_level': bond.bond_level,
                'bond_experience': bond.bond_experience,
                'experience_for_next_level': exp_for_next,
                'happiness': bond.happiness,
                'affection': bond.affection,
                'trust': bond.trust,
                'bond_milestones_unlocked': milestones
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve bond info: {str(e)}'
        }), 500


@echoes_bp.route('/<echo_id>/interact', methods=['POST'])
@jwt_required()
@validate_json
def interact_with_echo(echo_id):
    """
    Interact with Echo to increase happiness and bond
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "interaction_type": "string (pet, play, feed, battle, rest, etc)"
    }
    
    Response:
    {
        "success": bool,
        "data": {
            "happiness_change": int,
            "affection_change": int,
            "bond_experience_gained": int,
            "new_happiness": int,
            "new_affection": int
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        echo = Echo.query.get(echo_id)
        
        if not echo:
            return jsonify({
                'success': False,
                'message': 'Echo not found'
            }), 404
        
        if str(echo.character_id) != player_id:
            return jsonify({
                'success': False,
                'message': 'Unauthorized'
            }), 403
        
        data = request.get_json()
        interaction_type = data.get('interaction_type', 'pet')
        
        # Interaction effects
        interaction_effects = {
            'pet': {'happiness': 10, 'affection': 5, 'exp': 25},
            'play': {'happiness': 20, 'affection': 15, 'exp': 50},
            'feed': {'happiness': 15, 'affection': 5, 'exp': 30},
            'battle': {'happiness': 5, 'affection': 10, 'exp': 100},
            'rest': {'happiness': -5, 'affection': 0, 'exp': 0},
            'train': {'happiness': 10, 'affection': 15, 'exp': 75}
        }
        
        effects = interaction_effects.get(interaction_type, interaction_effects['pet'])
        
        bond = EchoBond.query.filter_by(echo_id=echo_id).first()
        if not bond:
            return jsonify({
                'success': False,
                'message': 'Bond record not found'
            }), 404
        
        # Apply changes
        happiness_change = effects['happiness']
        affection_change = effects['affection']
        exp_gained = effects['exp']
        
        bond.happiness = max(0, min(100, bond.happiness + happiness_change))
        bond.affection = max(0, min(100, bond.affection + affection_change))
        bond.bond_experience += exp_gained
        bond.last_interacted = datetime.utcnow()
        
        # Check for level up
        level_up = False
        if bond.bond_experience >= (bond.bond_level + 1) * 1000:
            bond.bond_level += 1
            bond.bond_experience = 0
            level_up = True
            happiness_change += 20  # Bonus happiness on level up
            bond.happiness = min(100, bond.happiness + 20)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Interacted with Echo ({interaction_type})',
            'data': {
                'interaction_type': interaction_type,
                'happiness_change': happiness_change,
                'affection_change': affection_change,
                'bond_experience_gained': exp_gained,
                'new_happiness': bond.happiness,
                'new_affection': bond.affection,
                'level_up': level_up,
                'new_bond_level': bond.bond_level if level_up else None
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Interaction failed: {str(e)}'
        }), 500


@echoes_bp.route('/<echo_id>/gift', methods=['POST'])
@jwt_required()
@validate_json
def give_gift_to_echo(echo_id):
    """
    Give a gift item to Echo to increase affection
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "item_id": "uuid",
        "item_type": "string (berry, treat, toy, etc)"
    }
    
    Response:
    {
        "success": bool,
        "data": {
            "affection_gained": int,
            "new_affection": int,
            "echo_reaction": "string"
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        echo = Echo.query.get(echo_id)
        
        if not echo:
            return jsonify({
                'success': False,
                'message': 'Echo not found'
            }), 404
        
        if str(echo.character_id) != player_id:
            return jsonify({
                'success': False,
                'message': 'Unauthorized'
            }), 403
        
        data = request.get_json()
        item_type = data.get('item_type', 'treat')
        
        # Item affection bonuses
        item_bonuses = {
            'berry': 10,
            'treat': 15,
            'toy': 20,
            'rare_item': 30,
            'legend_item': 50
        }
        
        affection_gained = item_bonuses.get(item_type, 10)
        
        bond = EchoBond.query.filter_by(echo_id=echo_id).first()
        if not bond:
            return jsonify({
                'success': False,
                'message': 'Bond record not found'
            }), 404
        
        bond.affection = min(100, bond.affection + affection_gained)
        bond.happiness = min(100, bond.happiness + 5)
        db.session.commit()
        
        # Echo reaction based on affection
        reactions = ['indifferent', 'curious', 'pleased', 'delighted', 'overjoyed']
        reaction_index = min(4, bond.affection // 25)
        reaction = reactions[reaction_index]
        
        return jsonify({
            'success': True,
            'data': {
                'affection_gained': affection_gained,
                'new_affection': bond.affection,
                'echo_reaction': reaction,
                'happiness_bonus': 5
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Gift giving failed: {str(e)}'
        }), 500


# ============================================================================
# ECHO LEVELING & PROGRESSION
# ============================================================================

@echoes_bp.route('/<echo_id>/experience', methods=['POST'])
@jwt_required()
@validate_json
def add_echo_experience(echo_id):
    """
    Add experience to Echo (from battles, etc)
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "amount": int,
        "source": "string (battle, training, etc)"
    }
    
    Response:
    {
        "success": bool,
        "data": {
            "experience_gained": int,
            "new_experience": int,
            "new_level": int,
            "level_up": bool
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        echo = Echo.query.get(echo_id)
        
        if not echo:
            return jsonify({
                'success': False,
                'message': 'Echo not found'
            }), 404
        
        if str(echo.character_id) != player_id:
            return jsonify({
                'success': False,
                'message': 'Unauthorized'
            }), 403
        
        data = request.get_json()
        amount = data.get('amount', 0)
        
        if amount <= 0:
            return jsonify({
                'success': False,
                'message': 'Experience amount must be positive'
            }), 400
        
        old_level = echo.level
        echo.experience += amount
        
        # Level up calculation (1000 exp per level)
        experience_for_next_level = (echo.level + 1) * 1000
        level_up = False
        
        while echo.experience >= experience_for_next_level:
            echo.level += 1
            echo.experience -= experience_for_next_level
            experience_for_next_level = (echo.level + 1) * 1000
            level_up = True
            
            # Stat growth on level up
            echo.max_health += int(5 * (1 + echo.level * 0.05))
            echo.current_health = echo.max_health
            echo.attack += int(2 * (1 + echo.level * 0.03))
            echo.defense += int(1 * (1 + echo.level * 0.02))
            echo.special_attack += int(2 * (1 + echo.level * 0.03))
            echo.special_defense += int(1 * (1 + echo.level * 0.02))
            echo.speed += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'experience_gained': amount,
                'new_experience': echo.experience,
                'old_level': old_level,
                'new_level': echo.level,
                'level_up': level_up,
                'stats_increased': level_up
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Experience update failed: {str(e)}'
        }), 500


# ============================================================================
# ECHO ABILITIES & MOVES
# ============================================================================

@echoes_bp.route('/<echo_id>/abilities', methods=['GET'])
def get_echo_abilities(echo_id):
    """
    Get abilities/moves available to Echo
    
    URL Parameters:
    echo_id - UUID of Echo
    
    Response:
    {
        "success": bool,
        "data": [
            {
                "id": "uuid",
                "name": "string",
                "type": "string",
                "power": int,
                "accuracy": float,
                "pp": int,
                "category": "string (physical, special, status)",
                "description": "string"
            }
        ]
    }
    """
    try:
        echo = Echo.query.get(echo_id)
        
        if not echo:
            return jsonify({
                'success': False,
                'message': 'Echo not found'
            }), 404
        
        # TODO: Fetch abilities based on Echo type and level
        # abilities = EchoAbility.query.filter_by(echo_type_id=echo.echo_type_id).filter(
        #     EchoAbility.required_level <= echo.level
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


@echoes_bp.route('/<echo_id>/learn-move', methods=['POST'])
@jwt_required()
@validate_json
def learn_move(echo_id):
    """
    Teach Echo a new move
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "move_id": "uuid"
    }
    
    Response:
    {
        "success": bool,
        "message": "string",
        "data": {
            "move_name": "string",
            "learned": bool
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        echo = Echo.query.get(echo_id)
        
        if not echo:
            return jsonify({
                'success': False,
                'message': 'Echo not found'
            }), 404
        
        if str(echo.character_id) != player_id:
            return jsonify({
                'success': False,
                'message': 'Unauthorized'
            }), 403
        
        # TODO: Implement move learning logic
        
        return jsonify({
            'success': True,
            'message': 'Move learned successfully',
            'data': {
                'move_name': 'New Move',
                'learned': True
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Move learning failed: {str(e)}'
        }), 500


# ============================================================================
# ECHO RELEASE & MANAGEMENT
# ============================================================================

@echoes_bp.route('/<echo_id>/release', methods=['POST'])
@jwt_required()
@validate_json
def release_echo(echo_id):
    """
    Release an Echo back to the wild
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "confirmation": "RELEASE" (required for safety)
    }
    
    Response:
    {
        "success": bool,
        "message": "string"
    }
    """
    try:
        player_id = get_jwt_identity()
        echo = Echo.query.get(echo_id)
        
        if not echo:
            return jsonify({
                'success': False,
                'message': 'Echo not found'
            }), 404
        
        if str(echo.character_id) != player_id:
            return jsonify({
                'success': False,
                'message': 'Unauthorized'
            }), 403
        
        data = request.get_json()
        if data.get('confirmation') != 'RELEASE':
            return jsonify({
                'success': False,
                'message': 'Release confirmation required'
            }), 400
        
        # Soft delete
        echo.is_active = False
        echo.released_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Echo released'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Echo release failed: {str(e)}'
        }), 500


@echoes_bp.route('/<echo_id>/rename', methods=['PUT'])
@jwt_required()
@validate_json
def rename_echo(echo_id):
    """
    Give Echo a custom nickname
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "nickname": "string (max 50 chars)"
    }
    
    Response:
    {
        "success": bool,
        "data": {
            "nickname": "string",
            "message": "string"
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        echo = Echo.query.get(echo_id)
        
        if not echo:
            return jsonify({
                'success': False,
                'message': 'Echo not found'
            }), 404
        
        if str(echo.character_id) != player_id:
            return jsonify({
                'success': False,
                'message': 'Unauthorized'
            }), 403
        
        data = request.get_json()
        nickname = data.get('nickname', '').strip()
        
        if not nickname or len(nickname) > 50:
            return jsonify({
                'success': False,
                'message': 'Nickname must be 1-50 characters'
            }), 400
        
        echo.nickname = nickname
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'nickname': echo.nickname,
                'message': f'Echo renamed to {nickname}'
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Rename failed: {str(e)}'
        }), 500


# ============================================================================
# ECHO STATISTICS & ANALYTICS
# ============================================================================

@echoes_bp.route('/<character_id>/statistics', methods=['GET'])
@jwt_required()
def get_collection_statistics(character_id):
    """
    Get statistics about character's Echo collection
    
    Headers:
    Authorization: Bearer {access_token}
    
    Response:
    {
        "success": bool,
        "data": {
            "total_echoes": int,
            "echoes_by_rarity": {...},
            "average_level": float,
            "average_happiness": float,
            "total_bond_points": int,
            "average_bond_level": float,
            "rarest_echo": {...}
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        
        echoes = Echo.query.filter_by(character_id=player_id, is_active=True).all()
        
        if not echoes:
            return jsonify({
                'success': True,
                'data': {
                    'total_echoes': 0,
                    'echoes_by_rarity': {},
                    'average_level': 0,
                    'average_happiness': 0,
                    'total_bond_points': 0,
                    'average_bond_level': 0
                }
            }), 200
        
        # Calculate statistics
        rarity_count = {}
        total_level = 0
        total_happiness = 0
        total_bond_level = 0
        total_bond_exp = 0
        rarest_echo = None
        rarity_rank = {'common': 1, 'uncommon': 2, 'rare': 3, 'legendary': 4, 'mythic': 5}
        max_rarity_rank = 0
        
        for echo in echoes:
            rarity_count[echo.rarity] = rarity_count.get(echo.rarity, 0) + 1
            total_level += echo.level
            
            bond = EchoBond.query.filter_by(echo_id=echo.id).first()
            if bond:
                total_happiness += bond.happiness
                total_bond_level += bond.bond_level
                total_bond_exp += bond.bond_experience
            
            # Find rarest echo
            if rarity_rank.get(echo.rarity, 0) > max_rarity_rank:
                max_rarity_rank = rarity_rank.get(echo.rarity, 0)
                rarest_echo = echo
        
        return jsonify({
            'success': True,
            'data': {
                'total_echoes': len(echoes),
                'echoes_by_rarity': rarity_count,
                'average_level': round(total_level / len(echoes), 2),
                'average_happiness': round(total_happiness / len(echoes), 2),
                'total_bond_points': total_bond_exp,
                'average_bond_level': round(total_bond_level / len(echoes), 2),
                'rarest_echo': echo_schema.dump(rarest_echo) if rarest_echo else None
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve statistics: {str(e)}'
        }), 500
