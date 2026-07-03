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
