# Guía de Deployment: Render + PlanetScale

## Preparación del Proyecto

### 1. Subir código a GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/tu-usuario/atlantic-city-casino.git
git push -u origin main
```

## Configuración de PlanetScale (Base de Datos)

### 1. Crear cuenta en PlanetScale
- Ve a [planetscale.com](https://planetscale.com)
- Regístrate con GitHub
- Plan gratuito: 10GB de almacenamiento

### 2. Crear base de datos
```bash
# Instalar CLI de PlanetScale (opcional)
npm install -g @planetscale/cli

# O usar la interfaz web:
# 1. Click "New Database"
# 2. Nombre: "atlantic-city-casino"
# 3. Región: "us-east" (más cercana)
```

### 3. Obtener string de conexión
1. En PlanetScale Dashboard
2. Selecciona tu base de datos
3. Ve a "Connect"
4. Selecciona "General" como framework
5. Copia la URL de conexión (formato: `mysql://usuario:password@host:port/database`)

### 4. Crear tablas (Migración)
```sql
-- Ejecutar en PlanetScale Console o usando un cliente MySQL

CREATE TABLE empleados (
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
);

CREATE TABLE clientes (
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
);

CREATE TABLE promociones (
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
);

CREATE TABLE transacciones (
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
);

CREATE TABLE tickets (
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
);

CREATE TABLE reportes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    tipo VARCHAR(100) NOT NULL,
    parametros TEXT,
    fecha_generacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    generado_por VARCHAR(100),
    archivo_path VARCHAR(500),
    formato VARCHAR(20) DEFAULT 'PDF'
);
```

## Configuración de Render (Backend + Frontend)

### 1. Crear cuenta en Render
- Ve a [render.com](https://render.com)
- Regístrate con GitHub
- Plan gratuito disponible

### 2. Crear Web Service
1. Click "New +" → "Web Service"
2. Conecta tu repositorio de GitHub
3. Configuración:
   - **Name**: `atlantic-city-casino`
   - **Environment**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `uvicorn api:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`

### 3. Variables de Entorno en Render
En el dashboard de Render, ve a "Environment" y agrega:

```
RENDER=true
DATABASE_URL=mysql://usuario:password@host:port/database
SECRET_KEY=tu-clave-secreta-muy-segura
DEBUG=false
LOG_LEVEL=INFO
PUNTOS_POR_PESO=0.1
PROMOCION_BIENVENIDA_ACTIVA=true
PUNTOS_BIENVENIDA=100
```

### 4. Deploy
1. Click "Create Web Service"
2. Render automáticamente:
   - Clona tu repositorio
   - Ejecuta `build.sh`
   - Instala dependencias
   - Inicia la aplicación
   - Te da una URL pública

## Verificación del Deployment

### 1. Verificar Backend
```bash
# Reemplaza con tu URL de Render
curl https://tu-app.onrender.com/
```

### 2. Verificar Base de Datos
```bash
# Endpoint de prueba
curl https://tu-app.onrender.com/clientes
```

### 3. Verificar Frontend
Visita: `https://tu-app.onrender.com/cliente.html`

## Datos de Prueba

### Insertar cliente de prueba
```sql
INSERT INTO clientes (numero_documento, nombres, apellidos, saldo, puntos_acumulados) 
VALUES ('75592455', 'Juan', 'Pérez', 1000.00, 500);
```

### Login de prueba
- Documento: `75592455`
- URL: `https://tu-app.onrender.com/cliente.html`

## Troubleshooting

### Error de conexión a base de datos
1. Verifica que DATABASE_URL esté correcta
2. Verifica que PlanetScale esté activo
3. Revisa logs en Render Dashboard

### Error 500 en la aplicación
1. Ve a Render Dashboard → Logs
2. Busca errores de Python
3. Verifica que todas las dependencias estén en requirements.txt

### Frontend no carga
1. Verifica que los archivos estén en `/static`
2. Verifica rutas en `api.py`
3. Verifica CORS si es necesario

## Costos

- **PlanetScale**: Gratuito hasta 10GB
- **Render**: Gratuito con limitaciones (se duerme después de 15 min)
- **Total**: $0/mes para desarrollo y pruebas

## Próximos Pasos

1. Configurar dominio personalizado
2. Configurar SSL (automático en Render)
3. Configurar backups de base de datos
4. Monitoreo y alertas
5. CI/CD automático con GitHub Actions