"""
ChronoRift WebSocket Routes
Handles real-time events, state synchronization, and live notifications
"""

from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
from flask_jwt_extended import decode_token
from datetime import datetime
import uuid
import logging

from app.models import db, Riftwalker, Battle, Echo, Guild, Message, WorldState
from app.utils.decorators import rate_limit

logger = logging.getLogger(__name__)

# Global tracking of connected players
connected_players = {}  # {socket_id: {player_id, rooms: []}}
active_battles = {}     # {battle_id: {participants, state}}


def init_websocket(app, socketio):
    """
    Initialize WebSocket handlers
    
    Args:
        app: Flask application
        socketio: Flask-SocketIO instance
    """
    
    # ============================================================================
    # CONNECTION MANAGEMENT
    # ============================================================================
    
    @socketio.on('connect')
    def handle_connect():
        """
        Handle player connection
        
        Client Event:
        {
            "token": "JWT access token"
        }
        """
        try:
            auth = request.args.get('token')
            if not auth:
                return False
            
            # Decode JWT token
            try:
                payload = decode_token(auth)
                player_id = payload['sub']
            except Exception as e:
                logger.error(f"Token decode failed: {str(e)}")
                return False
            
            player = Riftwalker.query.get(player_id)
            if not player:
                return False
            
            # Register connection
            connected_players[request.sid] = {
                'player_id': player_id,
                'character_name': player.character_name,
                'rooms': [],
                'connected_at': datetime.utcnow()
            }
            
            logger.info(f"Player {player.character_name} connected: {request.sid}")
            
            emit('connection_confirmed', {
                'success': True,
                'session_id': request.sid,
                'player_id': str(player_id),
                'character_name': player.character_name,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Notify others player came online
            emit('player_online', {
                'player_id': str(player_id),
                'character_name': player.character_name,
                'timestamp': datetime.utcnow().isoformat()
            }, broadcast=True, skip_sid=request.sid)
            
            return True
        
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            return False
    
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """
        Handle player disconnection with grace period
        """
        try:
            if request.sid in connected_players:
                player_info = connected_players[request.sid]
                player_id = player_info['player_id']
                character_name = player_info['character_name']
                
                logger.info(f"Player {character_name} disconnected: {request.sid}")
                
                # Notify others player went offline (after 30 second grace period)
                socketio.emit('player_offline', {
                    'player_id': str(player_id),
                    'character_name': character_name,
                    'grace_period': 30,
                    'timestamp': datetime.utcnow().isoformat()
                }, broadcast=True)
                
                del connected_players[request.sid]
        
        except Exception as e:
            logger.error(f"Disconnection error: {str(e)}")
    
    
    @socketio.on('heartbeat')
    def handle_heartbeat():
        """
        Handle player heartbeat (keep-alive)
        
        Client Event:
        {
            "timestamp": "ISO timestamp"
        }
        """
        try:
            if request.sid in connected_players:
                emit('heartbeat_ack', {
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        except Exception as e:
            logger.error(f"Heartbeat error: {str(e)}")
    
    
    # ============================================================================
    # ROOM MANAGEMENT
    # ============================================================================
    
    @socketio.on('join_room')
    def handle_join_room(data):
        """
        Join a WebSocket room (guild, battle, zone, etc)
        
        Client Event:
        {
            "room_type": "string (guild, battle, zone, faction, party)",
            "room_id": "uuid"
        }
        """
        try:
            if request.sid not in connected_players:
                return emit('error', {'message': 'Not authenticated'})
            
            room_type = data.get('room_type')
            room_id = data.get('room_id')
            
            if not room_type or not room_id:
                return emit('error', {'message': 'Room type and ID required'})
            
            room_name = f"{room_type}:{room_id}"
            player_info = connected_players[request.sid]
            
            join_room(room_name)
            player_info['rooms'].append(room_name)
            
            logger.info(f"Player {player_info['character_name']} joined {room_name}")
            
            emit('room_joined', {
                'room_type': room_type,
                'room_id': room_id,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Notify room members
            emit('player_joined_room', {
                'player_id': str(player_info['player_id']),
                'character_name': player_info['character_name'],
                'room_type': room_type,
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_name, skip_sid=request.sid)
        
        except Exception as e:
            logger.error(f"Join room error: {str(e)}")
            emit('error', {'message': str(e)})
    
    
    @socketio.on('leave_room')
    def handle_leave_room(data):
        """
        Leave a WebSocket room
        
        Client Event:
        {
            "room_type": "string",
            "room_id": "uuid"
        }
        """
        try:
            if request.sid not in connected_players:
                return
            
            room_type = data.get('room_type')
            room_id = data.get('room_id')
            room_name = f"{room_type}:{room_id}"
            
            player_info = connected_players[request.sid]
            
            leave_room(room_name)
            if room_name in player_info['rooms']:
                player_info['rooms'].remove(room_name)
            
            # Notify room members
            emit('player_left_room', {
                'player_id': str(player_info['player_id']),
                'character_name': player_info['character_name'],
                'room_type': room_type,
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_name)
        
        except Exception as e:
            logger.error(f"Leave room error: {str(e)}")
    
    
    # ============================================================================
    # BATTLE EVENTS
    # ============================================================================
    
    @socketio.on('battle_start')
    def handle_battle_start(data):
        """
        Broadcast battle start event
        
        Client Event:
        {
            "battle_id": "uuid",
            "battle_type": "string",
            "participants": [...]
        }
        """
        try:
            battle_id = data.get('battle_id')
            
            # Store active battle
            active_battles[battle_id] = {
                'started_at': datetime.utcnow(),
                'participants': data.get('participants', []),
                'round': 1
            }
            
            room_name = f"battle:{battle_id}"
            
            emit('battle_started', {
                'battle_id': battle_id,
                'battle_type': data.get('battle_type'),
                'participants': data.get('participants'),
                'round': 1,
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_name, broadcast=True)
        
        except Exception as e:
            logger.error(f"Battle start error: {str(e)}")
    
    
    @socketio.on('battle_action')
    def handle_battle_action(data):
        """
        Broadcast battle action (attack, move, defend)
        
        Client Event:
        {
            "battle_id": "uuid",
            "actor_id": "uuid",
            "action_type": "string",
            "damage": int,
            "target_health": int
        }
        """
        try:
            battle_id = data.get('battle_id')
            room_name = f"battle:{battle_id}"
            
            emit('battle_action_executed', {
                'actor_id': str(data.get('actor_id')),
                'action_type': data.get('action_type'),
                'damage': data.get('damage'),
                'target_health': data.get('target_health'),
                'effects': data.get('effects', []),
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_name)
        
        except Exception as e:
            logger.error(f"Battle action error: {str(e)}")
    
    
    @socketio.on('battle_round_end')
    def handle_battle_round_end(data):
        """
        Broadcast battle round end
        
        Client Event:
        {
            "battle_id": "uuid",
            "round": int,
            "turn_order": [...]
        }
        """
        try:
            battle_id = data.get('battle_id')
            room_name = f"battle:{battle_id}"
            
            if battle_id in active_battles:
                active_battles[battle_id]['round'] = data.get('round')
            
            emit('round_ended', {
                'round': data.get('round'),
                'turn_order': data.get('turn_order'),
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_name)
        
        except Exception as e:
            logger.error(f"Round end error: {str(e)}")
    
    
    @socketio.on('battle_end')
    def handle_battle_end(data):
        """
        Broadcast battle end
        
        Client Event:
        {
            "battle_id": "uuid",
            "result": "string (victory, defeat, draw)",
            "rewards": {...}
        }
        """
        try:
            battle_id = data.get('battle_id')
            room_name = f"battle:{battle_id}"
            
            # Clean up active battle
            if battle_id in active_battles:
                del active_battles[battle_id]
            
            emit('battle_ended', {
                'battle_id': battle_id,
                'result': data.get('result'),
                'experience_gained': data.get('rewards', {}).get('experience'),
                'currency_earned': data.get('rewards', {}).get('currency'),
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_name)
        
        except Exception as e:
            logger.error(f"Battle end error: {str(e)}")
    
    
    # ============================================================================
    # ECHO EVENTS
    # ============================================================================
    
    @socketio.on('echo_captured')
    def handle_echo_captured(data):
        """
        Broadcast Echo capture event
        
        Client Event:
        {
            "player_id": "uuid",
            "echo_id": "uuid",
            "echo_type": "string",
            "rarity": "string"
        }
        """
        try:
            emit('echo_captured_event', {
                'player_id': str(data.get('player_id')),
                'echo_id': str(data.get('echo_id')),
                'echo_type': data.get('echo_type'),
                'rarity': data.get('rarity'),
                'timestamp': datetime.utcnow().isoformat()
            }, broadcast=True)
        
        except Exception as e:
            logger.error(f"Echo capture error: {str(e)}")
    
    
    @socketio.on('echo_leveled_up')
    def handle_echo_level_up(data):
        """
        Broadcast Echo level up event
        
        Client Event:
        {
            "player_id": "uuid",
            "echo_id": "uuid",
            "new_level": int
        }
        """
        try:
            player_id = data.get('player_id')
            emit('echo_level_up_event', {
                'echo_id': str(data.get('echo_id')),
                'new_level': data.get('new_level'),
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"player:{player_id}")
        
        except Exception as e:
            logger.error(f"Echo level up error: {str(e)}")
    
    
    @socketio.on('echo_evolved')
    def handle_echo_evolved(data):
        """
        Broadcast Echo evolution event
        """
        try:
            emit('echo_evolved_event', {
                'echo_id': str(data.get('echo_id')),
                'new_form': data.get('new_form'),
                'stat_changes': data.get('stat_changes'),
                'timestamp': datetime.utcnow().isoformat()
            }, broadcast=True)
        
        except Exception as e:
            logger.error(f"Echo evolution error: {str(e)}")
    
    
    # ============================================================================
    # CHAT EVENTS
    # ============================================================================
    
    @socketio.on('guild_chat_message')
    def handle_guild_chat(data):
        """
        Broadcast guild chat message
        
        Client Event:
        {
            "guild_id": "uuid",
            "message": "string"
        }
        """
        try:
            if request.sid not in connected_players:
                return emit('error', {'message': 'Not authenticated'})
            
            guild_id = data.get('guild_id')
            message = data.get('message', '').strip()
            
            if not message or len(message) > 500:
                return emit('error', {'message': 'Invalid message'})
            
            player_info = connected_players[request.sid]
            room_name = f"guild:{guild_id}"
            
            emit('guild_message', {
                'player_id': str(player_info['player_id']),
                'character_name': player_info['character_name'],
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_name)
        
        except Exception as e:
            logger.error(f"Guild chat error: {str(e)}")
    
    
    @socketio.on('direct_message')
    def handle_direct_message(data):
        """
        Send direct message to player
        
        Client Event:
        {
            "recipient_id": "uuid",
            "message": "string"
        }
        """
        try:
            if request.sid not in connected_players:
                return emit('error', {'message': 'Not authenticated'})
            
            player_info = connected_players[request.sid]
            recipient_id = data.get('recipient_id')
            message = data.get('message', '').strip()
            
            if not message or len(message) > 500:
                return emit('error', {'message': 'Invalid message'})
            
            # Send to recipient's room
            emit('direct_message_received', {
                'sender_id': str(player_info['player_id']),
                'sender_name': player_info['character_name'],
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"player:{recipient_id}")
        
        except Exception as e:
            logger.error(f"Direct message error: {str(e)}")
    
    
    # ============================================================================
    # ECONOMY EVENTS
    # ============================================================================
    
    @socketio.on('price_update')
    def handle_price_update(data):
        """
        Broadcast marketplace price update
        
        Client Event:
        {
            "item_id": "uuid",
            "price": int,
            "currency": "string"
        }
        """
        try:
            emit('market_price_updated', {
                'item_id': str(data.get('item_id')),
                'price': data.get('price'),
                'currency': data.get('currency'),
                'timestamp': datetime.utcnow().isoformat()
            }, broadcast=True)
        
        except Exception as e:
            logger.error(f"Price update error: {str(e)}")
    
    
    @socketio.on('transaction_completed')
    def handle_transaction(data):
        """
        Broadcast transaction completion
        
        Client Event:
        {
            "player_id": "uuid",
            "transaction_type": "string",
            "amount": int
        }
        """
        try:
            emit('transaction_confirmed', {
                'transaction_type': data.get('transaction_type'),
                'amount': data.get('amount'),
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"player:{data.get('player_id')}")
        
        except Exception as e:
            logger.error(f"Transaction error: {str(e)}")
    
    
    # ============================================================================
    # WORLD EVENTS
    # ============================================================================
    
    @socketio.on('rift_spawned')
    def handle_rift_spawn(data):
        """
        Broadcast rift spawn event
        
        Client Event:
        {
            "event_id": "uuid",
            "zone_id": "uuid",
            "event_type": "string",
            "severity": "string",
            "coordinates": [x, y]
        }
        """
        try:
            zone_id = data.get('zone_id')
            emit('rift_event_spawned', {
                'event_id': str(data.get('event_id')),
                'event_type': data.get('event_type'),
                'severity': data.get('severity'),
                'threat_level': data.get('threat_level'),
                'coordinates': data.get('coordinates'),
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"zone:{zone_id}", broadcast=True)
        
        except Exception as e:
            logger.error(f"Rift spawn error: {str(e)}")
    
    
    @socketio.on('zone_discovered')
    def handle_zone_discovery(data):
        """
        Broadcast zone discovery
        
        Client Event:
        {
            "zone_id": "uuid",
            "player_id": "uuid",
            "is_first_discoverer": bool
        }
        """
        try:
            emit('zone_discovered_event', {
                'zone_id': str(data.get('zone_id')),
                'player_id': str(data.get('player_id')),
                'is_first_discoverer': data.get('is_first_discoverer'),
                'timestamp': datetime.utcnow().isoformat()
            }, broadcast=True)
        
        except Exception as e:
            logger.error(f"Zone discovery error: {str(e)}")
    
    
    @socketio.on('world_state_updated')
    def handle_world_state_update(data):
        """
        Broadcast world state changes
        
        Client Event:
        {
            "world_stability": float,
            "anomaly_level": float,
            "rifts_open": int
        }
        """
        try:
            emit('world_state_changed', {
                'world_stability': data.get('world_stability'),
                'anomaly_level': data.get('anomaly_level'),
                'rifts_open': data.get('rifts_open'),
                'timestamp': datetime.utcnow().isoformat()
            }, broadcast=True)
        
        except Exception as e:
            logger.error(f"World state error: {str(e)}")
    
    
    # ============================================================================
    # FACTION EVENTS
    # ============================================================================
    
    @socketio.on('faction_war_declared')
    def handle_faction_war(data):
        """
        Broadcast faction war declaration
        
        Client Event:
        {
            "faction_id_1": "uuid",
            "faction_id_2": "uuid"
        }
        """
        try:
            emit('faction_war_declared_event', {
                'faction_1_id': str(data.get('faction_id_1')),
                'faction_1_name': data.get('faction_1_name'),
                'faction_2_id': str(data.get('faction_id_2')),
                'faction_2_name': data.get('faction_2_name'),
                'timestamp': datetime.utcnow().isoformat()
            }, broadcast=True)
        
        except Exception as e:
            logger.error(f"War declaration error: {str(e)}")
    
    
    @socketio.on('faction_territory_claimed')
    def handle_territory_claim(data):
        """
        Broadcast faction territory claim
        """
        try:
            emit('territory_claimed_event', {
                'faction_id': str(data.get('faction_id')),
                'zone_id': str(data.get('zone_id')),
                'timestamp': datetime.utcnow().isoformat()
            }, broadcast=True)
        
        except Exception as e:
            logger.error(f"Territory claim error: {str(e)}")
    
    
    # ============================================================================
    # POSITION & STATE SYNCHRONIZATION
    # ============================================================================
    
    @socketio.on('position_update')
    def handle_position_update(data):
        """
        Update player position (throttled, batch updates)
        
        Client Event:
        {
            "zone_id": "uuid",
            "x": float,
            "y": float
        }
        """
        try:
            if request.sid not in connected_players:
                return
            
            player_info = connected_players[request.sid]
            zone_id = data.get('zone_id')
            
            # Broadcast to zone
            emit('player_position_changed', {
                'player_id': str(player_info['player_id']),
                'x': data.get('x'),
                'y': data.get('y'),
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"zone:{zone_id}", skip_sid=request.sid)
        
        except Exception as e:
            logger.error(f"Position update error: {str(e)}")
    
    
    @socketio.on('leaderboard_update')
    def handle_leaderboard_update(data):
        """
        Broadcast leaderboard changes
        
        Client Event:
        {
            "leaderboard_type": "string (level, wealth, exploration)",
            "top_players": [...]
        }
        """
        try:
            emit('leaderboard_updated', {
                'leaderboard_type': data.get('leaderboard_type'),
                'top_players': data.get('top_players'),
                'timestamp': datetime.utcnow().isoformat()
            }, broadcast=True)
        
        except Exception as e:
            logger.error(f"Leaderboard update error: {str(e)}")
    
    
    # ============================================================================
    # UTILITY HANDLERS
    # ============================================================================
    
    @socketio.on_error_default
    def default_error_handler(e):
        """Handle WebSocket errors"""
        logger.error(f"WebSocket error: {str(e)}")
        emit('error', {'message': 'An error occurred'})
    
    
    return socketio
