
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import create_access_token
from app.models.usuario import Token
from app.services import usuarios as svc

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends()):
    user = svc.autenticar(form.username, form.password)
    token = create_access_token(user["email"], user["rol"])
    return {"access_token": token, "token_type": "bearer", "usuario": svc.to_out(user)}