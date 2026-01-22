"""
ChronoRift Combat Routes
Handles turn-based combat system, battles, moves, and encounter mechanics
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import uuid
import random
import math

from app.models import db, Battle, BattleRound, Echo, Riftwalker, EchoAbility
from app.schemas import battle_schema, battles_schema
from app.utils.decorators import validate_json, rate_limit


combat_bp = Blueprint('combat', __name__, url_prefix='/api/combat')


# ============================================================================
# BATTLE INITIATION & MANAGEMENT
# ============================================================================

@combat_bp.route('/battles', methods=['POST'])
@jwt_required()
@validate_json
def start_battle():
    """
    Initiate a new battle encounter
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "battle_type": "string (pve, pvp, arena, rift)",
        "player_echo_ids": ["uuid", ...],
        "opponent_id": "uuid (optional, for PvP)",
        "encounter_id": "uuid (optional, for rift events)"
    }
    
    Response:
    {
        "success": bool,
        "message": "string",
        "data": {
            "battle_id": "uuid",
            "battle_type": "string",
            "turn_order": [
                {
                    "participant_id": "uuid",
                    "participant_name": "string",
                    "speed": int,
                    "is_player": bool
                }
            ],
            "current_turn_index": 0,
            "round": 1,
            "participants": [...]
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        data = request.get_json()
        
        battle_type = data.get('battle_type', 'pve')
        player_echo_ids = data.get('player_echo_ids', [])
        
        if not player_echo_ids:
            return jsonify({
                'success': False,
                'message': 'At least one Echo required for battle'
            }), 400
        
        # Validate player Echoes
        player_echoes = Echo.query.filter(
            Echo.id.in_(player_echo_ids),
            Echo.character_id == player_id,
            Echo.is_active == True
        ).all()
        
        if len(player_echoes) != len(player_echo_ids):
            return jsonify({
                'success': False,
                'message': 'Invalid Echo IDs or unauthorized access'
            }), 403
        
        # Create battle record
        battle = Battle(
            id=uuid.uuid4(),
            initiator_id=player_id,
            battle_type=battle_type,
            status='active',
            current_round=1,
            is_finished=False
        )
        
        # Handle opponent Echoes based on battle type
        if battle_type == 'pvp':
            opponent_id = data.get('opponent_id')
            opponent_echo_ids = data.get('opponent_echo_ids', [])
            
            if not opponent_id or not opponent_echo_ids:
                return jsonify({
                    'success': False,
                    'message': 'Opponent ID and Echoes required for PvP'
                }), 400
            
            opponent_echoes = Echo.query.filter(
                Echo.id.in_(opponent_echo_ids),
                Echo.character_id == opponent_id,
                Echo.is_active == True
            ).all()
            
            if len(opponent_echoes) != len(opponent_echo_ids):
                return jsonify({
                    'success': False,
                    'message': 'Invalid opponent Echo IDs'
                }), 403
            
            battle.opponent_id = opponent_id
            battle_echoes = player_echoes + opponent_echoes
        else:
            # PvE - opponent Echoes generated/provided by system
            battle_echoes = player_echoes
        
        # Calculate turn order based on speed
        turn_order_list = []
        for echo in battle_echoes:
            turn_order_list.append({
                'echo_id': echo.id,
                'echo_name': echo.echo_type_id,
                'speed': echo.speed,
                'owner_id': echo.character_id,
                'current_health': echo.current_health,
                'max_health': echo.max_health
            })
        
        # Sort by speed (highest first)
        turn_order_list.sort(key=lambda x: x['speed'], reverse=True)
        
        db.session.add(battle)
        db.session.flush()
        
        return jsonify({
            'success': True,
            'message': f'{battle_type.upper()} battle started!',
            'data': {
                'battle_id': str(battle.id),
                'battle_type': battle_type,
                'turn_order': turn_order_list,
                'current_turn_index': 0,
                'round': battle.current_round,
                'status': battle.status
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Battle initiation failed: {str(e)}'
        }), 500


@combat_bp.route('/battles/<battle_id>', methods=['GET'])
@jwt_required()
def get_battle_state(battle_id):
    """
    Get current battle state
    
    Headers:
    Authorization: Bearer {access_token}
    
    URL Parameters:
    battle_id - UUID of battle
    
    Response:
    {
        "success": bool,
        "data": {
            "battle_id": "uuid",
            "battle_type": "string",
            "status": "string",
            "round": int,
            "turn_order": [...],
            "current_turn_index": int,
            "participants": [
                {
                    "echo_id": "uuid",
                    "owner_id": "uuid",
                    "current_health": int,
                    "max_health": int,
                    "status_effects": [...]
                }
            ]
        }
    }
    """
    try:
        battle = Battle.query.get(battle_id)
        
        if not battle:
            return jsonify({
                'success': False,
                'message': 'Battle not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': battle_schema.dump(battle)
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve battle state: {str(e)}'
        }), 500


# ============================================================================
# TURN-BASED COMBAT ACTIONS
# ============================================================================

@combat_bp.route('/battles/<battle_id>/action', methods=['POST'])
@jwt_required()
@validate_json
@rate_limit(limit=30, window=60)
def execute_action(battle_id):
    """
    Execute a combat action (attack, move, defend, item use)
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "action_type": "string (attack, move, defend, item, switch, escape)",
        "actor_echo_id": "uuid",
        "target_echo_id": "uuid (optional)",
        "move_id": "uuid (for move action)",
        "item_id": "uuid (for item action)"
    }
    
    Response:
    {
        "success": bool,
        "message": "string",
        "data": {
            "action_executed": bool,
            "action_type": "string",
            "damage_dealt": int,
            "target_health": int,
            "effects_applied": [...],
            "next_turn_index": int,
            "battle_status": "string (ongoing, won, lost, draw)"
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        battle = Battle.query.get(battle_id)
        
        if not battle:
            return jsonify({
                'success': False,
                'message': 'Battle not found'
            }), 404
        
        if battle.status != 'active':
            return jsonify({
                'success': False,
                'message': 'Battle is not active'
            }), 400
        
        data = request.get_json()
        action_type = data.get('action_type', 'attack')
        actor_echo_id = data.get('actor_echo_id')
        target_echo_id = data.get('target_echo_id')
        
        # Get actor and target echoes
        actor = Echo.query.get(actor_echo_id)
        target = Echo.query.get(target_echo_id) if target_echo_id else None
        
        if not actor:
            return jsonify({
                'success': False,
                'message': 'Actor Echo not found'
            }), 404
        
        if action_type != 'escape' and not target:
            return jsonify({
                'success': False,
                'message': 'Target Echo required for this action'
            }), 400
        
        # Execute action based on type
        if action_type == 'attack':
            damage = calculate_damage(actor, target)
            effects = apply_damage(target, damage)
            
            result_data = {
                'action_executed': True,
                'action_type': action_type,
                'damage_dealt': damage,
                'target_health': target.current_health,
                'target_max_health': target.max_health,
                'effects_applied': effects
            }
        
        elif action_type == 'move':
            move_id = data.get('move_id')
            move = EchoAbility.query.get(move_id)
            
            if not move:
                return jsonify({
                    'success': False,
                    'message': 'Move not found'
                }), 404
            
            damage = calculate_move_damage(actor, target, move)
            effects = apply_damage(target, damage)
            
            # Apply move effects
            if move.effect_type:
                effects.extend(apply_status_effect(target, move.effect_type, move.effect_chance))
            
            result_data = {
                'action_executed': True,
                'action_type': action_type,
                'move_name': move.name,
                'damage_dealt': damage,
                'target_health': target.current_health,
                'effects_applied': effects
            }
        
        elif action_type == 'defend':
            # Implement defense mechanics
            actor.is_defending = True
            result_data = {
                'action_executed': True,
                'action_type': action_type,
                'message': f'{actor.echo_type_id} takes a defensive stance'
            }
        
        elif action_type == 'item':
            item_id = data.get('item_id')
            item_effect = use_item(actor, item_id)
            
            result_data = {
                'action_executed': True,
                'action_type': action_type,
                'item_effect': item_effect
            }
        
        elif action_type == 'switch':
            # Switch to different Echo
            new_echo_id = data.get('new_echo_id')
            result_data = {
                'action_executed': True,
                'action_type': action_type,
                'switched_to': str(new_echo_id)
            }
        
        elif action_type == 'escape':
            # Attempt escape from battle
            escape_chance = calculate_escape_chance(actor)
            escaped = random.random() < escape_chance
            
            if escaped:
                battle.status = 'escaped'
                battle.is_finished = True
            
            result_data = {
                'action_executed': escaped,
                'action_type': action_type,
                'escape_chance': escape_chance,
                'escaped': escaped
            }
        
        # Determine battle status
        battle_status = check_battle_status(battle)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Action executed',
            'data': {
                **result_data,
                'round': battle.current_round,
                'battle_status': battle_status
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Action execution failed: {str(e)}'
        }), 500


# ============================================================================
# DAMAGE CALCULATION
# ============================================================================

def calculate_damage(attacker, defender):
    """
    Calculate damage using formula:
    Base Damage = (Attack - Defense/2) * (1 + Level/100)
    Final Damage = Base Damage * (0.85 + Random(0.15))
    """
    base_damage = max(0, (attacker.attack - defender.defense / 2))
    level_multiplier = 1 + (attacker.level / 100)
    base_damage *= level_multiplier
    
    # Apply variance (85% to 100% of base)
    variance = 0.85 + (random.random() * 0.15)
    final_damage = int(base_damage * variance)
    
    # Critical hit chance (10% base)
    if random.random() < 0.1:
        final_damage = int(final_damage * 1.5)
    
    return max(1, final_damage)


def calculate_move_damage(attacker, defender, move):
    """
    Calculate damage from special move
    """
    if move.damage_type == 'special':
        base_damage = max(0, (attacker.special_attack - defender.special_defense / 2))
    else:
        base_damage = max(0, (attacker.attack - defender.defense / 2))
    
    # Move power multiplier
    base_damage *= (move.power / 100)
    
    level_multiplier = 1 + (attacker.level / 100)
    base_damage *= level_multiplier
    
    # Apply accuracy
    if random.random() > (move.accuracy / 100):
        return 0  # Miss
    
    variance = 0.85 + (random.random() * 0.15)
    final_damage = int(base_damage * variance)
    
    return max(1, final_damage)


def apply_damage(target, damage):
    """
    Apply damage to target and return effects
    """
    target.current_health = max(0, target.current_health - damage)
    
    effects = []
    if target.current_health == 0:
        effects.append('fainted')
    elif damage > target.max_health * 0.3:
        effects.append('critical_hit')
    
    return effects


def apply_status_effect(target, effect_type, chance):
    """
    Apply status effect to target with given chance
    """
    effects = []
    
    if random.random() < chance:
        status_effects = {
            'poison': {'duration': 5, 'damage_per_turn': 1},
            'paralysis': {'speed_reduction': 0.5, 'duration': 5},
            'sleep': {'duration': 3},
            'burn': {'damage_per_turn': 2, 'attack_reduction': 0.5, 'duration': 5},
            'freeze': {'duration': 3}
        }
        
        if effect_type in status_effects:
            if not target.status_effects:
                target.status_effects = {}
            
            target.status_effects[effect_type] = status_effects[effect_type]
            effects.append(effect_type)
    
    return effects


def use_item(actor, item_id):
    """
    Use an item in battle
    """
    # TODO: Implement item system
    return {'item_used': True, 'effect': 'health_restored'}


def calculate_escape_chance(echo):
    """
    Calculate chance to escape battle
    Base: 25%, Modified by Speed
    """
    base_chance = 0.25
    speed_bonus = (echo.speed / 100) * 0.25
    return min(0.9, base_chance + speed_bonus)


def check_battle_status(battle):
    """
    Determine if battle is ongoing, won, lost, or draw
    """
    # TODO: Check if any side has all fainted Echoes
    return 'ongoing'


# ============================================================================
# BATTLE STATISTICS & HISTORY
# ============================================================================

@combat_bp.route('/battles/<battle_id>/end', methods=['POST'])
@jwt_required()
@validate_json
def end_battle(battle_id):
    """
    End an active battle and calculate rewards
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "result": "string (victory, defeat, draw, surrender)"
    }
    
    Response:
    {
        "success": bool,
        "data": {
            "battle_id": "uuid",
            "result": "string",
            "experience_gained": int,
            "currency_earned": int,
            "items_earned": [...],
            "echoes_evolved": [...]
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        battle = Battle.query.get(battle_id)
        
        if not battle:
            return jsonify({
                'success': False,
                'message': 'Battle not found'
            }), 404
        
        data = request.get_json()
        result = data.get('result', 'draw')
        
        # Calculate rewards
        exp_gained = 100 if result == 'victory' else 50
        currency_earned = 500 if result == 'victory' else 200
        
        battle.status = 'finished'
        battle.result = result
        battle.is_finished = True
        battle.finished_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Battle ended: {result}',
            'data': {
                'battle_id': str(battle.id),
                'result': result,
                'experience_gained': exp_gained,
                'currency_earned': currency_earned,
                'items_earned': [],
                'echoes_evolved': []
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Battle end failed: {str(e)}'
        }), 500


@combat_bp.route('/battles/history', methods=['GET'])
@jwt_required()
def get_battle_history():
    """
    Get player's battle history
    
    Headers:
    Authorization: Bearer {access_token}
    
    Query Parameters:
    limit - int (default 20, max 50)
    offset - int (default 0)
    
    Response:
    {
        "success": bool,
        "data": [
            {
                "battle_id": "uuid",
                "battle_type": "string",
                "result": "string",
                "opponent_id": "uuid or null",
                "experience_gained": int,
                "completed_at": "ISO timestamp"
            }
        ],
        "pagination": {...}
    }
    """
    try:
        player_id = get_jwt_identity()
        
        limit = min(request.args.get('limit', 20, type=int), 50)
        offset = request.args.get('offset', 0, type=int)
        
        query = Battle.query.filter(
            (Battle.initiator_id == player_id) | (Battle.opponent_id == player_id),
            Battle.is_finished == True
        )
        
        total = query.count()
        battles = query.order_by(Battle.finished_at.desc()).limit(limit).offset(offset).all()
        
        return jsonify({
            'success': True,
            'data': battles_schema.dump(battles),
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve battle history: {str(e)}'
        }), 500


@combat_bp.route('/battles/statistics', methods=['GET'])
@jwt_required()
def get_battle_statistics():
    """
    Get player battle statistics
    
    Headers:
    Authorization: Bearer {access_token}
    
    Response:
    {
        "success": bool,
        "data": {
            "total_battles": int,
            "total_victories": int,
            "total_defeats": int,
            "total_draws": int,
            "win_rate": float,
            "total_experience_gained": int,
            "total_currency_earned": int,
            "average_battle_duration": int
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        
        battles = Battle.query.filter(
            (Battle.initiator_id == player_id) | (Battle.opponent_id == player_id),
            Battle.is_finished == True
        ).all()
        
        total = len(battles)
        victories = sum(1 for b in battles if b.result == 'victory')
        defeats = sum(1 for b in battles if b.result == 'defeat')
        draws = sum(1 for b in battles if b.result == 'draw')
        
        win_rate = (victories / total * 100) if total > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'total_battles': total,
                'total_victories': victories,
                'total_defeats': defeats,
                'total_draws': draws,
                'win_rate': round(win_rate, 2),
                'average_battle_duration': 0  # TODO: Calculate from timestamps
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve statistics: {str(e)}'
        }), 500


# ============================================================================
# MOVE LEADERBOARDS & RANKINGS
# ============================================================================

@combat_bp.route('/leaderboards/pvp', methods=['GET'])
def get_pvp_leaderboard():
    """
    Get PvP battle leaderboard
    
    Query Parameters:
    limit - int (default 50, max 100)
    season - string (current, all-time)
    
    Response:
    {
        "success": bool,
        "data": [
            {
                "rank": int,
                "player_name": "string",
                "win_rate": float,
                "total_wins": int,
                "rating": int
            }
        ]
    }
    """
    try:
        limit = min(request.args.get('limit', 50, type=int), 100)
        
        # TODO: Implement ELO or rating system
        # For now, simple win rate based leaderboard
        
        return jsonify({
            'success': True,
            'data': []
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve leaderboard: {str(e)}'
        }), 500
