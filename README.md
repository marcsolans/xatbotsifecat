# SIFECAT Chatbot

Chatbot RAG para consultar documentación de SIFECAT y fondos FEDER de Catalunya usando Streamlit, FAISS, Sentence Transformers y Groq.

## Qué incluye

- Interfaz web de chat con Streamlit
- Procesado de PDFs a fragmentos de texto
- Índice vectorial con FAISS
- Recuperación de contexto relevante
- Generación de respuestas con Groq

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
- Una API key válida de Groq

## Instalación

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuración

1. Crea un archivo `.env` en la raíz del proyecto.
2. Añade tu clave:

```env
GROQ_API_KEY=your_real_groq_api_key
```

## Cómo ejecutar

1. Coloca tus PDFs en `data/raw/`.
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
streamlit run src/app.py
```

## Archivos que no se suben

El repositorio está preparado para no subir:

- `.env`
- `venv/`
- `data/raw/`
- `data/processed/`
- `data/index/`
- `logs/`

Esto evita publicar credenciales, documentos potencialmente sensibles y artefactos generados.

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