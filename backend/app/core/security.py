# ==================================================================
# SECURITY UTILITIES
# ==================================================================

from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

# Password hashing context (using bcrypt)
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Function (hash_password) to hash a plaintext password
def hash_password(password: str) -> str:
    return _pwd_context.hash(password)

# Function (verify_password) to verify a plaintext password against a hash
def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)

# Function (create_access_token) to create a JWT access token for a user ID
def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": user_id, "exp": expire},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

# Function (decode_access_token) to decode a JWT access token and return the user ID
def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
