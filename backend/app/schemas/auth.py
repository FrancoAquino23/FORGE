# ==================================================================
# AUTHENTICATION SCHEMAS 
# ==================================================================

from pydantic import BaseModel, EmailStr, Field, field_validator

# Model RegisterRequest (User Registration)
class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=8, max_length=128)
    timezone: str = Field(default="UTC", max_length=64)

# Model TokenResponse (Authentication Response)
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Model TimezoneUpdateRequest (Timezone Update)
class TimezoneUpdateRequest(BaseModel):
    timezone: str = Field(default="UTC", max_length=64)

# Model UsernameUpdateRequest (Username Update)
class UsernameUpdateRequest(BaseModel):
    new_username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=1, max_length=128)

# Model PasswordUpdateRequest (Password Update)
class PasswordUpdateRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

# Model AvatarUpdateRequest (Avatar Update)
class AvatarUpdateRequest(BaseModel):
    avatar_color: str | None = Field(default=None, max_length=16)
    avatar_icon: str | None = Field(default=None, max_length=64)
