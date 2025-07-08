# Sistema de Gestión de Clientes - Casino Atlantic City

## Descripción

Sistema unificado de gestión de clientes para Casino Atlantic City que incluye tanto una aplicación de escritorio (PyQt5) como una aplicación web moderna (FastAPI + HTML/CSS/JS). El sistema permite gestionar clientes, promociones, transacciones, tickets de atención al cliente y generar reportes detallados.

## Características Principales

### Aplicación de Escritorio (PyQt5)
- ✅ Interfaz moderna con estilo Fusion
- ✅ Conexión a múltiples bases de datos (SQL Server, MySQL, PostgreSQL, SQLite)
- ✅ Editor SQL con resaltado de sintaxis
- ✅ Visualización de datos en tablas
- ✅ Exportación de resultados (Excel, CSV, JSON)
- ✅ Diagramas de base de datos con NetworkX
- ✅ Plantillas SQL predefinidas
- ✅ Gestión de archivos SQL

### Aplicación Web (FastAPI)
- ✅ API REST completa con documentación automática
- ✅ Autenticación JWT con tokens seguros
- ✅ Gestión completa de clientes del casino
- ✅ Sistema de promociones automáticas
- ✅ Registro de transacciones con cálculo de puntos
- ✅ Sistema de tickets de atención al cliente
- ✅ Dashboard con estadísticas en tiempo real
- ✅ Generación de reportes en Excel
- ✅ Interfaz web moderna y responsiva

## Estructura del Proyecto

```
python/
├── baseDeDatos.py          # Aplicación de escritorio PyQt5
├── config.py               # Configuraciones del sistema
├── models.py               # Modelos de datos
├── repository.py           # Capa de acceso a datos
├── services.py             # Lógica de negocio
├── api.py                  # API web FastAPI
├── static/
│   ├── index.html          # Interfaz web principal
│   ├── styles.css          # Estilos CSS
│   └── app.js              # Lógica JavaScript
├── requirements.txt        # Dependencias
└── README.md              # Este archivo
```

## Instalación

### Prerrequisitos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

## Uso

### Aplicación de Escritorio

```bash
python baseDeDatos.py
```

**Funcionalidades:**
- **Conexión a BD**: Configurar conexión a diferentes tipos de bases de datos
- **Editor SQL**: Escribir y ejecutar consultas SQL con resaltado de sintaxis
- **Visualización**: Ver resultados en tablas formateadas
- **Exportación**: Guardar resultados en Excel, CSV o JSON
- **Diagramas**: Visualizar estructura de la base de datos
- **Plantillas**: Usar consultas SQL predefinidas

### Aplicación Web

1. **Iniciar el servidor**
   ```bash
   python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
   ```

2. Configura la conexión:
   - **Servidor**: NESTOR\NESTOR23 (preconfigurado)
   - **Autenticación**: Selecciona Windows o SQL Server
   - **Base de datos**: Selecciona de la lista disponible

3. Haz clic en "Conectar" para establecer la conexión

4. Utiliza el explorador de base de datos para navegar

5. Escribe y ejecuta consultas SQL en las pestañas del editor

6. **🆕 Generar Diagrama**: Usa el botón "🗺️ Diagrama" o menú Herramientas > Diagrama de BD
   - Visualiza tablas con sus columnas y tipos de datos
   - Muestra relaciones entre tablas (claves foráneas)
   - Exporta diagramas como imágenes PNG
   - Controles para mostrar/ocultar columnas y relaciones

## Ejemplos de Consultas

### Consultas SELECT
```sql
SELECT * FROM usuarios;
SELECT nombre, email FROM usuarios WHERE edad > 18;
```

### Consultas de Modificación
```sql
INSERT INTO usuarios (nombre, email, edad) VALUES ('Juan', 'juan@email.com', 25);
UPDATE usuarios SET edad = 26 WHERE nombre = 'Juan';
DELETE FROM usuarios WHERE edad < 18;
```

## Funcionalidades

- **Estado de conexión**: Muestra si estás conectado o desconectado
- **Manejo de errores**: Mensajes informativos para errores de conexión o consultas
- **Resultados tabulares**: Los resultados de SELECT se muestran en una tabla con scrollbars
- **Limpieza de consultas**: Botón para limpiar el área de texto

## Notas de Seguridad

- Nunca hardcodees credenciales en el código
- Usa conexiones seguras en entornos de producción
- Valida siempre las consultas SQL antes de ejecutarlas

## Solución de Problemas

### Error de conexión
- Verifica que MySQL Server esté ejecutándose
- Confirma que las credenciales sean correctas
- Asegúrate de que el puerto esté disponible

### Error de módulo no encontrado
- Instala las dependencias: `pip install mysql-connector-python`

### Error de permisos
- Verifica que el usuario tenga permisos para acceder a la base de datos