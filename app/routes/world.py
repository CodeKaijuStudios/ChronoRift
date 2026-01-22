"""
ChronoRift World Routes
Handles world exploration, zones, rift events, and environmental state management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import uuid
import random

from app.models import db, Zone, RiftEvent, WorldState, Riftwalker, Echo
from app.schemas import zone_schema, zones_schema, rift_event_schema, rift_events_schema
from app.utils.decorators import validate_json, rate_limit


world_bp = Blueprint('world', __name__, url_prefix='/api/world')


# ============================================================================
# WORLD STATE & EXPLORATION
# ============================================================================

@world_bp.route('/state', methods=['GET'])
def get_world_state():
    """
    Get current global world state
    
    Response:
    {
        "success": bool,
        "data": {
            "current_time": "ISO timestamp",
            "total_rifts_open": int,
            "total_rifts_sealed": int,
            "world_stability": float (0-100),
            "dimensional_anomaly_level": float (0-100),
            "active_events": int,
            "factions_at_war": int,
            "global_events": [...]
        }
    }
    """
    try:
        world_state = WorldState.query.order_by(WorldState.updated_at.desc()).first()
        
        if not world_state:
            # Initialize world state if not exists
            world_state = WorldState(
                id=uuid.uuid4(),
                current_time=datetime.utcnow(),
                total_rifts_open=0,
                total_rifts_sealed=0,
                world_stability=75.0,
                dimensional_anomaly_level=25.0
            )
            db.session.add(world_state)
            db.session.commit()
        
        # Count active events
        active_events = RiftEvent.query.filter_by(is_active=True).count()
        
        return jsonify({
            'success': True,
            'data': {
                'current_time': world_state.current_time.isoformat(),
                'total_rifts_open': world_state.total_rifts_open,
                'total_rifts_sealed': world_state.total_rifts_sealed,
                'world_stability': world_state.world_stability,
                'dimensional_anomaly_level': world_state.dimensional_anomaly_level,
                'active_events': active_events,
                'last_updated': world_state.updated_at.isoformat()
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve world state: {str(e)}'
        }), 500


@world_bp.route('/progress', methods=['GET'])
def get_world_progress():
    """
    Get aggregate world progress statistics
    
    Response:
    {
        "success": bool,
        "data": {
            "total_players": int,
            "total_rifts_sealed": int,
            "total_echoes_captured": int,
            "faction_strengths": {...},
            "world_threats": [...],
            "community_milestones": [...]
        }
    }
    """
    try:
        total_players = Riftwalker.query.filter_by(is_active=True).count()
        world_state = WorldState.query.order_by(WorldState.updated_at.desc()).first()
        
        # Count total echoes captured
        total_echoes = Echo.query.filter_by(is_active=True).count()
        
        return jsonify({
            'success': True,
            'data': {
                'total_players': total_players,
                'total_rifts_sealed': world_state.total_rifts_sealed if world_state else 0,
                'total_echoes_captured': total_echoes,
                'world_stability': world_state.world_stability if world_state else 75.0,
                'dimensional_threat': world_state.dimensional_anomaly_level if world_state else 25.0,
                'last_updated': world_state.updated_at.isoformat() if world_state else None
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve progress: {str(e)}'
        }), 500


# ============================================================================
# ZONE EXPLORATION & DISCOVERY
# ============================================================================

@world_bp.route('/zones', methods=['GET'])
def list_zones():
    """
    List all explorable zones with optional filtering
    
    Query Parameters:
    region - string (filter by region)
    difficulty - string (novice, intermediate, advanced, legendary)
    discovered_only - boolean (only show discovered zones)
    limit - int (default 50, max 100)
    offset - int (default 0)
    
    Response:
    {
        "success": bool,
        "data": [
            {
                "id": "uuid",
                "name": "string",
                "region": "string",
                "difficulty": "string",
                "description": "string",
                "environment": "string",
                "level_range": {"min": int, "max": int},
                "discovered": bool,
                "feature_count": int
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
        query = Zone.query.filter_by(is_active=True)
        
        # Apply filters
        region = request.args.get('region', type=str)
        if region:
            query = query.filter_by(region=region)
        
        difficulty = request.args.get('difficulty', type=str)
        if difficulty:
            query = query.filter_by(difficulty=difficulty)
        
        discovered_only = request.args.get('discovered_only', False, type=bool)
        if discovered_only:
            query = query.filter(Zone.total_discoveries > 0)
        
        # Pagination
        limit = min(request.args.get('limit', 50, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        
        total = query.count()
        zones = query.order_by(Zone.name.asc()).limit(limit).offset(offset).all()
        
        return jsonify({
            'success': True,
            'data': zones_schema.dump(zones),
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to list zones: {str(e)}'
        }), 500


@world_bp.route('/zones/<zone_id>', methods=['GET'])
def get_zone_details(zone_id):
    """
    Get detailed information about a specific zone
    
    URL Parameters:
    zone_id - UUID of zone
    
    Response:
    {
        "success": bool,
        "data": {
            "id": "uuid",
            "name": "string",
            "description": "string",
            "region": "string",
            "environment": "string",
            "difficulty": "string",
            "level_range": {"min": int, "max": int},
            "features": [
                {"type": "string", "name": "string", "coordinates": [...]}
            ],
            "echo_types": ["uuid", ...],
            "item_drops": [{"item_id": "uuid", "rarity": "string", "drop_rate": float}],
            "total_discoverers": int,
            "discovered_at": "ISO timestamp or null",
            "controlledby_faction": "uuid or null",
            "active_rifts": int,
            "weather": "string",
            "time_of_day": "string"
        }
    }
    """
    try:
        zone = Zone.query.get(zone_id)
        
        if not zone:
            return jsonify({
                'success': False,
                'message': 'Zone not found'
            }), 404
        
        active_rifts = RiftEvent.query.filter_by(zone_id=zone_id, is_active=True).count()
        
        return jsonify({
            'success': True,
            'data': {
                **zone_schema.dump(zone),
                'active_rifts': active_rifts,
                'total_discoverers': zone.total_discoveries,
                'features_count': len(zone.features) if zone.features else 0
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve zone details: {str(e)}'
        }), 500


@world_bp.route('/zones/<zone_id>/discover', methods=['POST'])
@jwt_required()
def discover_zone(zone_id):
    """
    Record zone discovery for character
    
    Headers:
    Authorization: Bearer {access_token}
    
    URL Parameters:
    zone_id - UUID of zone
    
    Response:
    {
        "success": bool,
        "message": "string",
        "data": {
            "zone_name": "string",
            "is_first_discoverer": bool,
            "discovery_reward": int
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
        
        zone = Zone.query.get(zone_id)
        if not zone:
            return jsonify({
                'success': False,
                'message': 'Zone not found'
            }), 404
        
        # Check if already discovered
        if zone_id in (character.discovered_zones or []):
            return jsonify({
                'success': True,
                'message': 'Zone already discovered',
                'data': {
                    'zone_name': zone.name,
                    'is_first_discoverer': False,
                    'discovery_reward': 0
                }
            }), 200
        
        # Record discovery
        if not character.discovered_zones:
            character.discovered_zones = []
        
        is_first = zone.total_discoveries == 0
        discovery_reward = 500 if is_first else 100
        
        character.discovered_zones.append(zone_id)
        zone.total_discoveries += 1
        character.exploration_points = (character.exploration_points or 0) + discovery_reward
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Discovered {zone.name}!',
            'data': {
                'zone_name': zone.name,
                'is_first_discoverer': is_first,
                'discovery_reward': discovery_reward,
                'exploration_points_total': character.exploration_points
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Discovery failed: {str(e)}'
        }), 500


# ============================================================================
# RIFT EVENTS & ENCOUNTERS
# ============================================================================

@world_bp.route('/rifts', methods=['GET'])
def list_rift_events():
    """
    List active rift events across world
    
    Query Parameters:
    zone_id - uuid (filter by zone)
    event_type - string (dimensional_tear, echo_surge, anomaly, etc)
    severity - string (minor, moderate, severe, critical)
    active_only - boolean (default true)
    limit - int (default 50)
    offset - int (default 0)
    
    Response:
    {
        "success": bool,
        "data": [
            {
                "id": "uuid",
                "event_type": "string",
                "zone_id": "uuid",
                "zone_name": "string",
                "severity": "string",
                "description": "string",
                "coordinates": [x, y],
                "active": bool,
                "started_at": "ISO timestamp",
                "duration_remaining": int (seconds),
                "echoes_present": int,
                "player_count": int
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
        
        severity = request.args.get('severity', type=str)
        if severity:
            query = query.filter_by(severity=severity)
        
        # Pagination
        limit = min(request.args.get('limit', 50, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        
        total = query.count()
        events = query.order_by(RiftEvent.created_at.desc()).limit(limit).offset(offset).all()
        
        return jsonify({
            'success': True,
            'data': rift_events_schema.dump(events),
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to list rift events: {str(e)}'
        }), 500


@world_bp.route('/rifts/<event_id>', methods=['GET'])
def get_rift_event(event_id):
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
            "zone_id": "uuid",
            "zone_name": "string",
            "description": "string",
            "coordinates": [x, y],
            "started_at": "ISO timestamp",
            "duration_remaining": int,
            "active": bool,
            "threat_level": int (1-10),
            "echoes_present": int,
            "rewards": {
                "experience": int,
                "currency": int
            },
            "danger_indicators": [...],
            "nearby_features": [...]
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
        
        # Calculate duration remaining
        end_time = event.created_at + timedelta(seconds=event.duration_seconds)
        duration_remaining = max(0, int((end_time - datetime.utcnow()).total_seconds()))
        
        # Calculate threat level (1-10)
        severity_scale = {
            'minor': 1,
            'moderate': 4,
            'severe': 7,
            'critical': 10
        }
        threat_level = severity_scale.get(event.severity, 5)
        
        return jsonify({
            'success': True,
            'data': {
                **rift_event_schema.dump(event),
                'duration_remaining': duration_remaining,
                'threat_level': threat_level,
                'is_expired': duration_remaining <= 0
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve rift event: {str(e)}'
        }), 500


@world_bp.route('/rifts/<event_id>/enter', methods=['POST'])
@jwt_required()
@validate_json
def enter_rift_event(event_id):
    """
    Enter a rift event encounter
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "echo_id": "uuid (optional - Echo to bring)"
    }
    
    Response:
    {
        "success": bool,
        "message": "string",
        "data": {
            "encounter_id": "uuid",
            "event_type": "string",
            "threat_level": int,
            "initial_echoes": int,
            "rewards_available": {
                "experience": int,
                "currency": int
            }
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
        
        event = RiftEvent.query.get(event_id)
        if not event or not event.is_active:
            return jsonify({
                'success': False,
                'message': 'Rift event not found or inactive'
            }), 404
        
        # Check if event is expired
        end_time = event.created_at + timedelta(seconds=event.duration_seconds)
        if datetime.utcnow() > end_time:
            event.is_active = False
            db.session.commit()
            return jsonify({
                'success': False,
                'message': 'Rift event has expired'
            }), 410
        
        data = request.get_json()
        echo_id = data.get('echo_id')
        
        # TODO: Create encounter session record
        
        # Calculate rewards
        exp_reward = int(event.threat_level * 100 + random.randint(50, 200))
        currency_reward = int(event.threat_level * 50 + random.randint(25, 100))
        
        return jsonify({
            'success': True,
            'message': f'Entered {event.event_type} rift event',
            'data': {
                'encounter_id': str(uuid.uuid4()),
                'event_type': event.event_type,
                'threat_level': event.threat_level,
                'echoes_present': 1,
                'rewards_available': {
                    'experience': exp_reward,
                    'currency': currency_reward
                }
            }
        }), 201
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to enter rift event: {str(e)}'
        }), 500


@world_bp.route('/rifts/seal', methods=['POST'])
@jwt_required()
@validate_json
@rate_limit(limit=10, window=3600)
def seal_rift():
    """
    Seal an active rift event
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "event_id": "uuid",
        "method": "string (combat, ritual, harmonic, etc)"
    }
    
    Response:
    {
        "success": bool,
        "message": "string",
        "data": {
            "rift_sealed": bool,
            "sealing_bonus": int,
            "world_stability_change": float
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
        event_id = data.get('event_id')
        method = data.get('method', 'combat')
        
        event = RiftEvent.query.get(event_id)
        if not event:
            return jsonify({
                'success': False,
                'message': 'Rift event not found'
            }), 404
        
        event.is_active = False
        event.sealed_at = datetime.utcnow()
        
        # Update world state
        world_state = WorldState.query.order_by(WorldState.updated_at.desc()).first()
        if world_state:
            world_state.total_rifts_sealed += 1
            world_state.world_stability = min(100.0, world_state.world_stability + 2.5)
            world_state.dimensional_anomaly_level = max(0.0, world_state.dimensional_anomaly_level - 1.5)
        
        # Calculate rewards
        sealing_bonus = 500 + (event.threat_level * 100)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Rift sealed using {method}!',
            'data': {
                'rift_sealed': True,
                'sealing_bonus': sealing_bonus,
                'world_stability_change': 2.5
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Rift sealing failed: {str(e)}'
        }), 500


# ============================================================================
# ENVIRONMENTAL & TEMPORAL MECHANICS
# ============================================================================

@world_bp.route('/weather/<zone_id>', methods=['GET'])
def get_zone_weather(zone_id):
    """
    Get current weather conditions in zone
    
    URL Parameters:
    zone_id - UUID of zone
    
    Response:
    {
        "success": bool,
        "data": {
            "zone_id": "uuid",
            "current_weather": "string",
            "temperature": int,
            "visibility": string (poor, moderate, good, excellent),
            "precipitation": float (0-100),
            "wind_speed": int,
            "atmospheric_anomaly": float (0-100),
            "effect_on_echoes": "string"
        }
    }
    """
    try:
        zone = Zone.query.get(zone_id)
        
        if not zone:
            return jsonify({
                'success': False,
                'message': 'Zone not found'
            }), 404
        
        # TODO: Implement weather system with procedural generation
        # For now, return simple weather data
        
        return jsonify({
            'success': True,
            'data': {
                'zone_id': str(zone_id),
                'current_weather': zone.weather or 'clear',
                'temperature': zone.temperature or 20,
                'visibility': 'good',
                'precipitation': 0.0,
                'wind_speed': 5,
                'atmospheric_anomaly': zone.dimensional_intensity or 10.0,
                'effect_on_echoes': 'Normal'
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve weather: {str(e)}'
        }), 500


@world_bp.route('/time', methods=['GET'])
def get_world_time():
    """
    Get current world time
    
    Response:
    {
        "success": bool,
        "data": {
            "current_time": "ISO timestamp",
            "time_of_day": "string (morning, afternoon, evening, night)",
            "day_cycle": float (0-1),
            "season": "string (spring, summer, autumn, winter)"
        }
    }
    """
    try:
        world_state = WorldState.query.order_by(WorldState.updated_at.desc()).first()
        current_time = world_state.current_time if world_state else datetime.utcnow()
        
        # Calculate time of day
        hour = current_time.hour
        if 6 <= hour < 12:
            time_of_day = 'morning'
        elif 12 <= hour < 18:
            time_of_day = 'afternoon'
        elif 18 <= hour < 21:
            time_of_day = 'evening'
        else:
            time_of_day = 'night'
        
        # Calculate day cycle (0-1, where 0.5 is noon)
        day_cycle = (hour + current_time.minute / 60) / 24
        
        # Calculate season (simplified)
        month = current_time.month
        if 3 <= month < 6:
            season = 'spring'
        elif 6 <= month < 9:
            season = 'summer'
        elif 9 <= month < 12:
            season = 'autumn'
        else:
            season = 'winter'
        
        return jsonify({
            'success': True,
            'data': {
                'current_time': current_time.isoformat(),
                'time_of_day': time_of_day,
                'day_cycle': day_cycle,
                'season': season,
                'hour': hour,
                'day_of_year': current_time.timetuple().tm_yday
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve world time: {str(e)}'
        }), 500


# ============================================================================
# WORLD STATISTICS & LEADERBOARDS
# ============================================================================

@world_bp.route('/explorers/leaderboard', methods=['GET'])
def get_explorer_leaderboard():
    """
    Get leaderboard of top explorers by discoveries
    
    Query Parameters:
    limit - int (default 50, max 100)
    
    Response:
    {
        "success": bool,
        "data": [
            {
                "rank": int,
                "character_name": "string",
                "zones_discovered": int,
                "exploration_points": int,
                "level": int
            }
        ]
    }
    """
    try:
        limit = min(request.args.get('limit', 50, type=int), 100)
        
        explorers = Riftwalker.query.filter_by(is_active=True).order_by(
            Riftwalker.exploration_points.desc(),
            Riftwalker.level.desc()
        ).limit(limit).all()
        
        leaderboard = [
            {
                'rank': i + 1,
                'character_name': explorer.character_name,
                'zones_discovered': len(explorer.discovered_zones) if explorer.discovered_zones else 0,
                'exploration_points': explorer.exploration_points or 0,
                'level': explorer.level
            }
            for i, explorer in enumerate(explorers)
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


@world_bp.route('/region-control', methods=['GET'])
def get_region_control():
    """
    Get faction control status of regions
    
    Response:
    {
        "success": bool,
        "data": [
            {
                "region": "string",
                "controlling_faction": "uuid",
                "faction_name": "string",
                "control_percentage": float,
                "contested": bool,
                "zones_in_region": int
            }
        ]
    }
    """
    try:
        zones = Zone.query.filter_by(is_active=True).all()
        
        # Aggregate by region
        region_data = {}
        for zone in zones:
            region = zone.region or 'Unknown'
            
            if region not in region_data:
                region_data[region] = {
                    'total_zones': 0,
                    'faction_control': {}
                }
            
            region_data[region]['total_zones'] += 1
            
            if zone.controlling_faction_id:
                faction_id = str(zone.controlling_faction_id)
                region_data[region]['faction_control'][faction_id] = region_data[region]['faction_control'].get(faction_id, 0) + 1
        
        # Format response
        response_data = []
        for region, data in region_data.items():
            if data['faction_control']:
                dominant_faction = max(data['faction_control'].items(), key=lambda x: x[1])
                faction_id, controlled_count = dominant_faction
                control_percent = (controlled_count / data['total_zones']) * 100
                
                response_data.append({
                    'region': region,
                    'controlling_faction': faction_id,
                    'control_percentage': round(control_percent, 1),
                    'contested': control_percent < 75,
                    'zones_in_region': data['total_zones']
                })
        
        return jsonify({
            'success': True,
            'data': response_data
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve region control: {str(e)}'
        }), 500
