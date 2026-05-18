from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentationCreate(BaseModel):
    title: str
    domain: str
    description: str | None = None
    content_markdown: str | None = None
    example_interactive: str | None = None


class DocumentationUpdate(BaseModel):
    title: str | None = None
    domain: str | None = None
    description: str | None = None
    content_markdown: str | None = None
    example_interactive: str | None = None
    is_active: bool | None = None


class DocumentationOut(BaseModel):
    id: UUID
    title: str
    domain: str
    description: str | None = None
    content_markdown: str | None = None
    example_interactive: str | None = None
    created_by: UUID | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
