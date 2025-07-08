# 🔧 Solución de Problemas en Render

## ❌ Error: Pandas + Python 3.13 Incompatibilidad

### Problema
```
Pandas/_libs/tslibs/base.cpython-313-x86_64-linux-gnu.so.p/pandas/_libs/tslibs/base.pyx.c:5397:27: error: muy pocos argumentos para la función '_PyLong_AsByteAr
```

### ✅ Solución Aplicada

1. **Actualizado `requirements.txt`**:
   - ✅ `pandas==2.2.0` (compatible con Python 3.13)
   - ✅ `numpy==1.26.3` (requerido para pandas)
   - ✅ Removidas dependencias de escritorio innecesarias

2. **Creado `runtime.txt`**:
   ```
   python-3.11.7
   ```
   - Especifica versión estable de Python
   - Evita problemas de compatibilidad

### 🚀 Pasos para Redeploy

1. **Commit cambios**:
   ```bash
   git add requirements.txt runtime.txt
   git commit -m "Fix pandas compatibility for Render deployment"
   git push
   ```

2. **Manual Deploy en Render**:
   - Ir a tu servicio en Render
   - "Manual Deploy" → "Deploy Latest Commit"
   - Esperar 3-5 minutos

## 🛠️ Otros Errores Comunes

### Error: "Module not found"
**Solución**: Verificar que todas las dependencias estén en `requirements.txt`

### Error: "Build failed"
**Solución**: 
1. Revisar logs completos en Render
2. Verificar sintaxis en `requirements.txt`
3. Confirmar que `runtime.txt` especifica versión válida

### Error: "Database connection failed"
**Solución**:
1. Verificar `DATABASE_URL` en Environment Variables
2. Confirmar que el servicio de BD esté activo
3. Revisar formato de URL de conexión

### Error: "Port binding failed"
**Solución**: Confirmar que `api.py` use:
```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
```

## 📋 Checklist Pre-Deploy

- [ ] `requirements.txt` actualizado
- [ ] `runtime.txt` especifica Python 3.11.x
- [ ] Variables de entorno configuradas
- [ ] Código commiteado y pusheado
- [ ] Build command correcto: `pip install -r requirements.txt`
- [ ] Start command correcto: `python api.py`

## 🔍 Debugging Tips

### Ver Logs en Tiempo Real
1. Render Dashboard → Tu servicio
2. "Logs" tab
3. Filtrar por "Error" o "Warning"

### Probar Localmente
```bash
# Instalar dependencias exactas
pip install -r requirements.txt

# Probar aplicación
python api.py
```

### Verificar Compatibilidad
```bash
# Verificar versión de Python
python --version

# Verificar pandas
python -c "import pandas; print(pandas.__version__)"
```

## 📞 Recursos Adicionales

- **Render Docs**: https://render.com/docs
- **Python Compatibility**: https://devguide.python.org/versions/
- **Pandas Releases**: https://pandas.pydata.org/docs/whatsnew/

---

¡Con estos cambios tu aplicación debería deployar correctamente! 🚀