from typing import Any

from pydantic import BaseModel, Field, model_validator


class ProductoCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    descripcion: str = ""
    precio: float = Field(gt=0)
    stock: int = Field(ge=0)
    categoria: str = "General"
    imagen_url: str | None = None


class ProductoUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=120)
    descripcion: str | None = None
    precio: float | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    categoria: str | None = None
    imagen_url: str | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_null_required_fields(cls, values: Any) -> Any:
        if isinstance(values, dict):
            required_fields = {"nombre", "descripcion", "precio", "stock", "categoria"}
            null_fields = [field for field in required_fields if values.get(field, ...) is None]
            if null_fields:
                raise ValueError(f"These fields cannot be null: {', '.join(sorted(null_fields))}")
        return values


class ProductoOut(ProductoCreate):
    id: str