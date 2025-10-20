# MAP Violation Email Generator

Sistema automatizado para detectar violaciones de MAP (Minimum Advertised Price) y generar emails personalizados listos para enviar.

## Descripción

Este proyecto lee archivos Excel con datos de precios, identifica vendedores que están violando las políticas de precio mínimo anunciado, y genera emails individuales listos para copiar y pegar en Outlook.

## Características

- ✅ Lectura automática de archivos Excel con datos de precios
- ✅ Detección de violaciones basada en diferencia de precios
- ✅ Agrupación de múltiples violaciones por vendedor
- ✅ Generación de emails personalizados (singular/plural)
- ✅ Formato listo para copiar/pegar en Outlook
- ✅ Archivos de salida individuales por vendedor

## Requisitos

- Python 3.x
- pandas
- openpyxl

## Instalación

```bash
pip install pandas openpyxl
```

## Uso

1. Coloca tu archivo Excel en la carpeta del proyecto
2. Asegúrate de tener el template de email (`MAP-mail-template`)
3. Ejecuta el script principal:

```bash
python generate_emails.py
```

4. Los emails generados estarán en la carpeta `output/`
5. Copia y pega cada email en Outlook

## Estructura del Proyecto

```
map-dimplex/
├── generate_emails.py          # Script principal
├── MAP-mail-template           # Template del email
├── output/                     # Emails generados (ignorado por git)
├── .gitignore                  # Archivos a ignorar
└── README.md                   # Este archivo
```

## Notas

- Los archivos Excel y la carpeta output/ están excluidos del repositorio por contener información confidencial
- El sistema NO se conecta a Outlook automáticamente (por restricciones corporativas)
- El usuario debe copiar y pegar manualmente cada email

## Configuración

Para usar este proyecto:

1. Añade tu archivo Excel con las siguientes columnas mínimas:
   - `sellers`: Nombre del vendedor
   - `prices`: Precio actual
   - `U.S. MAP`: Precio mínimo permitido
   - `price_difference`: Diferencia (negativo = violación)
   - `Description`: Descripción del producto
   - `SAP Material`: Código SKU
   - `seller_links`: Links a los productos

2. Personaliza el template `MAP-mail-template` según tus necesidades

## Licencia

Uso interno de la empresa.
