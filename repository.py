import logging
from contextlib import contextmanager
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from models import (
    Cliente, Promocion, Transaccion, Ticket, Empleado, Reporte,
    TipoCliente, EstadoPromocion, TipoPromocion, EstadoTicket, TipoTicket, TipoTransaccion
)
from config import DatabaseConfig, get_connection_string, db_config

# Importar el driver apropiado según el entorno
if db_config.IS_PRODUCTION:
    import pymysql
    pymysql.install_as_MySQLdb()
else:
    import pyodbc

class DatabaseRepository:
    """Repositorio principal para operaciones de base de datos del casino"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection_string = get_connection_string()
        self.logger = logging.getLogger(__name__)
        
    @contextmanager
    def get_connection(self):
        """Context manager para conexiones de base de datos"""
        conn = None
        try:
            if db_config.IS_PRODUCTION:
                # Usar pymysql para MySQL/PlanetScale
                import pymysql
                conn = pymysql.connect(
                    host=self._parse_mysql_url()['host'],
                    user=self._parse_mysql_url()['user'],
                    password=self._parse_mysql_url()['password'],
                    database=self._parse_mysql_url()['database'],
                    port=self._parse_mysql_url()['port'],
                    ssl={'ssl_disabled': False},
                    autocommit=False
                )
            else:
                # Usar pyodbc para SQL Server local
                conn = pyodbc.connect(self.connection_string)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Error de conexión a base de datos: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _parse_mysql_url(self) -> dict:
        """Parsea la URL de MySQL para extraer componentes"""
        import urllib.parse as urlparse
        url = urlparse.urlparse(self.connection_string)
        return {
            'host': url.hostname,
            'port': url.port or 3306,
            'user': url.username,
            'password': url.password,
            'database': url.path[1:]  # Remover el '/' inicial
        }
    
    def test_connection(self) -> bool:
        """Prueba la conexión a la base de datos"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            self.logger.error(f"Error al probar conexión: {e}")
            return False
    
    def initialize_database(self):
        """Inicializa las tablas de la base de datos"""
        if db_config.IS_PRODUCTION:
            # Tablas para MySQL/PlanetScale
            tables_sql = [
                """
                CREATE TABLE IF NOT EXISTS empleados (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    numero_empleado VARCHAR(20) UNIQUE NOT NULL,
                    nombres VARCHAR(100) NOT NULL,
                    apellidos VARCHAR(100) NOT NULL,
                    email VARCHAR(255) UNIQUE,
                    cargo VARCHAR(100),
                    departamento VARCHAR(100),
                    fecha_ingreso DATE DEFAULT (CURRENT_DATE),
                    activo BOOLEAN DEFAULT TRUE,
                    permisos TEXT,
                    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS clientes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    numero_documento VARCHAR(20) UNIQUE NOT NULL,
                    tipo_documento VARCHAR(5) DEFAULT 'CC',
                    nombres VARCHAR(100) NOT NULL,
                    apellidos VARCHAR(100) NOT NULL,
                    email VARCHAR(255),
                    telefono VARCHAR(20),
                    fecha_nacimiento DATE,
                    direccion VARCHAR(255),
                    ciudad VARCHAR(100),
                    tipo_cliente VARCHAR(20) DEFAULT 'nuevo',
                    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                    fecha_ultima_visita DATETIME,
                    total_visitas INT DEFAULT 0,
                    total_gastado DECIMAL(15,2) DEFAULT 0,
                    saldo DECIMAL(15,2) DEFAULT 0,
                    puntos_acumulados INT DEFAULT 0,
                    activo BOOLEAN DEFAULT TRUE,
                    preferencias TEXT,
                    notas TEXT,
                    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS promociones (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    codigo VARCHAR(20) UNIQUE NOT NULL,
                    titulo VARCHAR(200) NOT NULL,
                    descripcion TEXT,
                    tipo VARCHAR(50) NOT NULL,
                    valor DECIMAL(10,2) DEFAULT 0,
                    fecha_inicio DATETIME NOT NULL,
                    fecha_fin DATETIME NOT NULL,
                    estado VARCHAR(20) DEFAULT 'activa',
                    cliente_id INT,
                    usos_maximos INT DEFAULT 1,
                    usos_actuales INT DEFAULT 0,
                    condiciones TEXT,
                    qr_code VARCHAR(255),
                    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    creado_por VARCHAR(100),
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS transacciones (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    cliente_id INT NOT NULL,
                    tipo VARCHAR(50) NOT NULL,
                    monto DECIMAL(15,2) NOT NULL,
                    descripcion VARCHAR(255),
                    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ubicacion VARCHAR(100),
                    promocion_id INT,
                    puntos_ganados INT DEFAULT 0,
                    metodo_pago VARCHAR(50),
                    numero_referencia VARCHAR(100),
                    empleado_id INT,
                    notas TEXT,
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                    FOREIGN KEY (promocion_id) REFERENCES promociones(id),
                    FOREIGN KEY (empleado_id) REFERENCES empleados(id)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    numero_ticket VARCHAR(50) UNIQUE NOT NULL,
                    cliente_id INT NOT NULL,
                    tipo VARCHAR(50) NOT NULL,
                    estado VARCHAR(20) DEFAULT 'abierto',
                    prioridad VARCHAR(20) DEFAULT 'MEDIA',
                    asunto VARCHAR(255) NOT NULL,
                    descripcion TEXT,
                    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    fecha_resolucion DATETIME,
                    asignado_a VARCHAR(100),
                    categoria VARCHAR(100),
                    subcategoria VARCHAR(100),
                    resolucion TEXT,
                    satisfaccion_cliente INT,
                    tiempo_resolucion_horas DECIMAL(10,2),
                    seguimientos TEXT,
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS reportes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(255) NOT NULL,
                    tipo VARCHAR(100) NOT NULL,
                    parametros TEXT,
                    fecha_generacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                    generado_por VARCHAR(100),
                    archivo_path VARCHAR(500),
                    formato VARCHAR(20) DEFAULT 'PDF'
                )
                """
            ]
        else:
            # Tablas para SQL Server (desarrollo local)
            tables_sql = [
                """
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='empleados' AND xtype='U')
                CREATE TABLE empleados (
                    id INTEGER IDENTITY(1,1) PRIMARY KEY,
                    numero_empleado NVARCHAR(20) UNIQUE NOT NULL,
                    nombres NVARCHAR(100) NOT NULL,
                    apellidos NVARCHAR(100) NOT NULL,
                    email NVARCHAR(255) UNIQUE,
                    cargo NVARCHAR(100),
                    departamento NVARCHAR(100),
                    fecha_ingreso DATE DEFAULT GETDATE(),
                    activo BIT DEFAULT 1,
                    permisos NVARCHAR(MAX),
                    fecha_creacion DATETIME DEFAULT GETDATE(),
                    fecha_actualizacion DATETIME DEFAULT GETDATE()
                )
                """,
            """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='clientes' AND xtype='U')
            CREATE TABLE clientes (
                id INTEGER IDENTITY(1,1) PRIMARY KEY,
                numero_documento NVARCHAR(20) UNIQUE NOT NULL,
                tipo_documento NVARCHAR(5) DEFAULT 'CC',
                nombres NVARCHAR(100) NOT NULL,
                apellidos NVARCHAR(100) NOT NULL,
                email NVARCHAR(255),
                telefono NVARCHAR(20),
                fecha_nacimiento DATE,
                direccion NVARCHAR(255),
                ciudad NVARCHAR(100),
                tipo_cliente NVARCHAR(20) DEFAULT 'nuevo',
                fecha_registro DATETIME DEFAULT GETDATE(),
                fecha_ultima_visita DATETIME,
                total_visitas INTEGER DEFAULT 0,
                total_gastado DECIMAL(15,2) DEFAULT 0,
                saldo DECIMAL(15,2) DEFAULT 0,
                puntos_acumulados INTEGER DEFAULT 0,
                activo BIT DEFAULT 1,
                preferencias NVARCHAR(MAX),
                notas NVARCHAR(MAX),
                fecha_actualizacion DATETIME DEFAULT GETDATE()
            )
            """,
            """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='promociones' AND xtype='U')
            CREATE TABLE promociones (
                id INTEGER IDENTITY(1,1) PRIMARY KEY,
                codigo NVARCHAR(20) UNIQUE NOT NULL,
                titulo NVARCHAR(200) NOT NULL,
                descripcion NVARCHAR(MAX),
                tipo NVARCHAR(50) NOT NULL,
                valor DECIMAL(10,2) DEFAULT 0,
                fecha_inicio DATETIME NOT NULL,
                fecha_fin DATETIME NOT NULL,
                estado NVARCHAR(20) DEFAULT 'activa',
                cliente_id INTEGER,
                usos_maximos INTEGER DEFAULT 1,
                usos_actuales INTEGER DEFAULT 0,
                condiciones NVARCHAR(MAX),
                qr_code NVARCHAR(255),
                fecha_creacion DATETIME DEFAULT GETDATE(),
                creado_por NVARCHAR(100),
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            )
            """,
            """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='transacciones' AND xtype='U')
            CREATE TABLE transacciones (
                id INTEGER IDENTITY(1,1) PRIMARY KEY,
                cliente_id INTEGER NOT NULL,
                tipo NVARCHAR(50) NOT NULL,
                monto DECIMAL(15,2) NOT NULL,
                descripcion NVARCHAR(255),
                fecha DATETIME DEFAULT GETDATE(),
                ubicacion NVARCHAR(100),
                promocion_id INTEGER,
                puntos_ganados INTEGER DEFAULT 0,
                metodo_pago NVARCHAR(50),
                numero_referencia NVARCHAR(100),
                empleado_id INTEGER,
                notas NVARCHAR(MAX),
                FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                FOREIGN KEY (promocion_id) REFERENCES promociones(id),
                FOREIGN KEY (empleado_id) REFERENCES empleados(id)
            )
            """,
            """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='tickets' AND xtype='U')
            CREATE TABLE tickets (
                id INTEGER IDENTITY(1,1) PRIMARY KEY,
                numero_ticket NVARCHAR(50) UNIQUE NOT NULL,
                cliente_id INTEGER NOT NULL,
                tipo NVARCHAR(50) NOT NULL,
                estado NVARCHAR(20) DEFAULT 'abierto',
                prioridad NVARCHAR(20) DEFAULT 'MEDIA',
                asunto NVARCHAR(255) NOT NULL,
                descripcion NVARCHAR(MAX),
                fecha_creacion DATETIME DEFAULT GETDATE(),
                fecha_actualizacion DATETIME DEFAULT GETDATE(),
                fecha_resolucion DATETIME,
                asignado_a NVARCHAR(100),
                categoria NVARCHAR(100),
                subcategoria NVARCHAR(100),
                resolucion NVARCHAR(MAX),
                satisfaccion_cliente INTEGER,
                tiempo_resolucion_horas DECIMAL(10,2),
                seguimientos NVARCHAR(MAX),
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            )
            """,
            """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='reportes' AND xtype='U')
            CREATE TABLE reportes (
                id INTEGER IDENTITY(1,1) PRIMARY KEY,
                nombre NVARCHAR(255) NOT NULL,
                tipo NVARCHAR(100) NOT NULL,
                parametros NVARCHAR(MAX),
                fecha_generacion DATETIME DEFAULT GETDATE(),
                generado_por NVARCHAR(100),
                archivo_path NVARCHAR(500),
                formato NVARCHAR(20) DEFAULT 'PDF'
            )
            """
        ]
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                for sql in tables_sql:
                    cursor.execute(sql)
                
                # Migración: Agregar campo saldo si no existe
                try:
                    if db_config.IS_PRODUCTION:
                        # MySQL: Verificar si la columna existe
                        cursor.execute("""
                        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'clientes' AND COLUMN_NAME = 'saldo'
                        """)
                        if cursor.fetchone()[0] == 0:
                            cursor.execute("ALTER TABLE clientes ADD COLUMN saldo DECIMAL(15,2) DEFAULT 0")
                    else:
                        # SQL Server
                        cursor.execute("""
                        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
                                       WHERE TABLE_NAME = 'clientes' AND COLUMN_NAME = 'saldo')
                        BEGIN
                            ALTER TABLE clientes ADD saldo DECIMAL(15,2) DEFAULT 0
                        END
                        """)
                except Exception as migration_error:
                    self.logger.warning(f"Error en migración de saldo: {migration_error}")
                
                conn.commit()
                self.logger.info("Base de datos inicializada correctamente")
        except Exception as e:
            self.logger.error(f"Error al inicializar base de datos: {e}")
            raise

    # CRUD para Clientes
    def crear_cliente(self, cliente: Cliente) -> int:
        """Crea un nuevo cliente"""
        sql = """
        INSERT INTO clientes (numero_documento, tipo_documento, nombres, apellidos, email, telefono,
                            fecha_nacimiento, direccion, ciudad, tipo_cliente, saldo, puntos_acumulados,
                            preferencias, notas)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (
                    cliente.numero_documento, cliente.tipo_documento, cliente.nombres,
                    cliente.apellidos, cliente.email, cliente.telefono,
                    cliente.fecha_nacimiento, cliente.direccion, cliente.ciudad,
                    cliente.tipo_cliente.value, cliente.saldo, cliente.puntos_acumulados,
                    str(cliente.preferencias), cliente.notas
                ))
                conn.commit()
                
                # Obtener el ID del cliente creado
                if db_config.IS_PRODUCTION:
                    cursor.execute("SELECT LAST_INSERT_ID()")
                else:
                    cursor.execute("SELECT @@IDENTITY")
                cliente_id = cursor.fetchone()[0]
                self.logger.info(f"Cliente creado con ID: {cliente_id}")
                return cliente_id
        except Exception as e:
            self.logger.error(f"Error al crear cliente: {e}")
            raise
    
    def obtener_cliente(self, cliente_id: int) -> Optional[Cliente]:
        """Obtiene un cliente por ID"""
        sql = "SELECT * FROM clientes WHERE id = ?"
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (cliente_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_cliente(row)
                return None
        except Exception as e:
            self.logger.error(f"Error al obtener cliente: {e}")
            raise
    
    def obtener_cliente_por_documento(self, numero_documento: str) -> Optional[Cliente]:
        """Obtiene un cliente por número de documento"""
        sql = "SELECT * FROM clientes WHERE numero_documento = ?"
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (numero_documento,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_cliente(row)
                return None
        except Exception as e:
            self.logger.error(f"Error al obtener cliente por documento: {e}")
            raise
    
    def listar_clientes(self, filtros: Dict[str, Any] = None, limite: int = 100) -> List[Cliente]:
        """Lista clientes con filtros opcionales"""
        sql = "SELECT * FROM clientes WHERE 1=1"
        params = []
        
        if filtros:
            if 'activo' in filtros:
                sql += " AND activo = ?"
                params.append(filtros['activo'])
            if 'tipo_cliente' in filtros:
                sql += " AND tipo_cliente = ?"
                params.append(filtros['tipo_cliente'])
            if 'ciudad' in filtros:
                sql += " AND ciudad LIKE ?"
                params.append(f"%{filtros['ciudad']}%")
        
        sql += f" ORDER BY fecha_registro DESC OFFSET 0 ROWS FETCH NEXT {limite} ROWS ONLY"
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                return [self._row_to_cliente(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error al listar clientes: {e}")
            raise
    
    def actualizar_cliente(self, cliente: Cliente) -> bool:
        """Actualiza un cliente existente"""
        sql = """
        UPDATE clientes SET
            nombres = ?, apellidos = ?, email = ?, telefono = ?,
            fecha_nacimiento = ?, direccion = ?, ciudad = ?, tipo_cliente = ?,
            fecha_ultima_visita = ?, total_visitas = ?, total_gastado = ?,
            saldo = ?, puntos_acumulados = ?, activo = ?, preferencias = ?, notas = ?,
            fecha_actualizacion = GETDATE()
        WHERE id = ?
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (
                    cliente.nombres, cliente.apellidos, cliente.email, cliente.telefono,
                    cliente.fecha_nacimiento, cliente.direccion, cliente.ciudad,
                    cliente.tipo_cliente.value, cliente.fecha_ultima_visita,
                    cliente.total_visitas, cliente.total_gastado, cliente.saldo,
                    cliente.puntos_acumulados, cliente.activo, str(cliente.preferencias), 
                    cliente.notas, cliente.id
                ))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error al actualizar cliente: {e}")
            raise
    
    # CRUD para Promociones
    def crear_promocion(self, promocion: Promocion) -> int:
        """Crea una nueva promoción"""
        sql = """
        INSERT INTO promociones (codigo, titulo, descripcion, tipo, valor, fecha_inicio,
                               fecha_fin, cliente_id, usos_maximos, condiciones, creado_por)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (
                    promocion.codigo, promocion.titulo, promocion.descripcion,
                    promocion.tipo.value, promocion.valor, promocion.fecha_inicio,
                    promocion.fecha_fin, promocion.cliente_id, promocion.usos_maximos,
                    promocion.condiciones, promocion.creado_por
                ))
                conn.commit()
                
                cursor.execute("SELECT @@IDENTITY")
                promocion_id = cursor.fetchone()[0]
                self.logger.info(f"Promoción creada con ID: {promocion_id}")
                return promocion_id
        except Exception as e:
            self.logger.error(f"Error al crear promoción: {e}")
            raise
    
    def obtener_promociones_activas(self, cliente_id: Optional[int] = None) -> List[Promocion]:
        """Obtiene promociones activas, opcionalmente para un cliente específico"""
        sql = """
        SELECT * FROM promociones 
        WHERE estado = 'activa' AND fecha_inicio <= GETDATE() AND fecha_fin >= GETDATE()
        """
        params = []
        
        if cliente_id:
            sql += " AND (cliente_id IS NULL OR cliente_id = ?)"
            params.append(cliente_id)
        
        sql += " ORDER BY fecha_creacion DESC"
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                return [self._row_to_promocion(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error al obtener promociones activas: {e}")
            raise
    
    # CRUD para Transacciones
    def crear_transaccion(self, transaccion: Transaccion) -> int:
        """Crea una nueva transacción"""
        sql = """
        INSERT INTO transacciones (cliente_id, tipo, monto, descripcion, ubicacion,
                                 promocion_id, puntos_ganados, metodo_pago,
                                 numero_referencia, empleado_id, notas)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (
                    transaccion.cliente_id, transaccion.tipo.value, transaccion.monto,
                    transaccion.descripcion, transaccion.ubicacion, transaccion.promocion_id,
                    transaccion.puntos_ganados, transaccion.metodo_pago,
                    transaccion.numero_referencia, transaccion.empleado_id, transaccion.notas
                ))
                conn.commit()
                
                cursor.execute("SELECT @@IDENTITY")
                transaccion_id = cursor.fetchone()[0]
                
                # Actualizar puntos del cliente si es necesario
                if transaccion.puntos_ganados > 0:
                    self._actualizar_puntos_cliente(conn, transaccion.cliente_id, transaccion.puntos_ganados)
                
                self.logger.info(f"Transacción creada con ID: {transaccion_id}")
                return transaccion_id
        except Exception as e:
            self.logger.error(f"Error al crear transacción: {e}")
            raise
    
    def obtener_todas_transacciones(self, limite: int = 100) -> List[Transaccion]:
        """Obtiene todas las transacciones"""
        sql = """
        SELECT * FROM transacciones 
        ORDER BY fecha DESC 
        OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (limite,))
                rows = cursor.fetchall()
                
                return [self._row_to_transaccion(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error al obtener todas las transacciones: {e}")
            raise
    
    def obtener_transacciones_cliente(self, cliente_id: int, limite: int = 50) -> List[Transaccion]:
        """Obtiene las transacciones de un cliente"""
        sql = """
        SELECT * FROM transacciones 
        WHERE cliente_id = ? 
        ORDER BY fecha DESC 
        OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (cliente_id, limite))
                rows = cursor.fetchall()
                
                return [self._row_to_transaccion(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error al obtener transacciones del cliente: {e}")
            raise
    
    # CRUD para Tickets
    def crear_ticket(self, ticket: Ticket) -> int:
        """Crea un nuevo ticket"""
        sql = """
        INSERT INTO tickets (numero_ticket, cliente_id, tipo, prioridad, asunto,
                           descripcion, categoria, subcategoria, seguimientos)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (
                    ticket.numero_ticket, ticket.cliente_id, ticket.tipo.value,
                    ticket.prioridad, ticket.asunto, ticket.descripcion,
                    ticket.categoria, ticket.subcategoria, str(ticket.seguimientos)
                ))
                conn.commit()
                
                cursor.execute("SELECT @@IDENTITY")
                ticket_id = cursor.fetchone()[0]
                self.logger.info(f"Ticket creado con ID: {ticket_id}")
                return ticket_id
        except Exception as e:
            self.logger.error(f"Error al crear ticket: {e}")
            raise
    
    def obtener_tickets_abiertos(self, limite: int = 100) -> List[Ticket]:
        """Obtiene tickets abiertos"""
        sql = """
        SELECT * FROM tickets 
        WHERE estado IN ('abierto', 'en_proceso') 
        ORDER BY 
            CASE prioridad 
                WHEN 'CRITICA' THEN 1 
                WHEN 'ALTA' THEN 2 
                WHEN 'MEDIA' THEN 3 
                WHEN 'BAJA' THEN 4 
            END,
            fecha_creacion ASC
        OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (limite,))
                rows = cursor.fetchall()
                
                return [self._row_to_ticket(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error al obtener tickets abiertos: {e}")
            raise
    
    def obtener_tickets_por_cliente(self, cliente_id: int, limite: int = 50) -> List[Ticket]:
        """Obtiene tickets de un cliente específico"""
        sql = """
        SELECT * FROM tickets 
        WHERE cliente_id = ?
        ORDER BY fecha_creacion DESC
        OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (cliente_id, limite))
                rows = cursor.fetchall()
                
                return [self._row_to_ticket(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error al obtener tickets del cliente: {e}")
            raise
    
    # Métodos de utilidad para conversión de datos
    def _row_to_cliente(self, row) -> Cliente:
        """Convierte una fila de base de datos a objeto Cliente"""
        import json
        
        preferencias = {}
        if row[18]:  # preferencias
            try:
                preferencias = json.loads(row[18]) if isinstance(row[18], str) else {}
            except:
                preferencias = {}
        
        return Cliente(
            id=row[0], numero_documento=row[1], tipo_documento=row[2],
            nombres=row[3], apellidos=row[4], email=row[5], telefono=row[6],
            fecha_nacimiento=row[7], direccion=row[8], ciudad=row[9],
            tipo_cliente=TipoCliente(row[10]), fecha_registro=row[11],
            fecha_ultima_visita=row[12], total_visitas=row[13],
            total_gastado=float(row[14]) if row[14] else 0.0,
            saldo=float(row[20]) if row[20] else 0.0,
            puntos_acumulados=row[15], activo=bool(row[16]),
            preferencias=preferencias, notas=row[18] or ""
        )
    
    def _row_to_promocion(self, row) -> Promocion:
        """Convierte una fila de base de datos a objeto Promocion"""
        return Promocion(
            id=row[0], codigo=row[1], titulo=row[2], descripcion=row[3],
            tipo=TipoPromocion(row[4]), valor=float(row[5]) if row[5] else 0.0,
            fecha_inicio=row[6], fecha_fin=row[7],
            estado=EstadoPromocion(row[8]), cliente_id=row[9],
            usos_maximos=row[10], usos_actuales=row[11],
            condiciones=row[12] or "", qr_code=row[13],
            fecha_creacion=row[14], creado_por=row[15]
        )
    
    def _row_to_transaccion(self, row) -> Transaccion:
        """Convierte una fila de base de datos a objeto Transaccion"""
        return Transaccion(
            id=row[0], cliente_id=row[1], tipo=TipoTransaccion(row[2]),
            monto=float(row[3]) if row[3] else 0.0, descripcion=row[4],
            fecha=row[5], ubicacion=row[6], promocion_id=row[7],
            puntos_ganados=row[8], metodo_pago=row[9],
            numero_referencia=row[10], empleado_id=row[11], notas=row[12] or ""
        )
    
    def _row_to_ticket(self, row) -> Ticket:
        """Convierte una fila de base de datos a objeto Ticket"""
        import json
        
        seguimientos = []
        if row[18]:  # seguimientos
            try:
                seguimientos = json.loads(row[18]) if isinstance(row[18], str) else []
            except:
                seguimientos = []
        
        return Ticket(
            id=row[0], numero_ticket=row[1], cliente_id=row[2],
            tipo=TipoTicket(row[3]), estado=EstadoTicket(row[4]),
            prioridad=row[5], asunto=row[6], descripcion=row[7],
            fecha_creacion=row[8], fecha_actualizacion=row[9],
            fecha_resolucion=row[10], asignado_a=row[11],
            categoria=row[12], subcategoria=row[13], resolucion=row[14] or "",
            satisfaccion_cliente=row[15], tiempo_resolucion_horas=row[16],
            seguimientos=seguimientos
        )
    
    def _actualizar_puntos_cliente(self, conn, cliente_id: int, puntos: int):
        """Actualiza los puntos acumulados de un cliente"""
        sql = """
        UPDATE clientes 
        SET puntos_acumulados = puntos_acumulados + ?,
            fecha_actualizacion = GETDATE()
        WHERE id = ?
        """
        cursor = conn.cursor()
        cursor.execute(sql, (puntos, cliente_id))
    
    # Métodos de reportes y estadísticas
    def obtener_estadisticas_clientes(self) -> Dict[str, Any]:
        """Obtiene estadísticas generales de clientes"""
        sql = """
        SELECT 
            COUNT(*) as total_clientes,
            COUNT(CASE WHEN activo = 1 THEN 1 END) as clientes_activos,
            COUNT(CASE WHEN tipo_cliente = 'vip' THEN 1 END) as clientes_vip,
            AVG(CAST(total_gastado AS FLOAT)) as promedio_gastado,
            SUM(puntos_acumulados) as total_puntos
        FROM clientes
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                row = cursor.fetchone()
                
                return {
                    'total_clientes': row[0],
                    'clientes_activos': row[1],
                    'clientes_vip': row[2],
                    'promedio_gastado': float(row[3]) if row[3] else 0.0,
                    'total_puntos': row[4] or 0
                }
        except Exception as e:
            self.logger.error(f"Error al obtener estadísticas de clientes: {e}")
            raise
    
    def obtener_transacciones_periodo(self, fecha_inicio: datetime, fecha_fin: datetime) -> List[Dict[str, Any]]:
        """Obtiene resumen de transacciones por período"""
        sql = """
        SELECT 
            tipo,
            COUNT(*) as cantidad,
            SUM(monto) as total_monto,
            AVG(monto) as promedio_monto
        FROM transacciones 
        WHERE fecha BETWEEN ? AND ?
        GROUP BY tipo
        ORDER BY total_monto DESC
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (fecha_inicio, fecha_fin))
                rows = cursor.fetchall()
                
                return [{
                    'tipo': row[0],
                    'cantidad': row[1],
                    'total_monto': float(row[2]) if row[2] else 0.0,
                    'promedio_monto': float(row[3]) if row[3] else 0.0
                } for row in rows]
        except Exception as e:
            self.logger.error(f"Error al obtener transacciones por período: {e}")
            raise