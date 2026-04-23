# SIFECAT Chatbot

Chatbot RAG para consultar documentación de SIFECAT y fondos FEDER de Catalunya usando Streamlit, FAISS, Sentence Transformers y un modelo LLM servido por Groq u OpenRouter.

## Qué incluye

- Interfaz web de chat con Streamlit
- Subida de documentos desde la propia app
- Lectura en voz alta de respuestas desde el navegador
- Procesado de PDFs a fragmentos de texto
- Índice vectorial con FAISS
- Recuperación de contexto relevante
- Generación de respuestas con Groq u OpenRouter
- Respuestas con citas explícitas a los fragmentos utilizados

## Estructura del proyecto

```text
src/
  app.py
  ingest.py
  response_engine.py
  search_engine.py
data/
  raw/
  processed/
  index/
logs/
```

## Requisitos

- Python 3.9+
- Una API key válida de Groq o OpenRouter

## Instalación

```bash
python -m venv venv
# Windows PowerShell
.\venv\Scripts\Activate.ps1
# macOS / Linux
# source venv/bin/activate
pip install -r requirements.txt
```

## Configuración

1. Crea un archivo `.env` en la raíz del proyecto.
2. Añade tu clave:

```env
GROQ_API_KEY=your_real_groq_api_key
```

Si prefieres OpenRouter, usa:

```env
OPENROUTER_API_KEY=your_real_openrouter_api_key
```

También puedes definir `GROQ_API_KEY` o `OPENROUTER_API_KEY` como variable de entorno en tu plataforma de despliegue.

Opcionalmente puedes ajustar el modelo con `GROQ_MODEL` o `OPENROUTER_MODEL`.

## Cómo ejecutar

1. Coloca tus documentos en `data/raw/`.
  Se admiten `PDF`, `TXT` y `MD`.
2. Genera los fragmentos:

```bash
python src/ingest.py
```

3. Construye el índice:

```bash
python src/search_engine.py
```

4. Lanza la aplicación:

```bash
python -m streamlit run src/app.py
```

Los scripts resuelven las rutas desde la raíz del proyecto, así que no dependen del directorio actual desde el que los lances.

## Notas operativas

- Si `data/raw/` no existe, créala antes de ejecutar la ingesta.
- `data/processed/` y `data/index/` se crean automáticamente cuando corresponde.
- Si cambias los documentos, vuelve a ejecutar `python src/ingest.py` y `python src/search_engine.py` para regenerar el índice.
- También puedes subir documentos directamente desde el panel inferior de la app (junto al área de consulta) para que se procesen e indexen sin salir de Streamlit.
- La lectura en voz alta usa la API de voz del navegador. Se recomienda abrir la app en Edge o Chrome para una compatibilidad más estable.
- La respuesta muestra referencias explícitas y, debajo, un bloque desplegable con los fragmentos recuperados y su procedencia.

## Archivos que no se suben

El repositorio está preparado para no subir:

- `.env`
- `venv/`
- `data/raw/`
- `logs/`

Esto evita publicar credenciales y documentos potencialmente sensibles. En cambio, `data/processed/` y `data/index/` sí pueden versionarse para desplegar la app sin reconstruir el índice en el servidor.

## Compartir la app

La forma más simple es desplegar el repositorio en Streamlit Community Cloud.

1. Sube a GitHub también `data/processed/` y `data/index/`.
2. Entra en Streamlit Community Cloud y crea una app conectando este repositorio.
3. Indica como archivo principal `src/app.py`.
4. Añade `GROQ_API_KEY` o `OPENROUTER_API_KEY` en los secretos o variables de entorno del servicio.

Al desplegar, obtendrás una URL pública sin necesidad de comprar un dominio. El dominio propio solo tiene sentido más adelante si quieres una dirección personalizada.

## Publicar en GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <URL_DE_TU_REPO>
git push -u origin main
```

## Nota

Si quieres versionar los PDFs de ejemplo o el índice generado, tendrás que ajustar `.gitignore` antes de hacer `git add`.