from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.database import get_db
from app.models.player import PlayerProfile, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_player(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
) -> PlayerProfile:
    user_id = decode_access_token(token)
    if not user_id:
        raise UnauthorizedError()

    result = await session.execute(
        select(PlayerProfile)
        .join(User, User.id == PlayerProfile.user_id)
        .where(User.id == user_id, User.is_active.is_(True))
    )
    player = result.scalar_one_or_none()
    if not player:
        raise UnauthorizedError()

    return player
