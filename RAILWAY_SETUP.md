# Alternativas Gratuitas para MySQL Server

⚠️ **Railway ya no ofrece MySQL Server gratuito**. Aquí tienes las mejores alternativas gratuitas para tu aplicación:

## 🎯 Opciones Recomendadas

### 1. **Aiven (Recomendado) - MySQL Gratuito**

✅ **MySQL Server real** - Compatible 100%  
✅ **1 mes gratis** - Perfecto para desarrollo  
✅ **Fácil configuración**  
✅ **Backup automático**  

**Pasos:**
1. Ir a: https://aiven.io
2. Crear cuenta gratuita
3. "Create Service" → **MySQL**
4. Seleccionar plan gratuito (1 mes)
5. Copiar `DATABASE_URL`
6. Configurar en Render como variable `DATABASE_URL`

### 2. **FreeSQLDatabase - MySQL Permanente**

✅ **Completamente gratuito**  
✅ **MySQL Server real**  
✅ **Sin límite de tiempo**  
❌ Limitado a 5MB  

**Pasos:**
1. Ir a: https://www.freesqldatabase.com
2. Crear cuenta gratuita
3. Crear base de datos MySQL
4. Obtener credenciales
5. Formar URL: `mysql://usuario:password@host:puerto/database`

### 3. **PlanetScale (Alternativa)**

✅ **MySQL compatible**  
✅ **10GB gratis**  
❌ Requiere tarjeta de crédito  

### 4. **Usar SQLite (Más Simple)**

✅ **Completamente gratuito**  
✅ **Sin configuración externa**  
✅ **Perfecto para desarrollo**  
❌ No escalable para producción  

## 🚀 Configuración Rápida con Aiven

### 1. Crear MySQL en Aiven

1. **Registrarse**: https://aiven.io
2. **"Create Service"** → **MySQL**
3. **Seleccionar**: Plan gratuito (1 mes)
4. **Región**: Elegir la más cercana
5. **Crear servicio** (tarda 2-3 minutos)

### 2. Obtener DATABASE_URL

1. **Hacer clic** en tu servicio MySQL
2. **Ir a "Overview"**
3. **Copiar** la "Service URI" completa
   - Formato: `mysql://usuario:password@host:puerto/defaultdb?ssl-mode=REQUIRED`

### 3. Configurar en Render

1. **Ir a tu app en Render**
2. **Settings** → **Environment Variables**
3. **Agregar**:
   - **Key**: `DATABASE_URL`
   - **Value**: *(URL de Aiven)*
4. **Manual Deploy**

## 💡 Alternativa Simple: SQLite

Si prefieres algo **más simple y gratuito permanente**:

### Configurar SQLite

1. **No configurar** `DATABASE_URL` en Render
2. Tu app usará **automáticamente SQLite**
3. **Redeploy** y listo

**Ventajas de SQLite:**
- ✅ Completamente gratuito
- ✅ Sin configuración externa
- ✅ Perfecto para desarrollo/demo
- ❌ No escalable para muchos usuarios

## 📊 SQL para crear tablas (Referencia)

### Crear todas las tablas

```sql
-- Crear tablas
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

-- Insertar cliente de prueba
INSERT INTO clientes (numero_documento, nombres, apellidos, saldo, puntos_acumulados) 
VALUES ('75592455', 'Juan', 'Pérez', 1000.00, 500);
```

#### Opción B: Automático (Recomendado)
1. Actualiza `DATABASE_URL` en Render
2. Redeploy tu aplicación en Render
3. Las tablas se crearán automáticamente al iniciar

### 5. Redeploy en Render

1. Ve a tu servicio en Render
2. Click "Manual Deploy" → "Deploy latest commit"
3. Espera a que termine el deployment
4. Verifica logs para confirmar conexión a Railway

### 6. Verificar conexión

```bash
# Probar endpoint
curl https://tu-app.onrender.com/health

# Probar login de cliente
curl -X POST https://tu-app.onrender.com/auth/cliente-login \
  -H "Content-Type: application/json" \
  -d '{"numero_documento": "75592455"}'
```

### 7. Migrar datos existentes (Opcional)

Si tienes datos en tu base local:

```bash
# Exportar desde SQLite local
sqlite3 atlantic_city_casino.db .dump > backup.sql

# Convertir a MySQL y ejecutar en Railway Console
# (Requiere ajustes manuales de sintaxis)
```

## Ventajas de Railway + Render

✅ **Separación de responsabilidades**: Base de datos independiente
✅ **Escalabilidad**: Cada servicio puede escalar independientemente
✅ **Backup automático**: Railway hace backups automáticos
✅ **Monitoreo**: Métricas separadas para DB y aplicación
✅ **Costo**: Gratuito para desarrollo (500 horas/mes Railway)

## Troubleshooting

### Error de conexión
1. Verifica que `DATABASE_URL` esté correcta
2. Verifica que Railway MySQL esté activo
3. Revisa logs en Render Dashboard

### Tablas no se crean
1. Verifica que `IS_PRODUCTION=true` se detecte correctamente
2. Revisa logs de inicialización en Render
3. Ejecuta SQL manualmente en Railway Console

### Performance lenta
1. Railway free tier tiene limitaciones
2. Considera optimizar consultas SQL
3. Agrega índices si es necesario

## Monitoreo

- **Railway**: Dashboard → Metrics (CPU, RAM, conexiones)
- **Render**: Dashboard → Metrics (requests, response time)
- **Logs**: Ambos servicios tienen logs en tiempo real

## Costos

- **Railway**: Gratuito (500 horas/mes, 1GB storage)
- **Render**: Gratuito (se duerme después de 15 min)
- **Total**: $0/mes para desarrollo

## ✅ Verificación

### 1. Verificar Backend
- Abre tu app en Render
- Debería cargar sin errores
- Prueba registrar un cliente

### 2. Verificar Base de Datos
- Las tablas se crean automáticamente
- Prueba las funciones principales

### 3. Verificar Frontend
- Registro de clientes ✅
- Promociones ✅
- Transacciones ✅

## 🎯 Recomendaciones por Uso

### Para Desarrollo/Demo
**SQLite** (Más simple)
- ✅ Sin configuración
- ✅ Completamente gratis
- ✅ Funciona inmediatamente

### Para Producción Pequeña
**Aiven MySQL** (1 mes gratis)
- ✅ MySQL Server real
- ✅ Backup automático
- ✅ Escalable

### Para Producción Permanente
**FreeSQLDatabase** (Limitado pero gratis)
- ✅ MySQL permanente
- ❌ Solo 5MB
- ✅ Sin costo

## 🔧 Troubleshooting

### Error de conexión
- Verifica `DATABASE_URL` en Render
- Revisa los logs de deploy
- Confirma que el servicio MySQL esté activo

### Tablas no se crean
- Tu código las crea automáticamente
- Si falla, revisa los logs de Render
- Verifica permisos de la base de datos

### App no carga
- Revisa Environment Variables
- Confirma que `requirements.txt` tenga `pymysql`

## 💰 Costos Comparados

| Opción | Costo | Límites | Duración |
|--------|-------|---------|----------|
| **SQLite** | $0 | Básico | Permanente |
| **Aiven** | $0 | 1GB | 1 mes |
| **FreeSQLDatabase** | $0 | 5MB | Permanente |
| **PlanetScale** | $0 | 10GB | Permanente* |

*Requiere tarjeta de crédito

## 🚀 Próximos Pasos

1. **Elegir opción** según tus necesidades
2. **Configurar** `DATABASE_URL` en Render
3. **Redeploy** tu aplicación
4. **Probar** todas las funciones
5. **Monitorear** el uso

## 📞 Soporte

- **Aiven**: https://aiven.io/support
- **Render**: https://render.com/docs
- **Tu código**: Ya está optimizado para MySQL Server

---

¡Tu aplicación del casino está lista para usar MySQL Server! 🎰🚀