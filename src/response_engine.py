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
MAX_OUTPUT_TOKENS = 900
MAX_FRAGMENTS_PROMPT = 6
MAX_FRAGMENT_CHARS = 1200
MAX_TOTAL_CONTEXT_CHARS = 7000

PERFIL_RESPOSTA_CONFIG = {
    "estandard": {
        "to": "Resposta professional i clara.",
        "min_paraules": 220,
    },
    "completa": {
        "to": "Resposta completa, ben estructurada i amb més profunditat.",
        "min_paraules": 420,
    },
    "informe": {
        "to": "Informe extens i detallat amb cobertura màxima del context.",
        "min_paraules": 850,
    },
}


def preparar_fragments_amb_cites(fragments):
    fragments_amb_cites = []
    for index, fragment in enumerate(fragments, start=1):
        fragment_preparat = dict(fragment)
        fragment_preparat["citation_id"] = index
        fragments_amb_cites.append(fragment_preparat)
    return fragments_amb_cites


def limitar_fragments_per_prompt(
    fragments,
    max_fragments=MAX_FRAGMENTS_PROMPT,
    max_fragment_chars=MAX_FRAGMENT_CHARS,
    max_total_context_chars=MAX_TOTAL_CONTEXT_CHARS,
):
    fragments_limitats = []
    total_chars = 0

    for fragment in fragments:
        if len(fragments_limitats) >= max_fragments:
            break

        text_original = str(fragment.get("text", "") or "").strip()
        if not text_original:
            continue

        text_truncat = text_original[:max_fragment_chars]
        if len(text_original) > max_fragment_chars:
            text_truncat += "..."

        if total_chars + len(text_truncat) > max_total_context_chars:
            espai_rest = max_total_context_chars - total_chars
            if espai_rest < 200:
                break
            text_truncat = f"{text_truncat[:espai_rest].rstrip()}..."

        fragment_preparat = dict(fragment)
        fragment_preparat["text"] = text_truncat
        fragments_limitats.append(fragment_preparat)
        total_chars += len(text_truncat)

    return fragments_limitats


@lru_cache(maxsize=1)
def carregar_configuracio_model():
    # Prioritza variables de l'entorn/sessio i usa .env com a fallback.
    load_dotenv(ENV_FILE, override=False)

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


def configurar_api_keys(groq_api_key=None, openrouter_api_key=None):
    if groq_api_key is not None:
        if key := groq_api_key.strip():
            os.environ["GROQ_API_KEY"] = key
        else:
            os.environ.pop("GROQ_API_KEY", None)

    if openrouter_api_key is not None:
        if key := openrouter_api_key.strip():
            os.environ["OPENROUTER_API_KEY"] = key
        else:
            os.environ.pop("OPENROUTER_API_KEY", None)

    carregar_configuracio_model.cache_clear()
    crear_client_groq.cache_clear()


@lru_cache(maxsize=1)
def crear_client_groq(api_key):
    return Groq(api_key=api_key)


def generar_resposta_groq(prompt, api_key, model):
    client = crear_client_groq(api_key)
    resposta = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=MAX_OUTPUT_TOKENS,
    )
    return resposta.choices[0].message.content


def generar_resposta_openrouter(prompt, api_key, model):
    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": MAX_OUTPUT_TOKENS,
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

    blocs = [" ".join(frases[index:index + 2]) for index in range(0, len(frases), 2)]

    return "\n\n".join(blocs)


def detectar_intencio_resposta(pregunta):
    pregunta_normalitzada = pregunta.lower()

    if any(paraula in pregunta_normalitzada for paraula in ["informe", "resum executiu", "avalu", "avaluació", "diagn", "diagnòstic", "anàlisi completa", "document extens"]):
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
        citation_id = fragment.get("citation_id", "?")
        text = fragment.get("text", "").strip().replace("\n", " ")
        text = re.sub(r"\s+", " ", text)
        resums.append(f"- [{citation_id}] {font}: {text[:220]}")
    return "\n".join(resums)


def construir_context_amb_cites(fragments):
    blocs = []
    for fragment in fragments:
        citation_id = fragment.get("citation_id", "?")
        font = fragment.get("font", "Document")
        fragment_id = fragment.get("id", "sense-id")
        text = fragment.get("text", "").strip()
        blocs.append(
            f"[{citation_id}] Font: {font}\n"
            f"Fragment: {fragment_id}\n"
            f"Text: {text}"
        )
    return "\n\n".join(blocs)


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
Quan sigui útil, concreta conceptes, diferències, camps, estats o criteris rellevants.
Sigues exhaustiu: desenvolupa cada apartat important amb el màxim detall que el context permeti."""


def normalitzar_perfil_resposta(perfil_resposta):
    perfil = (perfil_resposta or "completa").strip().lower()
    return perfil if perfil in PERFIL_RESPOSTA_CONFIG else "completa"


def construir_instruccions_per_perfil(perfil_resposta):
    perfil = normalitzar_perfil_resposta(perfil_resposta)
    configuracio = PERFIL_RESPOSTA_CONFIG[perfil]

    instruccio_base = [
        f"Objectiu de qualitat: {configuracio['to']}",
        f"Extensió mínima orientativa: {configuracio['min_paraules']} paraules (si el context ho permet).",
        "Evita respostes telegràfiques: desenvolupa cada apartat amb detall operatiu.",
        "Quan sigui pertinent, incorpora seccions de: requisits, passos, validacions, errors habituals, riscos i recomanacions.",
        "No ometis matisos importants del context recuperat.",
    ]

    if perfil == "informe":
        instruccio_base.extend(
            [
                "Estructura la sortida com un informe formal, amb títol i apartats clars.",
                "Inclou diagnosi, anàlisi detallada, implicacions operatives i recomanacions accionables.",
                "Afegeix una secció final de conclusions prioritzades.",
            ]
        )

    return "\n".join(f"- {linia}" for linia in instruccio_base)


def construir_prompt(pregunta, fragments, perfil_resposta="completa"):
    intencio = detectar_intencio_resposta(pregunta)
    fragments = preparar_fragments_amb_cites(fragments)
    fragments = limitar_fragments_per_prompt(fragments)
    context = construir_context_amb_cites(fragments)
    context_resumit = resumir_context(fragments, limit=4)
    instruccions_intencio = construir_instruccions_per_intencio(intencio)
    instruccions_perfil = construir_instruccions_per_perfil(perfil_resposta)

    return f"""Ets un assistent expert en SIFECAT i en la gestió operativa i documental dels fons FEDER de Catalunya.
La teva feina és donar respostes d'alta qualitat, útils de veritat i adaptades a la necessitat concreta de l'usuari.

Normes de resposta:
- Respon sempre i només en català.
- Fes una resposta natural, professional i específica; parla de manera propera, amable i fàcil d'entendre.
- Escriu de tu a tu, amb calidesa i claredat, sense sonar burocràtic, fred ni administratiu.
- Prioritza que la persona entengui bé què ha de fer o què significa cada cosa, amb llenguatge planer quan sigui possible.
- No utilitzis frases buides com "segons el context proporcionat" o "aquí tens la resposta".
- No repeteixis la pregunta ni facis introduccions artificials.
- No inventis informació ni completis buits amb suposicions no justificades.
- Si el context és insuficient, digues exactament què falta o quin límit tens.
- Si la informació existeix al context, extreu-ne el màxim valor possible: passos, camps, estats, criteris, matisos, riscos, diferències, excepcions o implicacions.
- Personalitza el contingut a la consulta real de l'usuari; no responguis amb una plantilla rígida si no cal.
- Evita el to "canned AI". La resposta ha de semblar feta per un especialista que entén el domini.
- Dona la resposta més completa possible. Si hi ha diversos punts rellevants, cobreix-los tots.
- Desenvolupa el contingut amb profunditat: procediment, requisits, validacions, excepcions, dependències, errors habituals, impacte funcional i recomanacions pràctiques.
- No siguis breu si el context permet ampliar. Prioritza exhaustivitat i precisió per sobre de concisió.
- Quan el tema sigui complex, estructura la resposta amb apartats clars i detallats.
- Quan afirmis alguna cosa rellevant, cita explícitament el fragment d'origen amb referències com [1], [2] o [1][3].
- Si combines diverses fonts en una mateixa idea, cita totes les que pertoquin.
- Acaba sempre amb un apartat breu titulat "Fonts utilitzades" on enumeris només els identificadors citats a la resposta.

Qualitat esperada:
- Dona primer la resposta útil, no una introducció decorativa.
- Si la pregunta és operativa, estructura en passos clars.
- Si la pregunta és analítica, sintetitza i interpreta.
- Si la pregunta demana redacció, entrega un esborrany professional aprofitable.
- Si hi ha diverses opcions o casos, diferencia'ls de forma neta.
- Quan el context ho permeti, concreta noms d'elements de SIFECAT com operacions, certificacions N1/N2, contractes, transaccions, indicadors, controls o estats.
- Si el context conté prou informació, afegeix una secció final amb observacions útils, riscos, matisos o bones pràctiques.
- Si hi ha passos o punts importants, explica'ls de manera amable i entenedora, no rígida.

Instruccions específiques per a aquesta consulta:
{instruccions_intencio}

Perfil de resposta requerit:
{instruccions_perfil}

Resums dels fragments recuperats:
{context_resumit}

Context complet:
{context}

Pregunta de l'usuari:
{pregunta}

Genera una resposta final professional, propera, clara, exhaustiva, rica en contingut i directament útil."""

def generar_resposta(pregunta, fragments, perfil_resposta="completa"):
    if not fragments:
        return "No he trobat context rellevant per respondre amb prou fiabilitat."

    prompt = construir_prompt(pregunta, fragments, perfil_resposta=perfil_resposta)
    resposta = generar_resposta_model(prompt)
    resposta = resposta.replace("Segons el context proporcionat, ", "")
    resposta = resposta.replace("Segons el context, ", "")
    resposta = resposta.replace("D'acord amb el context proporcionat, ", "")
    return formatar_resposta(resposta)

