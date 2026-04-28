# ==================================================================
# BASE MODELS
# ==================================================================

import re
from sqlalchemy.orm import DeclarativeBase

# Base class with automatic snake_case table naming
def _camel_to_snake(name: str) -> str:
    name = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name).lower()

# Base class for all models
class Base(DeclarativeBase):
    @classmethod
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "__tablename__") and cls.__name__ != "Base":
            cls.__tablename__ = _camel_to_snake(cls.__name__)
