from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

ObjectIdStr = Annotated[str, BeforeValidator(str)]


class ProductoBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str = ""
    precio: float = Field(gt=0)
    stock: int = Field(ge=0)
    categoria: str


class ProductoCreate(ProductoBase):
    pass


class Producto(ProductoBase):
    model_config = ConfigDict(populate_by_name=True)

    id: ObjectIdStr = Field(alias="_id")
