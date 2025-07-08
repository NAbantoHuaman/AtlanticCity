from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid

class TipoCliente(Enum):
    """Tipos de cliente del casino"""
    NUEVO = "nuevo"
    REGULAR = "regular"
    FRECUENTE = "frecuente"
    VIP = "vip"
    INACTIVO = "inactivo"

class EstadoPromocion(Enum):
    """Estados de las promociones"""
    ACTIVA = "activa"
    CANJEADA = "canjeada"
    EXPIRADA = "expirada"
    CANCELADA = "cancelada"

class TipoPromocion(Enum):
    """Tipos de promociones"""
    DESCUENTO = "descuento"
    PUNTOS_BONUS = "puntos_bonus"
    BEBIDA_GRATIS = "bebida_gratis"
    ENTRADA_GRATIS = "entrada_gratis"
    CASHBACK = "cashback"
    TORNEO_ESPECIAL = "torneo_especial"

class EstadoTicket(Enum):
    """Estados de los tickets de atención"""
    ABIERTO = "abierto"
    EN_PROCESO = "en_proceso"
    RESUELTO = "resuelto"
    CERRADO = "cerrado"
    ESCALADO = "escalado"

class TipoTicket(Enum):
    """Tipos de tickets"""
    QUEJA = "queja"
    SUGERENCIA = "sugerencia"
    CONSULTA = "consulta"
    RECLAMO = "reclamo"
    SOPORTE_TECNICO = "soporte_tecnico"

class TipoTransaccion(Enum):
    """Tipos de transacciones"""
    INGRESO = "ingreso"
    JUEGO = "juego"
    CONSUMO = "consumo"
    CANJE_PROMOCION = "canje_promocion"
    RETIRO = "retiro"

@dataclass
class Cliente:
    """Modelo de datos para clientes del casino"""
    id: Optional[int] = None
    numero_documento: str = ""
    tipo_documento: str = "CC"  # CC, CE, PP
    nombres: str = ""
    apellidos: str = ""
    email: str = ""
    telefono: str = ""
    fecha_nacimiento: Optional[date] = None
    direccion: str = ""
    ciudad: str = ""
    tipo_cliente: TipoCliente = TipoCliente.NUEVO
    fecha_registro: datetime = field(default_factory=datetime.now)
    fecha_ultima_visita: Optional[datetime] = None
    total_visitas: int = 0
    total_gastado: float = 0.0
    saldo: float = 0.0
    puntos_acumulados: int = 0
    activo: bool = True
    preferencias: Dict[str, Any] = field(default_factory=dict)
    notas: str = ""
    
    def __post_init__(self):
        if self.fecha_nacimiento and isinstance(self.fecha_nacimiento, str):
            self.fecha_nacimiento = datetime.strptime(self.fecha_nacimiento, '%Y-%m-%d').date()
    
    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}".strip()
    
    @property
    def edad(self) -> Optional[int]:
        if self.fecha_nacimiento:
            today = date.today()
            return today.year - self.fecha_nacimiento.year - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
        return None
    
    def es_cliente_frecuente(self, min_visitas: int = 10) -> bool:
        return self.total_visitas >= min_visitas
    
    def puede_recibir_promocion(self) -> bool:
        return self.activo and self.tipo_cliente != TipoCliente.INACTIVO

@dataclass
class Promocion:
    """Modelo de datos para promociones"""
    id: Optional[int] = None
    codigo: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    titulo: str = ""
    descripcion: str = ""
    tipo: TipoPromocion = TipoPromocion.DESCUENTO
    valor: float = 0.0  # Porcentaje de descuento o cantidad
    fecha_inicio: datetime = field(default_factory=datetime.now)
    fecha_fin: datetime = field(default_factory=lambda: datetime.now().replace(hour=23, minute=59, second=59))
    estado: EstadoPromocion = EstadoPromocion.ACTIVA
    cliente_id: Optional[int] = None
    usos_maximos: int = 1
    usos_actuales: int = 0
    condiciones: str = ""
    qr_code: Optional[str] = None
    fecha_creacion: datetime = field(default_factory=datetime.now)
    creado_por: Optional[str] = None
    
    @property
    def esta_vigente(self) -> bool:
        now = datetime.now()
        return self.fecha_inicio <= now <= self.fecha_fin
    
    @property
    def puede_canjearse(self) -> bool:
        return (self.estado == EstadoPromocion.ACTIVA and 
                self.esta_vigente and 
                self.usos_actuales < self.usos_maximos)
    
    def canjear(self) -> bool:
        if self.puede_canjearse:
            self.usos_actuales += 1
            if self.usos_actuales >= self.usos_maximos:
                self.estado = EstadoPromocion.CANJEADA
            return True
        return False

@dataclass
class Transaccion:
    """Modelo de datos para transacciones"""
    id: Optional[int] = None
    cliente_id: int = 0
    tipo: TipoTransaccion = TipoTransaccion.INGRESO
    monto: float = 0.0
    descripcion: str = ""
    fecha: datetime = field(default_factory=datetime.now)
    ubicacion: str = ""  # Mesa, máquina, bar, etc.
    promocion_id: Optional[int] = None
    puntos_ganados: int = 0
    metodo_pago: str = ""  # Efectivo, tarjeta, etc.
    numero_referencia: Optional[str] = None
    empleado_id: Optional[int] = None
    notas: str = ""
    
    def calcular_puntos(self, puntos_por_peso: float = 0.1) -> int:
        """Calcula puntos basado en el monto de la transacción"""
        if self.tipo in [TipoTransaccion.JUEGO, TipoTransaccion.CONSUMO]:
            return int(self.monto * puntos_por_peso)
        return 0

@dataclass
class Ticket:
    """Modelo de datos para tickets de atención al cliente"""
    id: Optional[int] = None
    numero_ticket: str = field(default_factory=lambda: f"TK{datetime.now().strftime('%Y%m%d%H%M%S')}")
    cliente_id: int = 0
    tipo: TipoTicket = TipoTicket.CONSULTA
    estado: EstadoTicket = EstadoTicket.ABIERTO
    prioridad: str = "MEDIA"  # BAJA, MEDIA, ALTA, CRITICA
    asunto: str = ""
    descripcion: str = ""
    fecha_creacion: datetime = field(default_factory=datetime.now)
    fecha_actualizacion: datetime = field(default_factory=datetime.now)
    fecha_resolucion: Optional[datetime] = None
    asignado_a: Optional[str] = None
    categoria: str = ""
    subcategoria: str = ""
    resolucion: str = ""
    satisfaccion_cliente: Optional[int] = None  # 1-5
    tiempo_resolucion_horas: Optional[float] = None
    seguimientos: List[Dict[str, Any]] = field(default_factory=list)
    
    def agregar_seguimiento(self, comentario: str, usuario: str):
        """Agrega un seguimiento al ticket"""
        seguimiento = {
            'fecha': datetime.now(),
            'usuario': usuario,
            'comentario': comentario
        }
        self.seguimientos.append(seguimiento)
        self.fecha_actualizacion = datetime.now()
    
    def resolver(self, resolucion: str, usuario: str):
        """Marca el ticket como resuelto"""
        self.estado = EstadoTicket.RESUELTO
        self.resolucion = resolucion
        self.fecha_resolucion = datetime.now()
        self.fecha_actualizacion = datetime.now()
        
        # Calcular tiempo de resolución
        if self.fecha_resolucion and self.fecha_creacion:
            delta = self.fecha_resolucion - self.fecha_creacion
            self.tiempo_resolucion_horas = delta.total_seconds() / 3600
        
        self.agregar_seguimiento(f"Ticket resuelto: {resolucion}", usuario)
    
    @property
    def esta_abierto(self) -> bool:
        return self.estado in [EstadoTicket.ABIERTO, EstadoTicket.EN_PROCESO]
    
    @property
    def tiempo_transcurrido_horas(self) -> float:
        delta = datetime.now() - self.fecha_creacion
        return delta.total_seconds() / 3600

@dataclass
class Empleado:
    """Modelo de datos para empleados"""
    id: Optional[int] = None
    numero_empleado: str = ""
    nombres: str = ""
    apellidos: str = ""
    email: str = ""
    cargo: str = ""
    departamento: str = ""
    fecha_ingreso: date = field(default_factory=date.today)
    activo: bool = True
    permisos: List[str] = field(default_factory=list)
    
    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}".strip()

@dataclass
class Reporte:
    """Modelo de datos para reportes"""
    id: Optional[int] = None
    nombre: str = ""
    tipo: str = ""  # clientes, promociones, transacciones, tickets
    parametros: Dict[str, Any] = field(default_factory=dict)
    fecha_generacion: datetime = field(default_factory=datetime.now)
    generado_por: Optional[str] = None
    archivo_path: Optional[str] = None
    formato: str = "PDF"  # PDF, EXCEL, CSV
    
# Funciones de utilidad para validación
def validar_email(email: str) -> bool:
    """Valida formato de email"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validar_telefono(telefono: str) -> bool:
    """Valida formato de teléfono"""
    import re
    # Acepta formatos: +57 300 123 4567, 300-123-4567, 3001234567
    pattern = r'^[+]?[0-9\s\-\(\)]{7,15}$'
    return re.match(pattern, telefono) is not None

def validar_documento(documento: str, tipo: str = "CC") -> bool:
    """Valida número de documento según el tipo"""
    if tipo == "CC":  # Cédula de ciudadanía
        return documento.isdigit() and 6 <= len(documento) <= 10
    elif tipo == "CE":  # Cédula de extranjería
        return documento.isdigit() and 6 <= len(documento) <= 12
    elif tipo == "PP":  # Pasaporte
        return 6 <= len(documento) <= 12
    return False