from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class GenericResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: T | None = None
