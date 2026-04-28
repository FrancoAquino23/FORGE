from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.activity import PlayerConsumable
from app.models.artifact import Artifact
from app.models.catalog import Attribute, ConsumableType
from app.models.player import PlayerAttribute, PlayerInventory, PlayerProfile, User
from app.schemas.auth import RegisterRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    # Guard: unique email and username
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
    profile = PlayerProfile(user_id=user.id)
    session.add(profile)
    await session.flush()

    # Create artifact (empty next_forge_cost — computed on first forge attempt)
    session.add(Artifact(player_id=profile.id))

    # Create one PlayerAttribute and one PlayerInventory row per S.P.E.C.I.A.L. attribute
    attributes = (await session.scalars(select(Attribute))).all()
    for attr in attributes:
        session.add(PlayerAttribute(player_id=profile.id, attribute_id=attr.id))
        session.add(PlayerInventory(player_id=profile.id, attribute_id=attr.id))

    # Create consumable slots so the player can receive potions/chips
    consumable_types = (await session.scalars(select(ConsumableType))).all()
    for ct in consumable_types:
        session.add(PlayerConsumable(player_id=profile.id, consumable_type_id=ct.id))

    await session.commit()

    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.post("/login", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """OAuth2 password flow — use email in the `username` field."""
    user = await session.scalar(select(User).where(User.email == form.username))
    if not user or not verify_password(form.password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")

    return TokenResponse(access_token=create_access_token(str(user.id)))
