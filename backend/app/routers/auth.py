# ==================================================================
# AUTHENTICATION ROUTES
# ==================================================================

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_player
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.artifact import Artifact
from app.models.catalog import Attribute
from app.models.player import PlayerAttribute, PlayerInventory, PlayerProfile, User
from app.models.relic import Relic
from app.constants import ORDINARY_CODES_ORDERED as _ORDINARY_CODES_ORDERED
from app.schemas.auth import (
    AvatarUpdateRequest,
    PasswordUpdateRequest,
    RegisterRequest,
    TimezoneUpdateRequest,
    TokenResponse,
    UsernameUpdateRequest,
)

# Router for authentication-related endpoints (registration, login)
router = APIRouter(prefix="/auth", tags=["auth"])

# Endpoint (POST /auth/register) for user registration
@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    # Guard unique email and username
    existing_email = await session.scalar(select(User).where(User.email == body.email))
    if existing_email:
        raise ConflictError("Email already registered")

    existing_username = await session.scalar(
        select(User).where(User.username == body.username)
    )
    if existing_username:
        raise ConflictError("Username already taken")

    # Create user
    user = User(
        email=body.email,
        username=body.username,
        password_hash=hash_password(body.password),
    )
    session.add(user)
    await session.flush()

    # Create player profile
    profile = PlayerProfile(user_id=user.id, timezone=body.timezone)
    session.add(profile)
    await session.flush()

    # Create artifact
    session.add(Artifact(player_id=profile.id))

    # Create one PlayerAttribute and one PlayerInventory row per S.P.E.C.I.A.L. attribute
    attributes = (await session.scalars(select(Attribute))).all()
    for attr in attributes:
        session.add(PlayerAttribute(player_id=profile.id, attribute_id=attr.id))
        session.add(PlayerInventory(player_id=profile.id, attribute_id=attr.id))

    # Create one Relic row per upgradeable attribute (ordinary + Luck)
    for code in (*_ORDINARY_CODES_ORDERED, "L"):
        session.add(Relic(player_id=profile.id, attribute_code=code, level=0, total_invested=0))

    try:
        await session.commit()
    except IntegrityError:
        raise ConflictError("Email or username already registered")

    return TokenResponse(access_token=create_access_token(str(user.id)))

# Endpoint (POST /auth/login) for user login
@router.post("/login", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user = await session.scalar(select(User).where(User.email == form.username))
    if not user or not verify_password(form.password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")

    return TokenResponse(access_token=create_access_token(str(user.id)))

# Endpoint (PATCH /auth/timezone) update player timezone after login
@router.patch("/timezone", status_code=204)
async def update_timezone(
    body: TimezoneUpdateRequest,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> None:
    player.timezone = body.timezone
    await session.commit()

# Endpoint (PATCH /auth/username) update username — requires password confirmation
@router.patch("/username", status_code=204)
async def update_username(
    body: UsernameUpdateRequest,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> None:
    user = await session.get(User, player.user_id)
    if not user or not verify_password(body.password, user.password_hash):
        raise UnauthorizedError("Incorrect password")
    existing = await session.scalar(select(User).where(User.username == body.new_username))
    if existing:
        raise ConflictError("Username already taken")
    user.username = body.new_username
    await session.commit()

# Endpoint (PATCH /auth/password) update password — requires current password
@router.patch("/password", status_code=204)
async def update_password(
    body: PasswordUpdateRequest,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> None:
    user = await session.get(User, player.user_id)
    if not user or not verify_password(body.current_password, user.password_hash):
        raise UnauthorizedError("Incorrect current password")
    user.password_hash = hash_password(body.new_password)
    await session.commit()

# Endpoint (PATCH /auth/avatar) update avatar color and icon
@router.patch("/avatar", status_code=204)
async def update_avatar(
    body: AvatarUpdateRequest,
    player: PlayerProfile = Depends(get_current_player),
    session: AsyncSession = Depends(get_db),
) -> None:
    player.avatar_color = body.avatar_color
    player.avatar_icon = body.avatar_icon
    await session.commit()
