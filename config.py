import os
from dataclasses import dataclass, field
from typing import Optional, List
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

@dataclass
class DatabaseConfig:
    """Configuración de base de datos"""
    # Configuración para producción (MySQL/PlanetScale)
    DATABASE_URL: Optional[str] = os.getenv('DATABASE_URL')
    
    # Configuración para desarrollo local (SQL Server)
    SERVER: str = os.getenv('DB_SERVER', 'localhost\\NESTOR23')
    DATABASE: str = os.getenv('DB_NAME', 'atlantic_city_casino')
    USERNAME: Optional[str] = os.getenv('DB_USERNAME')
    PASSWORD: Optional[str] = os.getenv('DB_PASSWORD')
    DRIVER: str = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
    TRUSTED_CONNECTION: bool = os.getenv('DB_TRUSTED_CONNECTION', 'true').lower() == 'true'
    CONNECTION_TIMEOUT: int = int(os.getenv('DB_CONNECTION_TIMEOUT', '30'))
    COMMAND_TIMEOUT: int = int(os.getenv('DB_COMMAND_TIMEOUT', '30'))
    
    # Detectar entorno
    IS_PRODUCTION: bool = os.getenv('RENDER') is not None or os.getenv('DATABASE_URL') is not None

@dataclass
class SecurityConfig:
    """Configuración de seguridad"""
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'atlantic-city-secret-key-2024')
    ENCRYPTION_KEY: Optional[str] = os.getenv('ENCRYPTION_KEY')
    JWT_ALGORITHM: str = 'HS256'
    JWT_EXPIRATION_HOURS: int = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30

@dataclass
class ApplicationConfig:
    """Configuración general de la aplicación"""
    APP_NAME: str = 'Atlantic City Casino CRM'
    VERSION: str = '1.0.0'
    DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'logs/atlantic_city.log')
    BACKUP_DIRECTORY: str = os.getenv('BACKUP_DIR', 'backups')
    REPORTS_DIRECTORY: str = os.getenv('REPORTS_DIR', 'reports')
    QR_CODES_DIRECTORY: str = os.getenv('QR_DIR', 'qr_codes')

@dataclass
class CasinoConfig:
    """Configuración específica del casino"""
    PROMOCION_EXPIRY_DAYS: int = int(os.getenv('PROMOCION_EXPIRY_DAYS', '30'))
    PUNTOS_POR_PESO: float = float(os.getenv('PUNTOS_POR_PESO', '0.1'))
    DESCUENTO_CLIENTE_FRECUENTE: float = float(os.getenv('DESCUENTO_FRECUENTE', '0.15'))
    MIN_VISITAS_CLIENTE_FRECUENTE: int = int(os.getenv('MIN_VISITAS_FRECUENTE', '10'))
    QR_CODE_EXPIRY_HOURS: int = int(os.getenv('QR_EXPIRY_HOURS', '24'))
    MAX_PROMOCIONES_ACTIVAS: int = int(os.getenv('MAX_PROMOCIONES_ACTIVAS', '5'))
    puntos_bienvenida: int = int(os.getenv('PUNTOS_BIENVENIDA', '100'))
    promocion_bienvenida_activa: bool = os.getenv('PROMOCION_BIENVENIDA_ACTIVA', 'true').lower() == 'true'
    puntos_por_peso: float = float(os.getenv('PUNTOS_POR_PESO', '0.1'))
    umbral_vip: float = float(os.getenv('UMBRAL_VIP', '50000.0'))
    umbral_frecuente: int = int(os.getenv('UMBRAL_FRECUENTE', '20'))
    umbral_regular: int = int(os.getenv('UMBRAL_REGULAR', '5'))



@dataclass
class APIConfig:
    """Configuración de API"""
    HOST: str = os.getenv('API_HOST', '0.0.0.0')
    PORT: int = int(os.getenv('API_PORT', '8000'))
    WORKERS: int = int(os.getenv('API_WORKERS', '4'))
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv('RATE_LIMIT', '100'))
    CORS_ORIGINS: list = field(default_factory=lambda: os.getenv('CORS_ORIGINS', '*').split(','))
    API_PREFIX: str = '/api/v1'

# Instancias globales de configuración
db_config = DatabaseConfig()
security_config = SecurityConfig()
app_config = ApplicationConfig()
casino_config = CasinoConfig()
api_config = APIConfig()

def get_connection_string() -> str:
    """Genera la cadena de conexión a la base de datos"""
    # Si estamos en producción, usar DATABASE_URL (MySQL/PlanetScale)
    if db_config.IS_PRODUCTION and db_config.DATABASE_URL:
        return db_config.DATABASE_URL
    
    # Si estamos en desarrollo local, usar SQL Server
    if db_config.TRUSTED_CONNECTION:
        return (
            f"DRIVER={{{db_config.DRIVER}}};"
            f"SERVER={db_config.SERVER};"
            f"DATABASE={db_config.DATABASE};"
            f"Trusted_Connection=yes;"
            f"Connection Timeout={db_config.CONNECTION_TIMEOUT};"
        )
    else:
        return (
            f"DRIVER={{{db_config.DRIVER}}};"
            f"SERVER={db_config.SERVER};"
            f"DATABASE={db_config.DATABASE};"
            f"UID={db_config.USERNAME};"
            f"PWD={db_config.PASSWORD};"
            f"Connection Timeout={db_config.CONNECTION_TIMEOUT};"
        )

def validate_config() -> bool:
    """Valida que la configuración sea correcta"""
    errors = []
    
    if not db_config.SERVER:
        errors.append("DB_SERVER no está configurado")
    
    if not db_config.DATABASE:
        errors.append("DB_NAME no está configurado")
    
    if not db_config.TRUSTED_CONNECTION and (not db_config.USERNAME or not db_config.PASSWORD):
        errors.append("Credenciales de base de datos no configuradas")
    
    if not security_config.SECRET_KEY:
        errors.append("SECRET_KEY no está configurado")
    
    if errors:
        print("Errores de configuración:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True