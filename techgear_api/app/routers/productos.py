from fastapi import APIRouter, HTTPException, status

from app.models.producto import Producto, ProductoCreate
from app.services import productos as servicio

router = APIRouter(prefix="/productos", tags=["productos"])


@router.post("/", response_model=Producto, status_code=status.HTTP_201_CREATED)
async def crear_producto(datos: ProductoCreate):
    return await servicio.crear(datos)


@router.get("/", response_model=list[Producto])
async def listar_productos():
    return await servicio.listar()


@router.get("/{producto_id}", response_model=Producto)
async def obtener_producto(producto_id: str):
    producto = await servicio.obtener(producto_id)
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


@router.put("/{producto_id}", response_model=Producto)
async def actualizar_producto(producto_id: str, datos: ProductoCreate):
    producto = await servicio.actualizar(producto_id, datos)
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_producto(producto_id: str):
    if not await servicio.eliminar(producto_id):
        raise HTTPException(status_code=404, detail="Producto no encontrado")