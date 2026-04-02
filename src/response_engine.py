import http.client
import json
import os
import re
from functools import lru_cache

from groq import Groq
from dotenv import load_dotenv

from settings import ENV_FILE

DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
DEFAULT_OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


@lru_cache(maxsize=1)
def carregar_configuracio_model():
    load_dotenv(ENV_FILE, override=True)

    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    groq_api_key = os.getenv("GROQ_API_KEY")

    if openrouter_api_key:
        return {
            "provider": "openrouter",
            "api_key": openrouter_api_key,
            "model": os.getenv("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL),
        }

    if groq_api_key:
        provider = "openrouter" if groq_api_key.startswith("sk-or-v1-") else "groq"
        model = os.getenv(
            "OPENROUTER_MODEL" if provider == "openrouter" else "GROQ_MODEL",
            DEFAULT_OPENROUTER_MODEL if provider == "openrouter" else DEFAULT_GROQ_MODEL,
        )
        return {
            "provider": provider,
            "api_key": groq_api_key,
            "model": model,
        }

    raise ValueError(
        "No s'ha trobat cap API key. Defineix GROQ_API_KEY o OPENROUTER_API_KEY al fitxer .env"
    )


@lru_cache(maxsize=1)
def crear_client_groq(api_key):
    return Groq(api_key=api_key)


def generar_resposta_groq(prompt, api_key, model):
    client = crear_client_groq(api_key)
    resposta = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1400,
    )
    return resposta.choices[0].message.content


def generar_resposta_openrouter(prompt, api_key, model):
    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 1400,
        }
    )
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "Chatbot SIFECAT",
        "User-Agent": "chatbot-sifecat/1.0",
    }

    conn = http.client.HTTPSConnection("openrouter.ai")
    try:
        conn.request("POST", "/api/v1/chat/completions", body=payload, headers=headers)
        response = conn.getresponse()
        raw = response.read().decode("utf-8", errors="replace")
    finally:
        conn.close()

    if response.status >= 400:
        raise RuntimeError(f"Error OpenRouter: {raw}")

    data = json.loads(raw)

    return data["choices"][0]["message"]["content"]


def generar_resposta_model(prompt):
    configuracio = carregar_configuracio_model()
    if configuracio["provider"] == "openrouter":
        return generar_resposta_openrouter(prompt, configuracio["api_key"], configuracio["model"])

    return generar_resposta_groq(prompt, configuracio["api_key"], configuracio["model"])


def formatar_resposta(resposta):
    resposta = resposta.strip()
    if not resposta:
        return resposta

    resposta = re.sub(r"\n{3,}", "\n\n", resposta)
    resposta = re.sub(r"[ \t]+\n", "\n", resposta)
    resposta = re.sub(r"\n[ \t]+", "\n", resposta)

    if "\n" in resposta:
        return resposta.strip()

    if len(resposta) < 220:
        return resposta

    frases = re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ú0-9])", resposta)
    frases = [frase.strip() for frase in frases if frase.strip()]

    if len(frases) <= 2:
        return resposta

    blocs = []
    for index in range(0, len(frases), 2):
        blocs.append(" ".join(frases[index:index + 2]))

    return "\n\n".join(blocs)


def detectar_intencio_resposta(pregunta):
    pregunta_normalitzada = pregunta.lower()

    if any(paraula in pregunta_normalitzada for paraula in ["informe", "resum executiu", "avalu", "avaluació", "diagn", "diagnòstic"]):
        return "analitica"
    if any(paraula in pregunta_normalitzada for paraula in ["redacta", "escriu", "prepara", "proposa", "enquesta", "correu", "email"]):
        return "redaccio"
    if any(paraula in pregunta_normalitzada for paraula in ["com", "passos", "procediment", "tramitar", "fer", "validar", "presentar"]):
        return "procedimental"
    return "explicativa"


def resumir_context(fragments, limit=5):
    resums = []
    for fragment in fragments[:limit]:
        font = fragment.get("font", "Document")
        text = fragment.get("text", "").strip().replace("\n", " ")
        text = re.sub(r"\s+", " ", text)
        resums.append(f"- {font}: {text[:360]}")
    return "\n".join(resums)


def construir_instruccions_per_intencio(intencio):
    if intencio == "procedimental":
        return """Prioritza una resposta operativa i accionable.
Obre amb la resposta directa.
Després explica el procediment en passos concrets i ordenats.
Si al context apareixen validacions, estats, pantalles, camps o requisits, incorpora'ls explícitament.
Si detectes condicions prèvies o excepcions, separa-les en un apartat breu."""

    if intencio == "redaccio":
        return """Prioritza un resultat útil per treballar immediatament.
Si la pregunta demana redactar o preparar un document, entrega un esborrany professional, natural i específic.
No facis una introducció meta sobre el context; entra directament en el contingut.
Mantén el text clar, formal i adaptat a l'entorn administratiu o funcional de SIFECAT."""

    if intencio == "analitica":
        return """Prioritza anàlisi i interpretació.
Identifica patrons, punts crítics, dependències, riscos o implicacions si es desprenen del context.
No et limitis a repetir fragments: sintetitza'ls i extreu conclusions útils.
Si hi ha límits d'informació, indica exactament què es pot concloure i què no."""

    return """Prioritza una resposta experta, clara i concreta.
Explica el que realment diu el context, evitant repetir frases genèriques.
Quan sigui útil, concreta conceptes, diferències, camps, estats o criteris rellevants."""


def construir_prompt(pregunta, fragments):
    intencio = detectar_intencio_resposta(pregunta)
    context = "\n\n".join([f["text"] for f in fragments])
    context_resumit = resumir_context(fragments)
    instruccions_intencio = construir_instruccions_per_intencio(intencio)

    return f"""Ets un assistent expert en SIFECAT i en la gestió operativa i documental dels fons FEDER de Catalunya.
La teva feina és donar respostes d'alta qualitat, útils de veritat i adaptades a la necessitat concreta de l'usuari.

Normes de resposta:
- Respon sempre i només en català.
- Fes una resposta natural, professional i específica; no sonis com un chatbot genèric.
- No utilitzis frases buides com "segons el context proporcionat" o "aquí tens la resposta".
- No repeteixis la pregunta ni facis introduccions artificials.
- No inventis informació ni completis buits amb suposicions no justificades.
- Si el context és insuficient, digues exactament què falta o quin límit tens.
- Si la informació existeix al context, extreu-ne el màxim valor possible: passos, camps, estats, criteris, matisos, riscos, diferències, excepcions o implicacions.
- Personalitza el contingut a la consulta real de l'usuari; no responguis amb una plantilla rígida si no cal.
- Evita el to "canned AI". La resposta ha de semblar feta per un especialista que entén el domini.

Qualitat esperada:
- Dona primer la resposta útil, no una introducció decorativa.
- Si la pregunta és operativa, estructura en passos clars.
- Si la pregunta és analítica, sintetitza i interpreta.
- Si la pregunta demana redacció, entrega un esborrany professional aprofitable.
- Si hi ha diverses opcions o casos, diferencia'ls de forma neta.
- Quan el context ho permeti, concreta noms d'elements de SIFECAT com operacions, certificacions N1/N2, contractes, transaccions, indicadors, controls o estats.

Instruccions específiques per a aquesta consulta:
{instruccions_intencio}

Resums dels fragments recuperats:
{context_resumit}

Context complet:
{context}

Pregunta de l'usuari:
{pregunta}

Genera una resposta final professional, clara, rica en contingut i directament útil."""

def generar_resposta(pregunta, fragments):
    if not fragments:
        return "No he trobat context rellevant per respondre amb prou fiabilitat."

    prompt = construir_prompt(pregunta, fragments)
    resposta = generar_resposta_model(prompt)
    resposta = resposta.replace("Segons el context proporcionat, ", "")
    resposta = resposta.replace("Segons el context, ", "")
    resposta = resposta.replace("D'acord amb el context proporcionat, ", "")
    return formatar_resposta(resposta)

