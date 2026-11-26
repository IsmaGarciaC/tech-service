from typing import Annotated

from fastapi import Depends
from pydantic import Field
from sqlalchemy.orm import Session

from app.core.database import get_db

BIGINT_MAX = 2**63 - 1
PositiveId = Annotated[int, Field(ge=1, le=BIGINT_MAX)]
Limit = Annotated[int, Field(ge=1, le=100)]
Offset = Annotated[int, Field(ge=0, le=BIGINT_MAX)]
Database = Annotated[Session, Depends(get_db)]
