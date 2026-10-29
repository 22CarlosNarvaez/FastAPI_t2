from fastapi import APIRouter, Depends, status

from app.core.deps import require_admin
from app.models.producto import ProductoCreate, ProductoOut, ProductoUpdate
from app.services import productos as svc

router = APIRouter(prefix="/productos", tags=["Productos"])


@router.get("", response_model=list[ProductoOut])
def listar():
    return svc.listar()


@router.get("/{producto_id}", response_model=ProductoOut)
def obtener(producto_id: str):
    return svc.obtener(producto_id)


@router.post("", response_model=ProductoOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_admin)])
def crear(data: ProductoCreate):
    return svc.crear(data)


@router.put("/{producto_id}", response_model=ProductoOut, dependencies=[Depends(require_admin)])
def actualizar(producto_id: str, data: ProductoUpdate):
    return svc.actualizar(producto_id, data)


@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_admin)])
def eliminar(producto_id: str):
    svc.eliminar(producto_id)