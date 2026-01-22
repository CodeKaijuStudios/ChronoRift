"""
ChronoRift Authentication Service
JWT token management, refresh token rotation, and session handling
"""

import jwt
import os
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field
from enum import Enum


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class TokenType(Enum):
    """JWT token types"""
    ACCESS = "access"           # Short-lived, used for API requests
    REFRESH = "refresh"         # Long-lived, used to get new access token
    SESSION = "session"         # Session token


class TokenStatus(Enum):
    """Token lifecycle status"""
    VALID = "valid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    INVALID = "invalid"
    REUSE_DETECTED = "reuse_detected"


# Token lifetimes
ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)      # 15 minute access tokens
REFRESH_TOKEN_LIFETIME = timedelta(days=7)         # 7 day refresh tokens
SESSION_TOKEN_LIFETIME = timedelta(hours=24)       # 24 hour session tokens

# Token configuration
TOKEN_ALGORITHM = "HS256"                          # HMAC-SHA256
TOKEN_AUDIENCE = "chronorift-game"
TOKEN_ISSUER = "chronorift-auth-server"
GRACE_PERIOD = timedelta(seconds=30)               # Grace period for race conditions

# Security thresholds
MAX_REFRESH_ATTEMPTS = 100                         # Max rotations per refresh token family
MAX_FAILED_LOGIN_ATTEMPTS = 5                      # Max failed logins before lockout
LOGIN_ATTEMPT_WINDOW = timedelta(minutes=15)       # Time window for failed attempts


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class TokenPayload:
    """JWT token payload structure"""
    user_id: str
    username: str
    email: str
    token_type: TokenType
    issued_at: datetime
    expires_at: datetime
    jti: str                          # JWT ID (unique token identifier)
    scopes: List[str] = field(default_factory=list)  # Permission scopes
    character_id: Optional[str] = None
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    token_family: Optional[str] = None  # For tracking token rotation lineage


@dataclass
class TokenPair:
    """Access and refresh token pair"""
    access_token: str
    refresh_token: str
    access_token_expires_in: int  # seconds
    refresh_token_expires_in: int  # seconds
    token_type: str = "Bearer"


@dataclass
class RefreshTokenRecord:
    """Stored refresh token metadata"""
    jti: str                           # Token ID
    user_id: str
    token_family: str                  # Lineage tracking
    created_at: datetime
    expires_at: datetime
    last_used_at: Optional[datetime] = None
    is_revoked: bool = False
    rotation_count: int = 0            # Times rotated
    parent_token_jti: Optional[str] = None  # Previous token in rotation chain
    device_id: Optional[str] = None
    ip_address: Optional[str] = None


@dataclass
class UserSession:
    """Active user session"""
    user_id: str
    username: str
    email: str
    character_id: Optional[str]
    login_timestamp: datetime
    last_activity: datetime
    device_id: str
    ip_address: str
    token_family: str
    is_active: bool = True
    logout_timestamp: Optional[datetime] = None


@dataclass
class LoginAttempt:
    """Failed login tracking"""
    username: str
    ip_address: str
    attempt_timestamp: datetime
    success: bool = False
    reason: str = ""


# ============================================================================
# AUTHENTICATION SERVICE
# ============================================================================

class AuthenticationService:
    """JWT authentication and token management"""
    
    def __init__(self, secret_key: str):
        """
        Initialize authentication service
        
        Args:
            secret_key: Secret key for signing tokens (should be env variable)
        """
        self.secret_key = secret_key
        # In production, these would be database tables
        self.refresh_token_store: Dict[str, RefreshTokenRecord] = {}
        self.token_blacklist: set = set()  # Revoked tokens
        self.sessions: Dict[str, UserSession] = {}
        self.login_attempts: List[LoginAttempt] = []
    
    
    @staticmethod
    def generate_jti() -> str:
        """Generate unique JWT ID"""
        timestamp = datetime.utcnow().isoformat()
        random_data = os.urandom(16).hex()
        jti = hashlib.sha256(f"{timestamp}{random_data}".encode()).hexdigest()
        return jti[:32]  # Use first 32 chars
    
    
    @staticmethod
    def generate_token_family() -> str:
        """Generate token family ID for rotation tracking"""
        return hashlib.sha256(os.urandom(32)).hexdigest()[:16]
    
    
    def create_token_pair(
        self,
        user_id: str,
        username: str,
        email: str,
        character_id: Optional[str] = None,
        device_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        token_family: Optional[str] = None,
    ) -> TokenPair:
        """
        Create new access and refresh token pair
        
        Args:
            user_id: User's unique ID
            username: Username
            email: User's email
            character_id: Associated character ID
            device_id: Device identifier
            ip_address: Client IP address
            scopes: Permission scopes
            token_family: Existing token family for rotation (None = new)
            
        Returns:
            TokenPair: Access and refresh tokens
        """
        if token_family is None:
            token_family = self.generate_token_family()
        
        now = datetime.now(timezone.utc)
        
        # Create access token
        access_jti = self.generate_jti()
        access_payload = TokenPayload(
            user_id=user_id,
            username=username,
            email=email,
            token_type=TokenType.ACCESS,
            issued_at=now,
            expires_at=now + ACCESS_TOKEN_LIFETIME,
            jti=access_jti,
            scopes=scopes or ["play", "chat"],
            character_id=character_id,
            device_id=device_id,
            ip_address=ip_address,
            token_family=token_family,
        )
        
        access_token = self._encode_token(access_payload)
        
        # Create refresh token
        refresh_jti = self.generate_jti()
        refresh_payload = TokenPayload(
            user_id=user_id,
            username=username,
            email=email,
            token_type=TokenType.REFRESH,
            issued_at=now,
            expires_at=now + REFRESH_TOKEN_LIFETIME,
            jti=refresh_jti,
            scopes=[],
            character_id=character_id,
            device_id=device_id,
            ip_address=ip_address,
            token_family=token_family,
        )
        
        refresh_token = self._encode_token(refresh_payload)
        
        # Store refresh token metadata
        self.refresh_token_store[refresh_jti] = RefreshTokenRecord(
            jti=refresh_jti,
            user_id=user_id,
            token_family=token_family,
            created_at=now,
            expires_at=now + REFRESH_TOKEN_LIFETIME,
            device_id=device_id,
            ip_address=ip_address,
        )
        
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expires_in=int(ACCESS_TOKEN_LIFETIME.total_seconds()),
            refresh_token_expires_in=int(REFRESH_TOKEN_LIFETIME.total_seconds()),
        )
    
    
    def refresh_access_token(
        self,
        refresh_token: str,
        device_id: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Optional[TokenPair]:
        """
        Refresh access token using refresh token (with rotation)
        
        Args:
            refresh_token: Current refresh token
            device_id: Device identifier for security check
            ip_address: Client IP for security check
            
        Returns:
            TokenPair: New token pair, or None if invalid
        """
        # Decode and validate refresh token
        payload = self.verify_token(refresh_token, TokenType.REFRESH)
        if payload is None:
            return None
        
        # Verify token exists and hasn't been used
        token_record = self.refresh_token_store.get(payload.jti)
        if token_record is None:
            return None
        
        # Check for reuse (security threat)
        if token_record.last_used_at is not None:
            # Token was already used - potential attack
            self._revoke_token_family(payload.token_family)
            return None
        
        # Validate device/IP if provided (optional security enhancement)
        if device_id and token_record.device_id != device_id:
            self._revoke_token_family(payload.token_family)
            return None
        
        # Check rotation limit
        if token_record.rotation_count >= MAX_REFRESH_ATTEMPTS:
            self._revoke_token_family(payload.token_family)
            return None
        
        # Revoke old refresh token
        now = datetime.now(timezone.utc)
        token_record.is_revoked = True
        token_record.last_used_at = now
        
        # Create new token pair (with rotation)
        new_pair = self.create_token_pair(
            user_id=payload.user_id,
            username=payload.username,
            email=payload.email,
            character_id=payload.character_id,
            device_id=device_id or token_record.device_id,
            ip_address=ip_address or token_record.ip_address,
            token_family=payload.token_family,  # Same family
        )
        
        # Update rotation count
        new_record = self.refresh_token_store[new_pair.refresh_token.split('.')[-1][:32]]
        new_record.rotation_count = token_record.rotation_count + 1
        new_record.parent_token_jti = payload.jti
        
        return new_pair
    
    
    def verify_token(
        self,
        token: str,
        expected_type: Optional[TokenType] = None
    ) -> Optional[TokenPayload]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token string
            expected_type: Expected token type (None = any)
            
        Returns:
            TokenPayload: Decoded payload, or None if invalid
        """
        try:
            decoded = jwt.decode(
                token,
                self.secret_key,
                algorithms=[TOKEN_ALGORITHM],
                audience=TOKEN_AUDIENCE,
                issuer=TOKEN_ISSUER,
            )
            
            # Check if token is revoked
            if decoded.get('jti') in self.token_blacklist:
                return None
            
            # Check expiration with grace period
            exp = datetime.fromtimestamp(decoded['exp'], tz=timezone.utc)
            if datetime.now(timezone.utc) > exp + GRACE_PERIOD:
                return None
            
            # Verify type if specified
            if expected_type and TokenType(decoded['token_type']) != expected_type:
                return None
            
            return TokenPayload(
                user_id=decoded['user_id'],
                username=decoded['username'],
                email=decoded['email'],
                token_type=TokenType(decoded['token_type']),
                issued_at=datetime.fromtimestamp(decoded['iat'], tz=timezone.utc),
                expires_at=datetime.fromtimestamp(decoded['exp'], tz=timezone.utc),
                jti=decoded['jti'],
                scopes=decoded.get('scopes', []),
                character_id=decoded.get('character_id'),
                device_id=decoded.get('device_id'),
                ip_address=decoded.get('ip_address'),
                token_family=decoded.get('token_family'),
            )
        
        except jwt.InvalidTokenError:
            return None
    
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token (add to blacklist)
        
        Args:
            token: Token to revoke
            
        Returns:
            bool: Success
        """
        payload = self.verify_token(token)
        if payload is None:
            return False
        
        self.token_blacklist.add(payload.jti)
        return True
    
    
    def _revoke_token_family(self, token_family: Optional[str]) -> None:
        """Revoke entire token family (all related refresh tokens)"""
        if token_family is None:
            return
        
        for record in self.refresh_token_store.values():
            if record.token_family == token_family:
                record.is_revoked = True
    
    
    def _encode_token(self, payload: TokenPayload) -> str:
        """Encode token payload to JWT string"""
        now = datetime.now(timezone.utc)
        
        claims = {
            'user_id': payload.user_id,
            'username': payload.username,
            'email': payload.email,
            'token_type': payload.token_type.value,
            'jti': payload.jti,
            'iat': now.timestamp(),
            'exp': payload.expires_at.timestamp(),
            'aud': TOKEN_AUDIENCE,
            'iss': TOKEN_ISSUER,
        }
        
        if payload.scopes:
            claims['scopes'] = payload.scopes
        if payload.character_id:
            claims['character_id'] = payload.character_id
        if payload.device_id:
            claims['device_id'] = payload.device_id
        if payload.ip_address:
            claims['ip_address'] = payload.ip_address
        if payload.token_family:
            claims['token_family'] = payload.token_family
        
        return jwt.encode(claims, self.secret_key, algorithm=TOKEN_ALGORITHM)
    
    
    def create_session(
        self,
        user_id: str,
        username: str,
        email: str,
        character_id: Optional[str],
        device_id: str,
        ip_address: str,
        token_family: str,
    ) -> UserSession:
        """
        Create new user session
        
        Args:
            user_id: User ID
            username: Username
            email: Email
            character_id: Character ID
            device_id: Device identifier
            ip_address: IP address
            token_family: Token family ID
            
        Returns:
            UserSession: New session
        """
        session = UserSession(
            user_id=user_id,
            username=username,
            email=email,
            character_id=character_id,
            login_timestamp=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            device_id=device_id,
            ip_address=ip_address,
            token_family=token_family,
        )
        
        self.sessions[f"{user_id}:{device_id}"] = session
        return session
    
    
    def get_session(self, user_id: str, device_id: str) -> Optional[UserSession]:
        """Get active session"""
        return self.sessions.get(f"{user_id}:{device_id}")
    
    
    def logout(self, user_id: str, device_id: str) -> bool:
        """
        Logout user session
        
        Args:
            user_id: User ID
            device_id: Device ID
            
        Returns:
            bool: Success
        """
        session = self.get_session(user_id, device_id)
        if session:
            session.is_active = False
            session.logout_timestamp = datetime.utcnow()
            return True
        return False
    
    
    def record_login_attempt(
        self,
        username: str,
        ip_address: str,
        success: bool,
        reason: str = ""
    ) -> None:
        """Record login attempt for security monitoring"""
        attempt = LoginAttempt(
            username=username,
            ip_address=ip_address,
            attempt_timestamp=datetime.utcnow(),
            success=success,
            reason=reason,
        )
        self.login_attempts.append(attempt)
        
        # Keep only recent 1000 attempts
        if len(self.login_attempts) > 1000:
            self.login_attempts = self.login_attempts[-1000:]
    
    
    def is_account_locked(self, username: str, ip_address: str) -> bool:
        """Check if account is locked due to failed login attempts"""
        now = datetime.utcnow()
        failed_attempts = [
            a for a in self.login_attempts
            if (a.username == username or a.ip_address == ip_address)
            and not a.success
            and (now - a.attempt_timestamp) < LOGIN_ATTEMPT_WINDOW
        ]
        
        return len(failed_attempts) >= MAX_FAILED_LOGIN_ATTEMPTS


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_token_status(token: str, auth_service: AuthenticationService) -> TokenStatus:
    """
    Get comprehensive token status
    
    Args:
        token: Token to check
        auth_service: Authentication service instance
        
    Returns:
        TokenStatus: Current status
    """
    payload = auth_service.verify_token(token)
    
    if payload is None:
        # Check if it's in blacklist
        try:
            decoded = jwt.decode(
                token,
                auth_service.secret_key,
                algorithms=[TOKEN_ALGORITHM],
                options={"verify_signature": False}
            )
            if decoded.get('jti') in auth_service.token_blacklist:
                return TokenStatus.REVOKED
        except:
            pass
        
        return TokenStatus.INVALID
    
    return TokenStatus.VALID


def extract_claims(token: str, secret_key: str) -> Optional[Dict]:
    """Extract all claims from token without verification (unsafe, debug only)"""
    try:
        return jwt.decode(
            token,
            secret_key,
            algorithms=[TOKEN_ALGORITHM],
        )
    except:
        return None
