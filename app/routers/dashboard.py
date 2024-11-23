from fastapi import APIRouter, Depends, FastAPI, HTTPException, Path
from .auth import get_current_user
from jose import jwt
from starlette import status
import time

router = APIRouter(
    prefix="/dashboard",
    tags=['dashboard']
)

METABASE_SITE_URL = "http://adap-r2-production.up.railway.app"
METABASE_SECRET_KEY = "0755b60bcd5edf45fd20aa39a158fdc8bd3ccda35bb7909413f9cac3aee5d79a"
 
def generate_iframe_url(company):
   
    payload = {
        "resource": {"dashboard": 6},
        "params": {
            "texto": company  # Añadir el ID de la empresa
        },
        "exp": round(time.time()) + (60 * 10)  # Expira en 10 minutos
    }
    # Generar el token
    token = jwt.encode(payload, METABASE_SECRET_KEY, algorithm="HS256")
 
    # Crear la URL del iframe
    iframeUrl = f"{METABASE_SITE_URL}/embed/dashboard/{token}#bordered=true&titled=true&texto={company}"
    return iframeUrl
 

@router.post('/get_dashboard', status_code=status.HTTP_200_OK)
async def get_dashboard(user: dict = Depends(get_current_user)):
    """
    Endpoint para obtener el dashboard de la compañía.
    """
    if user.get('user_type') == 'company':
        company_id = user.get('username')

        iframe_url = generate_iframe_url(company_id)
        return {"iframe_url": iframe_url}
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized user")