"""
ChronoRift Rifts Routes
Handles rift mechanics, dimensional events, sealing, and instability management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import uuid
import random

from app.models import db, RiftEvent, RiftInstance, Riftwalker, Echo, Zone, WorldState
from app.schemas import rift_event_schema, rift_events_schema
from app.utils.decorators import validate_json, rate_limit


rifts_bp = Blueprint('rifts', __name__, url_prefix='/api/rifts')


# ============================================================================
# RIFT SPAWNING & DYNAMICS
# ============================================================================

@rifts_bp.route('/spawn', methods=['POST'])
@validate_json
@rate_limit(limit=5, window=3600)
def spawn_rift_event():
    """
    Spawn a new rift event in a zone (admin/system endpoint)
    
    Request Body:
    {
        "zone_id": "uuid",
        "event_type": "string (dimensional_tear, echo_surge, anomaly, temporal_distortion, void_incursion)",
        "severity": "string (minor, moderate, severe, critical)",
        "duration_minutes": int (default 30),
        "coordinates": [x, y] (optional)
    }
    
    Response:
    {
        "success": bool,
        "message": "string",
        "data": {
            "event_id": "uuid",
            "event_type": "string",
            "zone_id": "uuid",
            "severity": "string",
            "threat_level": int (1-10),
            "spawned_at": "ISO timestamp",
            "expires_at": "ISO timestamp",
            "echoes_present": int
        }
    }
    """
    try:
        data = request.get_json()
        zone_id = data.get('zone_id')
        event_type = data.get('event_type', 'dimensional_tear')
        severity = data.get('severity', 'moderate')
        duration_minutes = data.get('duration_minutes', 30)
        
        # Validate inputs
        valid_types = ['dimensional_tear', 'echo_surge', 'anomaly', 'temporal_distortion', 'void_incursion']
        if event_type not in valid_types:
            return jsonify({
                'success': False,
                'message': f'Invalid event type. Must be one of: {", ".join(valid_types)}'
            }), 400
        
        valid_severities = ['minor', 'moderate', 'severe', 'critical']
        if severity not in valid_severities:
            return jsonify({
                'success': False,
                'message': f'Invalid severity. Must be one of: {", ".join(valid_severities)}'
            }), 400
        
        # Verify zone exists
        zone = Zone.query.get(zone_id)
        if not zone:
            return jsonify({
                'success': False,
                'message': 'Zone not found'
            }), 404
        
        # Severity to threat level mapping
        threat_map = {
            'minor': random.randint(1, 2),
            'moderate': random.randint(3, 5),
            'severe': random.randint(6, 8),
            'critical': random.randint(9, 10)
        }
        threat_level = threat_map[severity]
        
        # Create rift event
        expires_at = datetime.utcnow() + timedelta(minutes=duration_minutes)
        
        event = RiftEvent(
            id=uuid.uuid4(),
            zone_id=zone_id,
            event_type=event_type,
            severity=severity,
            threat_level=threat_level,
            description=generate_rift_description(event_type, severity),
            duration_seconds=duration_minutes * 60,
            is_active=True,
            coordinates=data.get('coordinates', [0, 0]),
            dimensional_intensity=50.0 + (threat_level * 5),
            instability_factor=0.3 + (threat_level * 0.07)
        )
        
        db.session.add(event)
        
        # Update world state
        world_state = WorldState.query.order_by(WorldState.updated_at.desc()).first()
        if world_state:
            world_state.total_rifts_open += 1
            world_state.dimensional_anomaly_level = min(100.0, world_state.dimensional_anomaly_level + (threat_level * 2))
            world_state.world_stability = max(0.0, world_state.world_stability - (threat_level * 1.5))
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{event_type} spawned in {zone.name}!',
            'data': {
                'event_id': str(event.id),
                'event_type': event_type,
                'zone_id': str(zone_id),
                'zone_name': zone.name,
                'severity': severity,
                'threat_level': threat_level,
                'spawned_at': event.created_at.isoformat(),
                'expires_at': expires_at.isoformat(),
                'duration_seconds': event.duration_seconds,
                'dimensional_intensity': event.dimensional_intensity
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Rift spawn failed: {str(e)}'
        }), 500


@rifts_bp.route('/active', methods=['GET'])
def list_active_rifts():
    """
    List all active rift events
    
    Query Parameters:
    zone_id - uuid (filter by zone)
    event_type - string (filter by type)
    threat_level_min - int
    threat_level_max - int
    limit - int (default 50, max 100)
    offset - int (default 0)
    
    Response:
    {
        "success": bool,
        "data": [
            {
                "id": "uuid",
                "event_type": "string",
                "severity": "string",
                "threat_level": int,
                "zone_id": "uuid",
                "zone_name": "string",
                "coordinates": [x, y],
                "duration_remaining": int (seconds),
                "participants": int,
                "dimensional_intensity": float
            }
        ],
        "pagination": {...}
    }
    """
    try:
        query = RiftEvent.query.filter_by(is_active=True)
        
        # Apply filters
        zone_id = request.args.get('zone_id', type=str)
        if zone_id:
            query = query.filter_by(zone_id=zone_id)
        
        event_type = request.args.get('event_type', type=str)
        if event_type:
            query = query.filter_by(event_type=event_type)
        
        threat_min = request.args.get('threat_level_min', type=int)
        if threat_min:
            query = query.filter(RiftEvent.threat_level >= threat_min)
        
        threat_max = request.args.get('threat_level_max', type=int)
        if threat_max:
            query = query.filter(RiftEvent.threat_level <= threat_max)
        
        # Pagination
        limit = min(request.args.get('limit', 50, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        
        total = query.count()
        events = query.order_by(RiftEvent.created_at.desc()).limit(limit).offset(offset).all()
        
        # Calculate duration remaining
        events_data = []
        for event in events:
            end_time = event.created_at + timedelta(seconds=event.duration_seconds)
            duration_remaining = max(0, int((end_time - datetime.utcnow()).total_seconds()))
            
            zone = Zone.query.get(event.zone_id)
            
            events_data.append({
                'id': str(event.id),
                'event_type': event.event_type,
                'severity': event.severity,
                'threat_level': event.threat_level,
                'zone_id': str(event.zone_id),
                'zone_name': zone.name if zone else 'Unknown',
                'coordinates': event.coordinates,
                'duration_remaining': duration_remaining,
                'dimensional_intensity': event.dimensional_intensity,
                'instability_factor': event.instability_factor,
                'description': event.description
            })
        
        return jsonify({
            'success': True,
            'data': events_data,
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to list active rifts: {str(e)}'
        }), 500


@rifts_bp.route('/<event_id>', methods=['GET'])
def get_rift_details(event_id):
    """
    Get detailed information about a rift event
    
    URL Parameters:
    event_id - UUID of rift event
    
    Response:
    {
        "success": bool,
        "data": {
            "id": "uuid",
            "event_type": "string",
            "severity": "string",
            "threat_level": int,
            "zone_id": "uuid",
            "zone_name": "string",
            "description": "string",
            "coordinates": [x, y],
            "created_at": "ISO timestamp",
            "duration_remaining": int,
            "dimensional_intensity": float,
            "instability_factor": float,
            "echoes_present": int,
            "active_participants": int,
            "sealing_difficulty": float (0-1),
            "estimated_rewards": {
                "experience": int,
                "currency": int
            }
        }
    }
    """
    try:
        event = RiftEvent.query.get(event_id)
        
        if not event:
            return jsonify({
                'success': False,
                'message': 'Rift event not found'
            }), 404
        
        # Calculate metrics
        end_time = event.created_at + timedelta(seconds=event.duration_seconds)
        duration_remaining = max(0, int((end_time - datetime.utcnow()).total_seconds()))
        
        # Get zone info
        zone = Zone.query.get(event.zone_id)
        
        # Count active participants
        active_instances = RiftInstance.query.filter_by(
            rift_event_id=event.id,
            is_active=True
        ).count()
        
        # Calculate rewards
        base_exp = 500 + (event.threat_level * 200)
        base_currency = 250 + (event.threat_level * 100)
        
        return jsonify({
            'success': True,
            'data': {
                'id': str(event.id),
                'event_type': event.event_type,
                'severity': event.severity,
                'threat_level': event.threat_level,
                'zone_id': str(event.zone_id),
                'zone_name': zone.name if zone else 'Unknown',
                'description': event.description,
                'coordinates': event.coordinates,
                'created_at': event.created_at.isoformat(),
                'duration_remaining': duration_remaining,
                'is_active': event.is_active,
                'dimensional_intensity': event.dimensional_intensity,
                'instability_factor': event.instability_factor,
                'active_participants': active_instances,
                'sealing_difficulty': event.instability_factor,
                'estimated_rewards': {
                    'experience': base_exp,
                    'currency': base_currency
                }
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve rift details: {str(e)}'
        }), 500


# ============================================================================
# RIFT INSTANCE MANAGEMENT
# ============================================================================

@rifts_bp.route('/<event_id>/enter', methods=['POST'])
@jwt_required()
@validate_json
def enter_rift_instance(event_id):
    """
    Enter a rift event instance
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "echo_ids": ["uuid", ...],
        "party_size": int (1-6)
    }
    
    Response:
    {
        "success": bool,
        "message": "string",
        "data": {
            "instance_id": "uuid",
            "rift_event_id": "uuid",
            "threat_level": int,
            "initial_state": {...},
            "session_token": "string"
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        
        event = RiftEvent.query.get(event_id)
        if not event or not event.is_active:
            return jsonify({
                'success': False,
                'message': 'Rift event not found or inactive'
            }), 404
        
        # Check event expiration
        end_time = event.created_at + timedelta(seconds=event.duration_seconds)
        if datetime.utcnow() > end_time:
            event.is_active = False
            db.session.commit()
            return jsonify({
                'success': False,
                'message': 'Rift event has expired'
            }), 410
        
        data = request.get_json()
        echo_ids = data.get('echo_ids', [])
        
        if not echo_ids:
            return jsonify({
                'success': False,
                'message': 'At least one Echo required'
            }), 400
        
        # Validate player echoes
        echoes = Echo.query.filter(
            Echo.id.in_(echo_ids),
            Echo.character_id == player_id,
            Echo.is_active == True
        ).all()
        
        if len(echoes) != len(echo_ids):
            return jsonify({
                'success': False,
                'message': 'Invalid Echo IDs'
            }), 403
        
        # Create instance
        instance = RiftInstance(
            id=uuid.uuid4(),
            rift_event_id=event.id,
            character_id=player_id,
            party_composition=[str(e.id) for e in echoes],
            initial_stability=100.0,
            current_stability=100.0,
            anomaly_level=event.dimensional_intensity,
            round_count=0,
            is_active=True
        )
        
        db.session.add(instance)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Entered rift instance',
            'data': {
                'instance_id': str(instance.id),
                'rift_event_id': str(event_id),
                'threat_level': event.threat_level,
                'event_type': event.event_type,
                'dimensional_intensity': event.dimensional_intensity,
                'initial_stability': instance.initial_stability,
                'session_token': 'session_' + str(uuid.uuid4())
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to enter rift instance: {str(e)}'
        }), 500


@rifts_bp.route('/instances/<instance_id>', methods=['GET'])
@jwt_required()
def get_instance_state(instance_id):
    """
    Get current state of a rift instance
    
    Headers:
    Authorization: Bearer {access_token}
    
    URL Parameters:
    instance_id - UUID of rift instance
    
    Response:
    {
        "success": bool,
        "data": {
            "instance_id": "uuid",
            "rift_event_id": "uuid",
            "status": "string (active, completed, failed, abandoned)",
            "round": int,
            "stability": float (0-100),
            "anomaly_level": float,
            "time_remaining": int (seconds),
            "party_status": [...]
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        
        instance = RiftInstance.query.get(instance_id)
        if not instance:
            return jsonify({
                'success': False,
                'message': 'Instance not found'
            }), 404
        
        # Verify ownership
        if str(instance.character_id) != player_id:
            return jsonify({
                'success': False,
                'message': 'Unauthorized'
            }), 403
        
        event = RiftEvent.query.get(instance.rift_event_id)
        end_time = event.created_at + timedelta(seconds=event.duration_seconds)
        time_remaining = max(0, int((end_time - datetime.utcnow()).total_seconds()))
        
        return jsonify({
            'success': True,
            'data': {
                'instance_id': str(instance.id),
                'rift_event_id': str(instance.rift_event_id),
                'status': 'active' if instance.is_active else 'completed',
                'round': instance.round_count,
                'stability': instance.current_stability,
                'anomaly_level': instance.anomaly_level,
                'time_remaining': time_remaining,
                'threat_level': event.threat_level,
                'total_damage_prevented': instance.total_damage_prevented or 0
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve instance state: {str(e)}'
        }), 500


# ============================================================================
# RIFT SEALING MECHANICS
# ============================================================================

@rifts_bp.route('/<event_id>/seal', methods=['POST'])
@jwt_required()
@validate_json
@rate_limit(limit=5, window=60)
def seal_rift_event(event_id):
    """
    Attempt to seal a rift event
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "instance_id": "uuid",
        "sealing_method": "string (combat, ritual, harmonic, dimensional)",
        "stability_contribution": float (0-100),
        "resources_used": {
            "currency": int,
            "special_items": ["uuid", ...]
        }
    }
    
    Response:
    {
        "success": bool,
        "message": "string",
        "data": {
            "rift_sealed": bool,
            "sealing_success_rate": float,
            "sealing_bonus": int,
            "world_impact": {
                "stability_restored": float,
                "anomaly_reduced": float
            }
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        
        event = RiftEvent.query.get(event_id)
        if not event:
            return jsonify({
                'success': False,
                'message': 'Rift event not found'
            }), 404
        
        data = request.get_json()
        instance_id = data.get('instance_id')
        sealing_method = data.get('sealing_method', 'combat')
        stability_contribution = data.get('stability_contribution', 50.0)
        
        instance = RiftInstance.query.get(instance_id)
        if not instance or str(instance.character_id) != player_id:
            return jsonify({
                'success': False,
                'message': 'Invalid instance'
            }), 403
        
        # Method effectiveness
        method_effectiveness = {
            'combat': 0.6,
            'ritual': 0.8,
            'harmonic': 0.9,
            'dimensional': 0.95
        }
        
        effectiveness = method_effectiveness.get(sealing_method, 0.5)
        
        # Calculate success rate
        success_rate = min(1.0, (stability_contribution / 100) * effectiveness)
        sealed = random.random() < success_rate
        
        if sealed:
            event.is_active = False
            event.sealed_at = datetime.utcnow()
            event.sealed_by_id = player_id
            event.sealing_method = sealing_method
            
            instance.is_active = False
            instance.status = 'completed'
            
            # Update world state
            world_state = WorldState.query.order_by(WorldState.updated_at.desc()).first()
            if world_state:
                world_state.total_rifts_sealed += 1
                world_state.world_stability = min(100.0, world_state.world_stability + 3.0)
                world_state.dimensional_anomaly_level = max(0.0, world_state.dimensional_anomaly_level - 2.0)
            
            # Calculate rewards
            sealing_bonus = int((event.threat_level * 500) * effectiveness)
        else:
            sealing_bonus = 0
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Rift sealing attempt completed',
            'data': {
                'rift_sealed': sealed,
                'sealing_method': sealing_method,
                'sealing_success_rate': round(success_rate, 3),
                'sealing_bonus': sealing_bonus if sealed else 0,
                'world_impact': {
                    'stability_restored': 3.0 if sealed else 0.0,
                    'anomaly_reduced': 2.0 if sealed else 0.0
                } if sealed else None
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Rift sealing failed: {str(e)}'
        }), 500


# ============================================================================
# RIFT INSTABILITY & EVENTS
# ============================================================================

@rifts_bp.route('/instances/<instance_id>/stabilize', methods=['POST'])
@jwt_required()
@validate_json
def stabilize_instance(instance_id):
    """
    Stabilize rift instance to prevent degradation
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "stabilization_amount": float (0-100)
    }
    
    Response:
    {
        "success": bool,
        "data": {
            "previous_stability": float,
            "new_stability": float,
            "stabilization_applied": float
        }
    }
    """
    try:
        player_id = get_jwt_identity()
        
        instance = RiftInstance.query.get(instance_id)
        if not instance or str(instance.character_id) != player_id:
            return jsonify({
                'success': False,
                'message': 'Instance not found or unauthorized'
            }), 403
        
        data = request.get_json()
        stabilization = data.get('stabilization_amount', 10.0)
        
        previous_stability = instance.current_stability
        instance.current_stability = min(100.0, instance.current_stability + stabilization)
        instance.total_damage_prevented = (instance.total_damage_prevented or 0) + int(stabilization)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'previous_stability': previous_stability,
                'new_stability': instance.current_stability,
                'stabilization_applied': stabilization
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Stabilization failed: {str(e)}'
        }), 500


@rifts_bp.route('/instances/<instance_id>/abandon', methods=['POST'])
@jwt_required()
def abandon_instance(instance_id):
    """
    Abandon a rift instance
    
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
        
        instance = RiftInstance.query.get(instance_id)
        if not instance or str(instance.character_id) != player_id:
            return jsonify({
                'success': False,
                'message': 'Instance not found'
            }), 403
        
        instance.is_active = False
        instance.status = 'abandoned'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Instance abandoned'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Abandonment failed: {str(e)}'
        }), 500


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_rift_description(event_type, severity):
    """
    Generate descriptive text for rift events
    """
    descriptions = {
        'dimensional_tear': {
            'minor': 'A small tear in reality opens, revealing glimpses of other dimensions.',
            'moderate': 'A significant dimensional rift tears open, destabilizing the area.',
            'severe': 'A massive rift rends the fabric of reality, threatening the entire zone.',
            'critical': 'Reality itself fractures as a catastrophic dimensional tear consumes everything.'
        },
        'echo_surge': {
            'minor': 'A faint pulse of Echo energy emanates from the ground.',
            'moderate': 'Echoes swarm the area, responding to a surge of dimensional energy.',
            'severe': 'An overwhelming surge of Echo energy floods the zone.',
            'critical': 'An apocalyptic Echo surge threatens to consume all life in the region.'
        },
        'anomaly': {
            'minor': 'Strange phenomena distort the environment slightly.',
            'moderate': 'Spacetime anomalies begin warping the landscape.',
            'severe': 'Multiple reality-bending anomalies create dangerous conditions.',
            'critical': 'The laws of physics break down as anomalies consume the zone.'
        },
        'temporal_distortion': {
            'minor': 'Time flows irregularly in a small area.',
            'moderate': 'Temporal distortions create pockets of altered time.',
            'severe': 'Time itself becomes chaotic and unpredictable.',
            'critical': 'Temporal collapse threatens to erase history itself.'
        },
        'void_incursion': {
            'minor': 'The void peers into reality, causing unease.',
            'moderate': 'A void intrusion opens, pulling at reality\'s fabric.',
            'severe': 'The void expands, consuming everything in its path.',
            'critical': 'The void consumes all, threatening complete annihilation.'
        }
    }
    
    return descriptions.get(event_type, {}).get(severity, 'An unknown rift event occurs.')


# ============================================================================
# RIFT STATISTICS & LEADERBOARDS
# ============================================================================

@rifts_bp.route('/leaderboards/sealers', methods=['GET'])
def get_sealer_leaderboard():
    """
    Get leaderboard of rift sealers
    
    Query Parameters:
    limit - int (default 50, max 100)
    period - string (day, week, month, all-time)
    
    Response:
    {
        "success": bool,
        "data": [
            {
                "rank": int,
                "player_name": "string",
                "rifts_sealed": int,
                "bonus_points": int,
                "preferred_method": "string"
            }
        ]
    }
    """
    try:
        limit = min(request.args.get('limit', 50, type=int), 100)
        
        sealed_events = RiftEvent.query.filter(
            RiftEvent.sealed_at != None
        ).order_by(RiftEvent.sealed_at.desc()).limit(limit).all()
        
        # Aggregate by sealer
        sealer_stats = {}
        for event in sealed_events:
            sealer_id = str(event.sealed_by_id)
            if sealer_id not in sealer_stats:
                sealer_stats[sealer_id] = {
                    'rifts_sealed': 0,
                    'bonus_points': 0,
                    'methods': {}
                }
            
            sealer_stats[sealer_id]['rifts_sealed'] += 1
            sealer_stats[sealer_id]['bonus_points'] += event.threat_level * 500
            method = event.sealing_method or 'unknown'
            sealer_stats[sealer_id]['methods'][method] = sealer_stats[sealer_id]['methods'].get(method, 0) + 1
        
        # Format leaderboard
        leaderboard = []
        for rank, (sealer_id, stats) in enumerate(sorted(sealer_stats.items(), 
            key=lambda x: x[1]['bonus_points'], reverse=True)[:limit]):
            
            preferred_method = max(stats['methods'].items(), key=lambda x: x[1])[0]
            
            leaderboard.append({
                'rank': rank + 1,
                'sealer_id': sealer_id,
                'rifts_sealed': stats['rifts_sealed'],
                'bonus_points': stats['bonus_points'],
                'preferred_method': preferred_method
            })
        
        return jsonify({
            'success': True,
            'data': leaderboard
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve leaderboard: {str(e)}'
        }), 500
