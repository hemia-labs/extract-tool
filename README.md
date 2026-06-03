# Hemia Extract API

Servicio ligero de extraccion de texto y OCR.

## Stack

- FastAPI + Uvicorn
- PyMuPDF para PDFs
- python-docx para DOCX
- openpyxl para XLSX
- Pillow + Tesseract OCR para imagenes y PDFs escaneados
- Docker

## Ejecutar localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Ejecutar con Docker

```bash
docker compose up --build
```

Con Docker, el host expone la API en `http://localhost:8001` para no chocar con Coolify. Dentro del contenedor FastAPI sigue escuchando en `8000`.

## Deploy con GitHub Actions

El workflow [.github/workflows/deploy.yml](.github/workflows/deploy.yml) se ejecuta en cada push a `main`.

Flujo:

- instala dependencias Python
- valida imports con `python -m compileall app`
- conecta a Tailscale
- sube `app`, `Dockerfile`, `docker-compose.yml`, `requirements.txt` y `README.md` al server
- crea `.env` en el server
- levanta el servicio con `docker compose up -d --build --remove-orphans`

Secrets requeridos:

| Secret | Descripcion |
|---|---|
| `TAILSCALE_OAUTH_CLIENT_ID` | OAuth Client ID de Tailscale |
| `TAILSCALE_OAUTH_SECRET` | OAuth Client secret de Tailscale |
| `SSH_HOST` | Host/IP del server |
| `SSH_USER` | Usuario SSH |
| `SSH_PORT` | Puerto SSH |
| `SSH_PRIVATE_KEY` | Llave privada SSH |
| `APP_PATH` | Ruta destino en el server |

El OAuth client de Tailscale debe poder crear nodos efimeros con el tag `tag:ci`. Ese tag debe existir en tu tailnet.

Secrets opcionales:

| Secret | Default |
|---|---|
| `MAX_FILE_SIZE_MB` | `25` |
| `MAX_PDF_PAGES` | `50` |
| `MAX_IMAGE_PIXELS` | `20000000` |
| `OCR_DEFAULT_LANGUAGE` | `spa+eng` |
| `REQUEST_TIMEOUT_SECONDS` | `60` |

## Endpoints

- `GET /health`
- `GET /v1/formats`
- `POST /v1/extract`

## Health check

```http
GET /health
```

### Respuesta `200`

```json
{
  "status": "ok"
}
```

## Formatos soportados

```http
GET /v1/formats
```

### Respuesta `200`

```json
{
  "formats": [
    "csv",
    "docx",
    "jpeg",
    "jpg",
    "md",
    "pdf",
    "png",
    "tiff",
    "txt",
    "webp",
    "xlsx"
  ]
}
```

## Extraer texto

```http
POST /v1/extract
Content-Type: multipart/form-data
```

### Form data de entrada

| Campo | Tipo | Requerido | Default | Valores permitidos | Descripcion |
|---|---|---:|---|---|---|
| `file` | File | Si | - | `pdf`, `txt`, `md`, `docx`, `xlsx`, `csv`, `jpg`, `jpeg`, `png`, `webp`, `tiff` | Archivo a procesar |
| `ocr` | string | No | `auto` | `auto`, `true`, `false` | Modo OCR |
| `language` | string | No | `spa+eng` | Cualquier idioma de Tesseract instalado en el runtime | Idioma para OCR |
| `output` | string | No | `text` | `text`, `pages`, `markdown` | Estilo de salida preferido |

### Modos OCR

| Valor | Comportamiento |
|---|---|
| `auto` | Usa extraccion nativa primero. Ejecuta OCR solo cuando hace falta. |
| `true` | Fuerza OCR para PDFs/imagenes cuando aplica. |
| `false` | Desactiva OCR para PDFs. Las imagenes aun requieren OCR. |

### Respuesta `200`

```json
{
  "success": true,
  "filename": "documento.pdf",
  "mimeType": "application/pdf",
  "extension": "pdf",
  "text": "Texto completo extraido...",
  "pages": [
    {
      "page": 1,
      "text": "Texto de la pagina 1...",
      "confidence": null
    }
  ],
  "metadata": {
    "ocrUsed": false,
    "language": "spa",
    "characters": 8421,
    "pages": 1,
    "processingTimeMs": 384
  }
}
```

### Contrato de respuesta

| Campo | Tipo | Descripcion |
|---|---|---|
| `success` | boolean | Siempre `true` cuando la extraccion fue exitosa |
| `filename` | string | Nombre sanitizado del archivo cargado |
| `mimeType` | string | Tipo MIME detectado |
| `extension` | string | Extension detectada del archivo |
| `text` | string | Texto completo extraido y normalizado |
| `pages` | array | Resultado por pagina o seccion |
| `metadata` | object | Metadatos de extraccion |

### Objeto page

| Campo | Tipo | Descripcion |
|---|---|---|
| `page` | integer | Numero de pagina/seccion empezando en `1` |
| `text` | string | Texto extraido de esa pagina/seccion |
| `confidence` | number o null | Confianza OCR cuando esta disponible |

### Objeto metadata

| Campo | Tipo | Descripcion |
|---|---|---|
| `ocrUsed` | boolean | Indica si se uso OCR |
| `language` | string | Idioma OCR usado en el request |
| `characters` | integer | Numero de caracteres en `text` |
| `pages` | integer | Numero de paginas/secciones devueltas |
| `processingTimeMs` | integer | Tiempo de extraccion en milisegundos |

## Ejemplos de uso

### Extraer PDF con OCR automatico

```bash
curl -X POST http://localhost:8001/v1/extract \
  -F "file=@documento.pdf" \
  -F "ocr=auto" \
  -F "language=spa" \
  -F "output=pages"
```

### Forzar OCR en un PDF escaneado

```bash
curl -X POST http://localhost:8001/v1/extract \
  -F "file=@contrato-escaneado.pdf" \
  -F "ocr=true" \
  -F "language=spa+eng"
```

### Extraer texto plano

```bash
curl -X POST http://localhost:8001/v1/extract \
  -F "file=@notas.txt"
```

### Extraer archivo Markdown

```bash
curl -X POST http://localhost:8001/v1/extract \
  -F "file=@documento.md" \
  -F "output=markdown"
```

### Extraer DOCX

```bash
curl -X POST http://localhost:8001/v1/extract \
  -F "file=@reporte.docx"
```

### Extraer XLSX como tablas Markdown

```bash
curl -X POST http://localhost:8001/v1/extract \
  -F "file=@ventas.xlsx" \
  -F "output=markdown"
```

### Extraer CSV como tabla Markdown

```bash
curl -X POST http://localhost:8001/v1/extract \
  -F "file=@clientes.csv" \
  -F "output=markdown"
```

### OCR de imagen

```bash
curl -X POST http://localhost:8001/v1/extract \
  -F "file=@factura.png" \
  -F "language=spa"
```

## Respuestas de error

Los errores usan el envelope default de FastAPI:

```json
{
  "detail": "Unsupported file extension: zip"
}
```

Estados comunes:

| Estado | Razon |
|---:|---|
| `413` | El archivo excede el limite de tamano o el limite de paginas PDF |
| `415` | Extension no soportada o MIME no coincide |
| `422` | Fallo de extraccion u OCR |

## Limites

Los valores default se pueden cambiar con variables de entorno.

| Variable env | Default |
|---|---|
| `MAX_FILE_SIZE_MB` | `25` |
| `MAX_PDF_PAGES` | `50` |
| `MAX_IMAGE_PIXELS` | `20000000` |
| `OCR_DEFAULT_LANGUAGE` | `spa+eng` |
| `REQUEST_TIMEOUT_SECONDS` | `60` |
