from fastapi import FastAPI, HTTPException, Depends, status, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator, ValidationError
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import logging
import jwt
import hashlib
import secrets
from contextlib import asynccontextmanager

from models import (
    Cliente, Promocion, Transaccion, Ticket,
    TipoCliente, TipoPromocion, TipoTicket, TipoTransaccion
)
from repository import DatabaseRepository
from services import ClienteService, PromocionService, TransaccionService, TicketService, ReporteService
from config import DatabaseConfig, SecurityConfig, APIConfig, ApplicationConfig, CasinoConfig

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Modelos Pydantic para la API
class ClienteCreate(BaseModel):
    numero_documento: str = Field(..., min_length=6, max_length=12)
    tipo_documento: str = Field(default="CC", pattern="^(CC|CE|PP)$")
    nombres: str = Field(..., min_length=2, max_length=100)
    apellidos: str = Field(..., min_length=2, max_length=100)
    email: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    telefono: Optional[str] = Field(None, min_length=7, max_length=15)
    fecha_nacimiento: Optional[date] = None
    direccion: Optional[str] = Field(None, max_length=255)
    ciudad: Optional[str] = Field(None, max_length=100)
    
    @validator('fecha_nacimiento')
    def validar_edad_minima(cls, v):
        if v and v > date.today() - timedelta(days=18*365):
            raise ValueError('El cliente debe ser mayor de 18 años')
        return v

class ClienteUpdate(BaseModel):
    nombres: Optional[str] = Field(None, min_length=2, max_length=100)
    apellidos: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    telefono: Optional[str] = Field(None, min_length=7, max_length=15)
    direccion: Optional[str] = Field(None, max_length=255)
    ciudad: Optional[str] = Field(None, max_length=100)
    activo: Optional[bool] = None
    notas: Optional[str] = Field(None, max_length=1000)

class PromocionCreate(BaseModel):
    titulo: str = Field(..., min_length=5, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=1000)
    tipo: str = Field(..., pattern="^(descuento|puntos_bonus|bebida_gratis|entrada_gratis|cashback|torneo_especial)$")
    valor: float = Field(..., ge=0)
    fecha_inicio: datetime
    fecha_fin: datetime
    cliente_id: Optional[int] = None
    usos_maximos: int = Field(default=1, ge=1)
    condiciones: Optional[str] = Field(None, max_length=1000)
    
    @validator('fecha_fin')
    def validar_fechas(cls, v, values):
        if 'fecha_inicio' in values and v <= values['fecha_inicio']:
            raise ValueError('La fecha de fin debe ser posterior a la fecha de inicio')
        return v

class TransaccionCreate(BaseModel):
    cliente_id: int = Field(..., gt=0)
    tipo: str = Field(..., pattern="^(ingreso|juego|consumo|canje_promocion|retiro)$")
    monto: float = Field(..., ne=0)  # No puede ser 0, pero permite negativos
    descripcion: Optional[str] = Field(None, max_length=255)
    ubicacion: Optional[str] = Field(None, max_length=100)
    promocion_id: Optional[int] = None
    metodo_pago: Optional[str] = Field(None, max_length=50)
    numero_referencia: Optional[str] = Field(None, max_length=100)
    empleado_id: Optional[int] = None
    notas: Optional[str] = Field(None, max_length=500)

class TicketCreate(BaseModel):
    cliente_id: int = Field(..., gt=0)
    tipo: str = Field(..., pattern="^(queja|sugerencia|consulta|reclamo|soporte_tecnico)$")
    prioridad: str = Field(default="MEDIA", pattern="^(BAJA|MEDIA|ALTA|CRITICA)$")
    asunto: str = Field(..., min_length=5, max_length=255)
    descripcion: str = Field(..., min_length=10, max_length=2000)
    categoria: Optional[str] = Field(None, max_length=100)
    subcategoria: Optional[str] = Field(None, max_length=100)

class TicketUpdate(BaseModel):
    estado: Optional[str] = Field(None, pattern="^(abierto|en_proceso|resuelto|cerrado|escalado)$")
    asignado_a: Optional[str] = Field(None, max_length=100)
    resolucion: Optional[str] = Field(None, max_length=2000)
    satisfaccion_cliente: Optional[int] = Field(None, ge=1, le=5)

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class ClienteLoginRequest(BaseModel):
    numero_documento: str = Field(..., min_length=6, max_length=12)

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# Configuración global
db_config = DatabaseConfig()
security_config = SecurityConfig()
api_config = APIConfig()
app_config = ApplicationConfig()
casino_config = CasinoConfig()

# Inicialización de servicios
repository = DatabaseRepository(db_config)
cliente_service = ClienteService(repository, casino_config)
promocion_service = PromocionService(repository)
transaccion_service = TransaccionService(repository, casino_config)
ticket_service = TicketService(repository)
reporte_service = ReporteService(repository)

# Configuración de seguridad
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Iniciando API del Casino Atlantic City")
    try:
        # Probar conexión a base de datos
        if repository.test_connection():
            logger.info("Conexión a base de datos exitosa")
            # Inicializar tablas si es necesario
            repository.initialize_database()
        else:
            logger.error("Error de conexión a base de datos")
    except Exception as e:
        logger.error(f"Error durante el startup: {e}")
    
    yield
    
    # Shutdown
    logger.info("Cerrando API del Casino Atlantic City")

# Crear aplicación FastAPI
app = FastAPI(
    title="Casino Atlantic City - API de Gestión de Clientes",
    description="API REST para el sistema unificado de gestión de clientes del Casino Atlantic City",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware de seguridad
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes para desarrollo
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1"]
)

# Funciones de autenticación
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=security_config.JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, security_config.SECRET_KEY, algorithm=security_config.JWT_ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, security_config.SECRET_KEY, algorithms=[security_config.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

def hash_password(password: str) -> str:
    return hashlib.sha256((password + security_config.SECRET_KEY).encode()).hexdigest()

# Middleware para logging de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    
    response = await call_next(request)
    
    process_time = (datetime.now() - start_time).total_seconds()
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response

# Configuración de archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Ruta raíz que sirve la página principal
@app.get("/")
async def read_root():
    """Servir la página principal del casino"""
    return FileResponse('static/index.html')

# Ruta para servir la página de cliente
@app.get("/cliente.html")
async def read_cliente():
    """Servir la página del portal de cliente"""
    return FileResponse('static/cliente.html')

# Endpoints de autenticación
@app.post("/auth/login", response_model=APIResponse)
async def login(login_data: LoginRequest):
    """Autenticación de usuarios administrativos"""
    try:
        # Validar credenciales (implementar con base de datos real)
        hashed_password = hash_password(login_data.password)
        
        # Por ahora, usuario demo
        if login_data.username == "admin" and login_data.password == "admin123":
            access_token = create_access_token(data={"sub": login_data.username, "type": "admin"})
            return APIResponse(
                success=True,
                message="Login exitoso",
                data={
                    "access_token": access_token,
                    "token_type": "bearer",
                    "expires_in": security_config.JWT_EXPIRATION_HOURS * 3600,
                    "user_type": "admin"
                }
            )
        else:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.post("/auth/cliente-login", response_model=APIResponse)
async def cliente_login(request: ClienteLoginRequest):
    """Autenticación de clientes usando solo número de documento"""
    try:
        # Buscar cliente por número de documento
        cliente = repository.obtener_cliente_por_documento(request.numero_documento)
        
        if cliente and cliente.activo:
            # Registrar la visita del cliente (actualiza fecha_ultima_visita)
            cliente_service.registrar_visita(cliente.id, 0.0)
            logger.info(f"Visita registrada para cliente {cliente.id} - {cliente.nombre_completo}")
            
            # Crear token para el cliente
            access_token = create_access_token(data={
                "sub": str(cliente.id),
                "documento": request.numero_documento,
                "type": "cliente"
            })
            
            return APIResponse(
                success=True,
                message=f"Bienvenido {cliente.nombre_completo}",
                data={
                    "access_token": access_token,
                    "token_type": "bearer",
                    "expires_in": security_config.JWT_EXPIRATION_HOURS * 3600,
                    "user_type": "cliente",
                    "cliente": {
                        "id": cliente.id,
                        "nombre_completo": cliente.nombre_completo,
                        "numero_documento": cliente.numero_documento,
                        "tipo_cliente": cliente.tipo_cliente.value,
                        "saldo": cliente.saldo,
                        "puntos_acumulados": cliente.puntos_acumulados
                    }
                }
            )
        else:
            raise HTTPException(status_code=401, detail="Cliente no encontrado o inactivo")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login de cliente: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# Endpoints de clientes
@app.post("/clientes", response_model=APIResponse)
async def crear_cliente(cliente_data: ClienteCreate, current_user: str = Depends(verify_token)):
    """Crear un nuevo cliente (requiere autenticación)"""
    try:
        success, message, cliente_id = cliente_service.registrar_cliente(cliente_data.dict())
        
        if success:
            return APIResponse(
                success=True,
                message=message,
                data={"cliente_id": cliente_id}
            )
        else:
            raise HTTPException(status_code=400, detail=message)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear cliente: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.post("/registro", response_model=APIResponse)
async def registro_publico_cliente(cliente_data: ClienteCreate):
    """Registro público de clientes (sin autenticación requerida)"""
    try:
        logger.info(f"Intento de registro con datos: {cliente_data.dict()}")
        
        # Validaciones adicionales para registro público
        if not cliente_data.numero_documento or len(cliente_data.numero_documento) < 6:
            logger.error(f"Número de documento inválido: {cliente_data.numero_documento}")
            raise HTTPException(status_code=400, detail="Número de documento inválido")
        
        if not cliente_data.nombres or not cliente_data.apellidos:
            logger.error(f"Nombres o apellidos faltantes: nombres={cliente_data.nombres}, apellidos={cliente_data.apellidos}")
            raise HTTPException(status_code=400, detail="Nombres y apellidos son obligatorios")
        
        # Verificar si el cliente ya existe
        cliente_existente = repository.obtener_cliente_por_documento(cliente_data.numero_documento)
        if cliente_existente:
            logger.error(f"Cliente ya existe con documento: {cliente_data.numero_documento}")
            raise HTTPException(status_code=400, detail="Ya existe un cliente con este número de documento")
        
        success, message, cliente_id = cliente_service.registrar_cliente(cliente_data.dict())
        
        if success:
            logger.info(f"Nuevo cliente registrado públicamente: ID {cliente_id}, Documento: {cliente_data.numero_documento}")
            return APIResponse(
                success=True,
                message="¡Registro exitoso! Bienvenido al Casino Atlantic City",
                data={
                    "cliente_id": cliente_id,
                    "numero_documento": cliente_data.numero_documento,
                    "nombre_completo": f"{cliente_data.nombres} {cliente_data.apellidos}"
                }
            )
        else:
            logger.error(f"Error en cliente_service.registrar_cliente: {message}")
            raise HTTPException(status_code=400, detail=message)
    
    except HTTPException:
        raise
    except ValidationError as ve:
        logger.error(f"Error de validación en registro: {ve}")
        raise HTTPException(status_code=400, detail=f"Error de validación: {str(ve)}")
    except Exception as e:
        logger.error(f"Error en registro público: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/clientes/{cliente_id}", response_model=APIResponse)
async def obtener_cliente(cliente_id: int, current_user: str = Depends(verify_token)):
    """Obtener información de un cliente"""
    try:
        cliente = repository.obtener_cliente(cliente_id)
        
        if cliente:
            cliente_data = {
                "id": cliente.id,
                "numero_documento": cliente.numero_documento,
                "tipo_documento": cliente.tipo_documento,
                "nombres": cliente.nombres,
                "apellidos": cliente.apellidos,
                "nombre_completo": cliente.nombre_completo,
                "email": cliente.email,
                "telefono": cliente.telefono,
                "fecha_nacimiento": cliente.fecha_nacimiento.isoformat() if cliente.fecha_nacimiento else None,
                "direccion": cliente.direccion,
                "ciudad": cliente.ciudad,
                "tipo_cliente": cliente.tipo_cliente.value,
                "fecha_registro": cliente.fecha_registro.isoformat(),
                "fecha_ultima_visita": cliente.fecha_ultima_visita.isoformat() if cliente.fecha_ultima_visita else None,
                "total_visitas": cliente.total_visitas,
                "total_gastado": cliente.total_gastado,
                "saldo": cliente.saldo,
                "puntos_acumulados": cliente.puntos_acumulados,
                "activo": cliente.activo,
                "edad": cliente.edad
            }
            
            return APIResponse(
                success=True,
                message="Cliente encontrado",
                data=cliente_data
            )
        else:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener cliente: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/clientes", response_model=APIResponse)
async def listar_clientes(
    activo: Optional[bool] = None,
    tipo_cliente: Optional[str] = None,
    ciudad: Optional[str] = None,
    limite: int = Query(default=100, le=1000),
    current_user: str = Depends(verify_token)
):
    """Listar clientes con filtros opcionales"""
    try:
        filtros = {}
        if activo is not None:
            filtros['activo'] = activo
        if tipo_cliente:
            filtros['tipo_cliente'] = tipo_cliente
        if ciudad:
            filtros['ciudad'] = ciudad
        
        clientes = repository.listar_clientes(filtros, limite)
        
        clientes_data = [{
            "id": c.id,
            "numero_documento": c.numero_documento,
            "nombres": c.nombres,
            "apellidos": c.apellidos,
            "nombre_completo": c.nombre_completo,
            "email": c.email,
            "tipo_cliente": c.tipo_cliente.value,
            "total_visitas": c.total_visitas,
            "total_gastado": c.total_gastado,
            "saldo": c.saldo,
            "puntos_acumulados": c.puntos_acumulados,
            "activo": c.activo
        } for c in clientes]
        
        return APIResponse(
            success=True,
            message=f"Se encontraron {len(clientes)} clientes",
            data=clientes_data
        )
    
    except Exception as e:
        logger.error(f"Error al listar clientes: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.put("/clientes/{cliente_id}", response_model=APIResponse)
async def actualizar_cliente(
    cliente_id: int,
    cliente_data: ClienteUpdate,
    current_user: str = Depends(verify_token)
):
    """Actualizar información de un cliente"""
    try:
        cliente = repository.obtener_cliente(cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        # Actualizar campos proporcionados
        update_data = cliente_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(cliente, field, value)
        
        success = repository.actualizar_cliente(cliente)
        
        if success:
            return APIResponse(
                success=True,
                message="Cliente actualizado exitosamente"
            )
        else:
            raise HTTPException(status_code=400, detail="Error al actualizar cliente")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar cliente: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# Endpoints de promociones
@app.post("/promociones", response_model=APIResponse)
async def crear_promocion(promocion_data: PromocionCreate, current_user: str = Depends(verify_token)):
    """Crear una nueva promoción"""
    try:
        success, message, promocion_id = promocion_service.crear_promocion_personalizada(promocion_data.dict())
        
        if success:
            return APIResponse(
                success=True,
                message=message,
                data={"promocion_id": promocion_id}
            )
        else:
            raise HTTPException(status_code=400, detail=message)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear promoción: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/promociones/activas", response_model=APIResponse)
async def obtener_promociones_activas(
    cliente_id: Optional[int] = None,
    current_user: str = Depends(verify_token)
):
    """Obtener promociones activas"""
    try:
        promociones = repository.obtener_promociones_activas(cliente_id)
        
        promociones_data = [{
            "id": p.id,
            "codigo": p.codigo,
            "titulo": p.titulo,
            "descripcion": p.descripcion,
            "tipo": p.tipo.value,
            "valor": p.valor,
            "fecha_inicio": p.fecha_inicio.isoformat(),
            "fecha_fin": p.fecha_fin.isoformat(),
            "usos_maximos": p.usos_maximos,
            "usos_actuales": p.usos_actuales,
            "puede_canjearse": p.puede_canjearse
        } for p in promociones]
        
        return APIResponse(
            success=True,
            message=f"Se encontraron {len(promociones)} promociones activas",
            data=promociones_data
        )
    
    except Exception as e:
        logger.error(f"Error al obtener promociones: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.post("/promociones/{codigo}/canjear", response_model=APIResponse)
async def canjear_promocion(
    codigo: str,
    cliente_id: int,
    current_user: str = Depends(verify_token)
):
    """Canjear una promoción"""
    try:
        success, message, beneficio = promocion_service.canjear_promocion(codigo, cliente_id)
        
        if success:
            return APIResponse(
                success=True,
                message=message,
                data=beneficio
            )
        else:
            raise HTTPException(status_code=400, detail=message)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al canjear promoción: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# Endpoints de transacciones
@app.post("/transacciones", response_model=APIResponse)
async def crear_transaccion(transaccion_data: TransaccionCreate, current_user: str = Depends(verify_token)):
    """Crear una nueva transacción"""
    try:
        success, message, transaccion_id = transaccion_service.procesar_transaccion(transaccion_data.dict())
        
        if success:
            return APIResponse(
                success=True,
                message=message,
                data={"transaccion_id": transaccion_id}
            )
        else:
            raise HTTPException(status_code=400, detail=message)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear transacción: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/transacciones", response_model=APIResponse)
async def obtener_todas_transacciones(
    limite: int = Query(default=100, le=500),
    current_user: str = Depends(verify_token)
):
    """Obtener todas las transacciones"""
    try:
        transacciones = repository.obtener_todas_transacciones(limite)
        
        transacciones_data = [{
            "id": t.id,
            "cliente_id": t.cliente_id,
            "tipo": t.tipo.value,
            "monto": t.monto,
            "descripcion": t.descripcion,
            "fecha_transaccion": t.fecha.isoformat(),
            "ubicacion": t.ubicacion,
            "puntos_ganados": t.puntos_ganados,
            "metodo_pago": t.metodo_pago
        } for t in transacciones]
        
        return APIResponse(
            success=True,
            message=f"Se encontraron {len(transacciones)} transacciones",
            data=transacciones_data
        )
    
    except Exception as e:
        logger.error(f"Error al obtener transacciones: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/transacciones/cliente/{cliente_id}", response_model=APIResponse)
async def obtener_transacciones_cliente(
    cliente_id: int,
    limite: int = Query(default=50, le=200),
    current_user: str = Depends(verify_token)
):
    """Obtener transacciones de un cliente"""
    try:
        transacciones = repository.obtener_transacciones_cliente(cliente_id, limite)
        
        transacciones_data = [{
            "id": t.id,
            "tipo": t.tipo.value,
            "monto": t.monto,
            "descripcion": t.descripcion,
            "fecha_transaccion": t.fecha.isoformat(),
            "ubicacion": t.ubicacion,
            "puntos_ganados": t.puntos_ganados,
            "metodo_pago": t.metodo_pago
        } for t in transacciones]
        
        return APIResponse(
            success=True,
            message=f"Se encontraron {len(transacciones)} transacciones",
            data=transacciones_data
        )
    
    except Exception as e:
        logger.error(f"Error al obtener transacciones: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# Endpoints de tickets
@app.post("/tickets", response_model=APIResponse)
async def crear_ticket(ticket_data: TicketCreate, current_user: str = Depends(verify_token)):
    """Crear un nuevo ticket de atención"""
    try:
        success, message, ticket_id = ticket_service.crear_ticket(ticket_data.dict())
        
        if success:
            return APIResponse(
                success=True,
                message=message,
                data={"ticket_id": ticket_id}
            )
        else:
            raise HTTPException(status_code=400, detail=message)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear ticket: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/tickets/abiertos", response_model=APIResponse)
async def obtener_tickets_abiertos(
    limite: int = Query(default=100, le=500),
    current_user: str = Depends(verify_token)
):
    """Obtener tickets abiertos"""
    try:
        tickets = repository.obtener_tickets_abiertos(limite)
        
        tickets_data = [{
            "id": t.id,
            "numero_ticket": t.numero_ticket,
            "cliente_id": t.cliente_id,
            "tipo": t.tipo.value,
            "estado": t.estado.value,
            "prioridad": t.prioridad,
            "asunto": t.asunto,
            "fecha_creacion": t.fecha_creacion.isoformat(),
            "asignado_a": t.asignado_a,
            "tiempo_transcurrido_horas": t.tiempo_transcurrido_horas
        } for t in tickets]
        
        return APIResponse(
            success=True,
            message=f"Se encontraron {len(tickets)} tickets abiertos",
            data=tickets_data
        )
    
    except Exception as e:
        logger.error(f"Error al obtener tickets: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/tickets/cliente/{cliente_id}", response_model=APIResponse)
async def obtener_tickets_cliente(
    cliente_id: int,
    limite: int = Query(default=50, le=200),
    current_user: str = Depends(verify_token)
):
    """Obtener tickets de un cliente específico"""
    try:
        # Verificar que el cliente existe
        cliente = repository.obtener_cliente(cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        # Obtener tickets del cliente
        tickets = repository.obtener_tickets_por_cliente(cliente_id, limite)
        
        tickets_data = [{
            "id": t.id,
            "numero_ticket": t.numero_ticket,
            "tipo": t.tipo.value,
            "estado": t.estado.value,
            "prioridad": t.prioridad,
            "asunto": t.asunto,
            "descripcion": t.descripcion,
            "categoria": t.categoria,
            "fecha_creacion": t.fecha_creacion.isoformat(),
            "fecha_actualizacion": t.fecha_actualizacion.isoformat() if t.fecha_actualizacion else None,
            "asignado_a": t.asignado_a,
            "resolucion": t.resolucion
        } for t in tickets]
        
        return APIResponse(
            success=True,
            message=f"Se encontraron {len(tickets)} tickets para el cliente",
            data=tickets_data
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener tickets del cliente: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# Endpoints de reportes
@app.post("/reportes/clientes", response_model=APIResponse)
async def generar_reporte_clientes(
    request: dict,
    current_user: str = Depends(verify_token)
):
    """Generar reporte de clientes"""
    try:
        parametros = {
            'filtros': {},
            'limite': request.get('limite', 1000)
        }
        
        if request.get('tipo_cliente'):
            parametros['filtros']['tipo_cliente'] = request['tipo_cliente']
        if request.get('activo') is not None:
            parametros['filtros']['activo'] = request['activo']
        
        reporte = reporte_service.generar_reporte_clientes(parametros)
        
        return APIResponse(
            success=True,
            message="Reporte generado exitosamente",
            data=reporte
        )
    
    except Exception as e:
        logger.error(f"Error al generar reporte: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.post("/reportes/transacciones", response_model=APIResponse)
async def generar_reporte_transacciones(
    request: dict,
    current_user: str = Depends(verify_token)
):
    """Generar reporte de transacciones"""
    try:
        fecha_inicio_str = request.get('fecha_inicio')
        fecha_fin_str = request.get('fecha_fin')
        
        if not fecha_inicio_str or not fecha_fin_str:
            raise HTTPException(status_code=400, detail="Las fechas de inicio y fin son requeridas")
        
        fecha_inicio = datetime.fromisoformat(fecha_inicio_str).date()
        fecha_fin = datetime.fromisoformat(fecha_fin_str).date()
        
        if fecha_fin < fecha_inicio:
            raise HTTPException(status_code=400, detail="La fecha de fin debe ser posterior a la fecha de inicio")
        
        fecha_inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())
        fecha_fin_dt = datetime.combine(fecha_fin, datetime.max.time())
        
        reporte = reporte_service.generar_reporte_transacciones(fecha_inicio_dt, fecha_fin_dt)
        
        return APIResponse(
            success=True,
            message="Reporte generado exitosamente",
            data=reporte
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al generar reporte: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# Endpoints de estadísticas
@app.get("/estadisticas/dashboard", response_model=APIResponse)
async def obtener_estadisticas_dashboard(current_user: str = Depends(verify_token)):
    """Obtener estadísticas para el dashboard"""
    try:
        estadisticas_clientes = repository.obtener_estadisticas_clientes()
        metricas_tickets = ticket_service.obtener_metricas_atencion()
        resumen_diario = transaccion_service.obtener_resumen_diario()
        
        dashboard = {
            'clientes': estadisticas_clientes,
            'tickets': metricas_tickets,
            'transacciones_hoy': resumen_diario,
            'fecha_actualizacion': datetime.now().isoformat()
        }
        
        return APIResponse(
            success=True,
            message="Estadísticas obtenidas exitosamente",
            data=dashboard
        )
    
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# Endpoint de salud
@app.get("/health")
async def health_check():
    """Verificar el estado de la API"""
    try:
        db_status = repository.test_connection()
        
        return {
            "status": "healthy" if db_status else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected" if db_status else "disconnected",
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "version": "1.0.0"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host=api_config.HOST,
        port=8001,
        reload=app_config.DEBUG,
        log_level="info"
    )