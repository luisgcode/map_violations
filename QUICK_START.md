# MAP Violations Email Generator

## 🚀 Inicio Rápido

Para usar este proyecto **mañana y siempre**, simplemente ejecuta:

```powershell
.\start.ps1
```

## ✅ ¿Qué hace el script `start.ps1`?

1. **Activa automáticamente** el entorno virtual dedicado
2. **Verifica** que todas las dependencias estén instaladas
3. **Inicia** la aplicación Flask
4. **Abre** la aplicación en `http://localhost:5000`

## 📁 Estructura del Proyecto

```
map_violations/
├── .venv/              # Entorno virtual (creado automáticamente)
├── start.ps1           # ⭐ SCRIPT DE INICIO RÁPIDO
├── app_flask.py        # Aplicación principal
├── requirements.txt    # Dependencias
├── templates/          # Plantillas HTML
├── uploads/           # Archivos subidos
└── output/            # Emails generados
```

## 🔧 Solución de Problemas

Si `.\start.ps1` no funciona:

1. **Problema de políticas**: Ejecuta una vez:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
   ```

2. **Reinstalación completa** (si algo se rompió):
   ```powershell
   .\setup.ps1
   ```

## 🎯 Uso Diario

1. Abre PowerShell en la carpeta del proyecto
2. Ejecuta: `.\start.ps1`
3. Ve a `http://localhost:5000` en tu navegador
4. Sube tu archivo Excel con violaciones MAP
5. Copia los emails generados a Outlook

## ⚡ Ventajas de esta Configuración

- ✅ **Entorno aislado**: No interfiere con otros proyectos Python
- ✅ **Inicio instantáneo**: Un solo comando para ejecutar todo
- ✅ **Persistente**: Funciona siempre, incluso después de reiniciar
- ✅ **Auto-reparación**: Detecta y soluciona problemas automáticamente