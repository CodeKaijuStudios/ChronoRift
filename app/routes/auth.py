"""
ChronoRift Authentication Routes
Handles user authentication, authorization, and session management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import uuid

from app.models import db, Riftwalker
from app.schemas import riftwalker_schema, riftwalkers_schema
from app.utils.decorators import rate_limit, admin_required, validate_json


auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@auth_bp.route('/register', methods=['POST'])
@rate_limit(limit=5, window=3600)  # 5 requests per hour
@validate_json
def register():
    """
    Register a new player account
    
    Request Body:
    {
        "username": "string (3-50 chars)",
        "email": "string (valid email)",
        "password": "string (min 8 chars)",
        "display_name": "string (optional)"
    }
    
    Response:
    {
        "success": bool,
        "message": "string",
        "data": {
            "id": "uuid",
            "username": "string",
            "email": "string",
            "display_name": "string",
            "created_at": "ISO timestamp"
        },
        "tokens": {
            "access_token": "JWT",
            "refresh_token": "JWT"
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('username') or len(data['username']) < 3 or len(data['username']) > 50:
            return jsonify({
                'success': False,
                'message': 'Username must be between 3 and 50 characters'
            }), 400
        
        if not data.get('email') or '@' not in data['email']:
            return jsonify({
                'success': False,
                'message': 'Valid email is required'
            }), 400
        
        if not data.get('password') or len(data['password']) < 8:
            return jsonify({
                'success': False,
                'message': 'Password must be at least 8 characters'
            }), 400
        
        # Check for existing username/email
        existing_user = Riftwalker.query.filter_by(username=data['username']).first()
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'Username already taken'
            }), 409
        
        existing_email = Riftwalker.query.filter_by(email=data['email']).first()
        if existing_email:
            return jsonify({
                'success': False,
                'message': 'Email already registered'
            }), 409
        
        # Create new player
        new_player = Riftwalker(
            id=uuid.uuid4(),
            username=data['username'],
            email=data['email'],
            display_name=data.get('display_name', data['username']),
            password_hash=generate_password_hash(data['password']),
            level=1,
            experience=0,
            health=100,
            max_health=100,
            mana=50,
            max_mana=50,
            is_active=True
        )
        
        db.session.add(new_player)
        db.session.commit()
        
        # Generate tokens
        access_token = create_access_token(identity=str(new_player.id))
        refresh_token = create_refresh_token(identity=str(new_player.id))
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'data': riftwalker_schema.dump(new_player),
            'tokens': {
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Registration failed: {str(e)}'
        }), 500


@auth_bp.route('/login', methods=['POST'])
@rate_limit(limit=10, window=600)  # 10 requests per 10 minutes
@validate_json
def login():
    """
    Authenticate player and return tokens
    
    Request Body:
    {
        "username": "string",
        "password": "string"
    }
    
    Response:
    {
        "success": bool,
        "message": "string",
        "data": {
            "id": "uuid",
            "username": "string",
            "display_name": "string",
            "level": int,
            "faction_id": "uuid or null"
        },
        "tokens": {
            "access_token": "JWT",
            "refresh_token": "JWT"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return jsonify({
                'success': False,
                'message': 'Username and password required'
            }), 400
        
        # Find player
        player = Riftwalker.query.filter_by(username=data['username']).first()
        
        if not player or not check_password_hash(player.password_hash, data['password']):
            return jsonify({
                'success': False,
                'message': 'Invalid username or password'
            }), 401
        
        if not player.is_active:
            return jsonify({
                'success': False,
                'message': 'Account is inactive'
            }), 403
        
        # Update last login
        player.last_login = datetime.utcnow()
        db.session.commit()
        
        # Generate tokens
        access_token = create_access_token(identity=str(player.id))
        refresh_token = create_refresh_token(identity=str(player.id))
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'data': riftwalker_schema.dump(player),
            'tokens': {
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Login failed: {str(e)}'
        }), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token using refresh token
    
    Headers:
    Authorization: Bearer {refresh_token}
    
    Response:
    {
        "success": bool,
        "message": "string",
        "access_token": "JWT"
    }
    """
    try:
        identity = get_jwt_identity()
        access_token = create_access_token(identity=identity)
        
        return jsonify({
            'success': True,
            'message': 'Token refreshed',
            'access_token': access_token
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Token refresh failed: {str(e)}'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout player (client-side token management)
    
    Headers:
    Authorization: Bearer {access_token}
    
    Response:
    {
        "success": bool,
        "message": "string"
    }
    """
    try:
        identity = get_jwt_identity()
        
        # Optional: Add token to blacklist or invalidate session
        # This would be implementation-specific
        
        return jsonify({
            'success': True,
            'message': 'Logout successful'
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Logout failed: {str(e)}'
        }), 500


# ============================================================================
# ACCOUNT MANAGEMENT ENDPOINTS
# ============================================================================

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
@validate_json
def change_password():
    """
    Change player password
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "current_password": "string",
        "new_password": "string (min 8 chars)",
        "confirm_password": "string"
    }
    
    Response:
    {
        "success": bool,
        "message": "string"
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
        
        # Verify current password
        if not check_password_hash(player.password_hash, data.get('current_password', '')):
            return jsonify({
                'success': False,
                'message': 'Current password is incorrect'
            }), 401
        
        # Validate new password
        if not data.get('new_password') or len(data['new_password']) < 8:
            return jsonify({
                'success': False,
                'message': 'New password must be at least 8 characters'
            }), 400
        
        if data.get('new_password') != data.get('confirm_password'):
            return jsonify({
                'success': False,
                'message': 'Passwords do not match'
            }), 400
        
        # Update password
        player.password_hash = generate_password_hash(data['new_password'])
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Password change failed: {str(e)}'
        }), 500


@auth_bp.route('/verify-email', methods=['POST'])
@rate_limit(limit=3, window=3600)
@validate_json
def verify_email():
    """
    Request email verification (send verification link)
    
    Request Body:
    {
        "email": "string"
    }
    
    Response:
    {
        "success": bool,
        "message": "string"
    }
    """
    try:
        data = request.get_json()
        email = data.get('email')
        
        player = Riftwalker.query.filter_by(email=email).first()
        if not player:
            # Don't reveal if email exists for security
            return jsonify({
                'success': True,
                'message': 'If email exists, verification link has been sent'
            }), 200
        
        if player.email_verified:
            return jsonify({
                'success': True,
                'message': 'Email already verified'
            }), 200
        
        # TODO: Generate verification token and send email
        # verification_token = generate_verification_token(player.id)
        # send_verification_email(player.email, verification_token)
        
        return jsonify({
            'success': True,
            'message': 'Verification link sent to email'
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Email verification request failed: {str(e)}'
        }), 500


@auth_bp.route('/confirm-email/<token>', methods=['POST'])
def confirm_email(token):
    """
    Confirm email verification with token
    
    URL Parameters:
    token - Email verification token
    
    Response:
    {
        "success": bool,
        "message": "string"
    }
    """
    try:
        # TODO: Verify token and mark email as verified
        # player_id = verify_email_token(token)
        # if not player_id:
        #     return error response
        
        # player = Riftwalker.query.get(player_id)
        # player.email_verified = True
        # db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Email verified successfully'
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Email confirmation failed: {str(e)}'
        }), 500


@auth_bp.route('/forgot-password', methods=['POST'])
@rate_limit(limit=3, window=3600)
@validate_json
def forgot_password():
    """
    Request password reset (send reset email)
    
    Request Body:
    {
        "email": "string"
    }
    
    Response:
    {
        "success": bool,
        "message": "string"
    }
    """
    try:
        data = request.get_json()
        email = data.get('email')
        
        player = Riftwalker.query.filter_by(email=email).first()
        if not player:
            # Don't reveal if email exists for security
            return jsonify({
                'success': True,
                'message': 'If email exists, password reset link has been sent'
            }), 200
        
        # TODO: Generate reset token and send email
        # reset_token = generate_password_reset_token(player.id)
        # send_password_reset_email(player.email, reset_token)
        
        return jsonify({
            'success': True,
            'message': 'Password reset link sent to email'
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Password reset request failed: {str(e)}'
        }), 500


@auth_bp.route('/reset-password/<token>', methods=['POST'])
@validate_json
def reset_password(token):
    """
    Reset password with reset token
    
    URL Parameters:
    token - Password reset token
    
    Request Body:
    {
        "password": "string (min 8 chars)",
        "confirm_password": "string"
    }
    
    Response:
    {
        "success": bool,
        "message": "string"
    }
    """
    try:
        data = request.get_json()
        
        # TODO: Verify reset token
        # player_id = verify_password_reset_token(token)
        # if not player_id:
        #     return error response
        
        # Validate password
        if not data.get('password') or len(data['password']) < 8:
            return jsonify({
                'success': False,
                'message': 'Password must be at least 8 characters'
            }), 400
        
        if data.get('password') != data.get('confirm_password'):
            return jsonify({
                'success': False,
                'message': 'Passwords do not match'
            }), 400
        
        # TODO: Update password
        # player = Riftwalker.query.get(player_id)
        # player.password_hash = generate_password_hash(data['password'])
        # db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Password reset successfully'
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Password reset failed: {str(e)}'
        }), 500


# ============================================================================
# CURRENT USER ENDPOINTS
# ============================================================================

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current authenticated player profile
    
    Headers:
    Authorization: Bearer {access_token}
    
    Response:
    {
        "success": bool,
        "data": {
            "id": "uuid",
            "username": "string",
            "display_name": "string",
            "email": "string",
            "level": int,
            "experience": int,
            "faction_id": "uuid or null",
            "guild_id": "uuid or null",
            "created_at": "ISO timestamp"
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
            'data': riftwalker_schema.dump(player)
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve player: {str(e)}'
        }), 500


@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
@validate_json
def update_current_user():
    """
    Update current player profile
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "display_name": "string (optional)",
        "bio": "string (optional)"
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
        player = Riftwalker.query.get(player_id)
        
        if not player:
            return jsonify({
                'success': False,
                'message': 'Player not found'
            }), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'display_name' in data:
            player.display_name = data['display_name']
        
        if 'bio' in data:
            player.bio = data['bio']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated',
            'data': riftwalker_schema.dump(player)
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Profile update failed: {str(e)}'
        }), 500


@auth_bp.route('/session', methods=['POST'])
@jwt_required()
def create_session():
    """
    Create player session (client tracking)
    
    Headers:
    Authorization: Bearer {access_token}
    
    Request Body:
    {
        "device_info": "string (optional)",
        "ip_address": "string (optional)"
    }
    
    Response:
    {
        "success": bool,
        "session_id": "uuid",
        "expires_in": int
    }
    """
    try:
        player_id = get_jwt_identity()
        
        # TODO: Create session record
        # session = PlayerSession(
        #     player_id=player_id,
        #     device_info=request.get_json().get('device_info'),
        #     ip_address=request.remote_addr
        # )
        # db.session.add(session)
        # db.session.commit()
        
        return jsonify({
            'success': True,
            'session_id': str(uuid.uuid4()),
            'expires_in': 86400  # 24 hours
        }), 201
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Session creation failed: {str(e)}'
        }), 500


# ============================================================================
# ADMIN AUTHENTICATION ENDPOINTS
# ============================================================================

@auth_bp.route('/admin/login', methods=['POST'])
@rate_limit(limit=5, window=600)
@validate_json
def admin_login():
    """
    Admin authentication endpoint
    
    Request Body:
    {
        "username": "string",
        "password": "string"
    }
    
    Response:
    {
        "success": bool,
        "tokens": {
            "access_token": "JWT",
            "refresh_token": "JWT"
        }
    }
    """
    try:
        data = request.get_json()
        
        player = Riftwalker.query.filter_by(username=data.get('username')).first()
        
        if not player or not player.is_admin or not check_password_hash(player.password_hash, data.get('password', '')):
            return jsonify({
                'success': False,
                'message': 'Invalid credentials or insufficient permissions'
            }), 401
        
        access_token = create_access_token(identity=str(player.id))
        refresh_token = create_refresh_token(identity=str(player.id))
        
        return jsonify({
            'success': True,
            'message': 'Admin login successful',
            'tokens': {
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Admin login failed: {str(e)}'
        }), 500
