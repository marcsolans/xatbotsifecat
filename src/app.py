import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

from ingest import SUPPORTED_EXTENSIONS, processar_documents
from response_engine import generar_resposta
from search_engine import cercar, construir_index
from settings import INDEX_DIR, PROCESSED_DIR, RAW_DIR

DEFAULT_PERFIL_RESPOSTA = "informe"
DEFAULT_TOP_K = 12

PREGUNTES_PER_BLOC = {
    "Operacions": [
        "Quina informació es necessita per donar d'alta una operació?",
        "Com es busquen, editen i visualitzen operacions a SIFECAT?",
        "Quins passos s'han de seguir per validar una operació?",
    ],
    "Certificació": [
        "Com es fa la certificació de la despesa a SIFECAT?",
        "Quines diferències hi ha entre certificació de primer nivell i N2?",
        "Quins indicadors de productivitat intervenen en la certificació?",
    ],
    "ICPECTs": [
        "Què són els ICPECTs i com es registren?",
        "Com es busquen, editen i visualitzen els ICPECTs?",
    ],
    "Gestió administrativa": [
        "Com es gestionen els contractes i les transaccions a SIFECAT?",
        "Quines dades mestres es gestionen dins del sistema?",
    ],
}

OBJECTIUS_USUARI = {
    "Necessito orientar-me": [
        "Què puc consultar dins d'aquest assistent?",
        "Quins tipus de tràmits o processos cobreix SIFECAT?",
    ],
    "Vull donar d'alta una operació": [
        "Quina informació es necessita per donar d'alta una operació?",
        "Com es busquen, editen i visualitzen operacions a SIFECAT?",
    ],
    "Vull certificar despesa": [
        "Com es fa la certificació de la despesa a SIFECAT?",
        "Quines diferències hi ha entre certificació de primer nivell i N2?",
    ],
    "Vull consultar indicadors o ICPECTs": [
        "Què són els ICPECTs i com es registren?",
        "Com es busquen, editen i visualitzen els ICPECTs?",
    ],
    "Vull validar o revisar una operació": [
        "Quins passos s'han de seguir per validar una operació?",
        "Quins errors o comprovacions acostumen a aparèixer en la validació?",
    ],
}

EXEMPLES_PREGUNTES = [
    pregunta
    for preguntes_bloc in PREGUNTES_PER_BLOC.values()
    for pregunta in preguntes_bloc[:1]
]

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=DM+Mono:wght@400;500&display=swap');

:root {
    --sifecat-ink: #111827;
    --sifecat-muted: #4b5563;
    --sifecat-soft: #6b7280;
    --sifecat-line: rgba(17, 24, 39, 0.12);
    --sifecat-surface: #ffffff;
    --sifecat-shadow: 0 18px 40px rgba(17, 24, 39, 0.08);
    --sifecat-shadow-soft: 0 10px 24px rgba(17, 24, 39, 0.06);
    --sifecat-accent: #0f172a;
    --sifecat-accent-soft: rgba(15, 23, 42, 0.06);
}

.stApp {
    background:
        radial-gradient(circle at 8% 5%, rgba(226, 232, 240, 0.34), transparent 34%),
        radial-gradient(circle at 86% 15%, rgba(241, 245, 249, 0.68), transparent 28%),
        linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    color: var(--sifecat-ink);
    font-family: 'Plus Jakarta Sans', sans-serif;
}

.stApp > header {
    background: transparent;
}

.stApp [data-testid="block-container"] {
    max-width: 980px;
    margin: 0 auto;
    padding-top: 1.1rem;
    padding-bottom: 1.75rem;
    padding-left: 1.15rem;
    padding-right: 1.15rem;
}

[data-testid="stSidebar"] {
    background: #f8fafc;
    border-right: 1px solid rgba(15, 23, 42, 0.08);
    backdrop-filter: none;
}

[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    padding-top: 0.8rem;
    padding-left: 0.15rem;
    padding-right: 0.15rem;
}

[data-testid="stSidebar"] * {
    color: var(--sifecat-ink);
}

.stMarkdown,
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label {
    text-align: left;
}

.sifecat-shell {
    padding: 0.1rem 0 1rem 0;
}

.sifecat-hero {
    background: #ffffff;
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 20px;
    padding: 1.45rem 1.4rem 1.2rem 1.4rem;
    box-shadow: var(--sifecat-shadow);
    margin-bottom: 0.7rem;
}

.sifecat-kicker {
    display: inline-block;
    font-size: 0.72rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    font-weight: 700;
    color: var(--sifecat-ink);
    background: rgba(255, 255, 255, 0.74);
    border: 1px solid rgba(16, 17, 20, 0.06);
    padding: 0.4rem 0.68rem;
    border-radius: 999px;
    margin-bottom: 1rem;
}

.sifecat-hero h1 {
    font-size: 2.35rem;
    line-height: 1.05;
    letter-spacing: -0.03em;
    margin: 0;
    color: var(--sifecat-ink);
    white-space: normal;
    text-align: left;
}

.sifecat-hero p {
    margin: 0.65rem 0 0 0;
    color: var(--sifecat-muted);
    max-width: 60rem;
    font-size: 0.97rem;
    line-height: 1.58;
    text-align: left;
}

.sifecat-empty {
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 16px;
    padding: 0.9rem 1rem;
    margin: 0.3rem 0 0.85rem 0;
    box-shadow: var(--sifecat-shadow-soft);
}

.sifecat-empty strong {
    color: var(--sifecat-ink);
    font-size: 1rem;
}

.sifecat-empty p {
    color: var(--sifecat-muted);
    margin: 0.4rem 0 0 0;
    line-height: 1.65;
}

.sifecat-suggestions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    margin-top: 0.75rem;
    width: 100%;
    max-width: 100%;
}

.sifecat-loading {
    display: flex;
    align-items: center;
    gap: 0.9rem;
    padding: 0.3rem 0;
    color: var(--sifecat-muted);
    font-size: 0.88rem;
    letter-spacing: -0.01em;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

.sifecat-loading-dots {
    display: flex;
    gap: 5px;
    align-items: center;
}

.sifecat-loading-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: var(--sifecat-ink);
    opacity: 0.22;
    animation: sifecat-bounce 1.2s ease-in-out infinite;
}

.sifecat-loading-dot:nth-child(1) { animation-delay: 0s; }
.sifecat-loading-dot:nth-child(2) { animation-delay: 0.18s; }
.sifecat-loading-dot:nth-child(3) { animation-delay: 0.36s; }

@keyframes sifecat-bounce {
    0%, 55%, 100% { opacity: 0.22; transform: translateY(0); }
    28% { opacity: 0.85; transform: translateY(-5px); }
}

.sifecat-source {
    border-left: 2px solid rgba(16, 17, 20, 0.10);
    padding-left: 0.85rem;
    margin-bottom: 0.9rem;
}

.sifecat-source code {
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
    color: var(--sifecat-soft);
}

.sifecat-bottom-tools {
    margin: 0.55rem 0 0.65rem 0;
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 14px;
    padding: 0.95rem 1rem 0.5rem 1rem;
    box-shadow: var(--sifecat-shadow-soft);
}

.sifecat-bottom-tools p {
    margin: 0;
    color: var(--sifecat-muted);
    font-size: 0.9rem;
    line-height: 1.5;
}

[data-testid="stChatMessage"] {
    background: transparent;
    padding: 0;
}

[data-testid="stChatMessage"] [data-testid="chatAvatarIcon-user"] {
    background: transparent;
    color: transparent;
}

[data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] {
    background: transparent;
    color: transparent;
    border: none;
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li {
    line-height: 1.72;
    color: var(--sifecat-ink);
}

[data-testid="stChatMessage"] {
    margin-bottom: 0.55rem;
}

[data-testid="stChatMessageContent"] {
    background: #ffffff;
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 14px;
    padding: 0.95rem 1rem;
    box-shadow: none;
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] {
    background: #0f172a;
    border: 1px solid #0f172a;
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] p {
    color: #f8fafc;
}

[data-testid="stChatInput"] {
    background: transparent;
}

[data-testid="stChatInput"] > div {
    border-radius: 14px !important;
    border: 1px solid rgba(15, 23, 42, 0.14) !important;
    background: #ffffff !important;
    box-shadow: none !important;
}

[data-testid="stChatInput"] textarea {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    color: var(--sifecat-ink) !important;
}

[data-testid="stSidebar"] .stButton > button {
    justify-content: flex-start;
    text-align: left;
    padding-left: 1rem;
}

.sifecat-suggestions + div .stButton > button,
.sifecat-suggestions .stButton > button {
    width: 100%;
}

[data-testid="stSidebar"] [role="radiogroup"] {
    align-items: flex-start;
}

.stButton > button,
[data-testid="stBaseButton-secondary"] {
    border-radius: 10px;
    border: 1px solid rgba(15, 23, 42, 0.14);
    background: #ffffff;
    color: var(--sifecat-ink);
    font-weight: 600;
    box-shadow: none;
}

.sifecat-suggestions .stButton > button {
    min-height: auto;
    border-radius: 999px;
    justify-content: center;
    text-align: center;
    padding: 0.45rem 0.85rem;
    background: #ffffff;
    border: 1px solid rgba(15, 23, 42, 0.12);
    box-shadow: none;
    font-size: 0.88rem;
    line-height: 1.2;
}

.sifecat-suggestions .stButton > button:hover {
    transform: none;
    border-color: rgba(15, 23, 42, 0.28);
}

.stButton > button:hover,
[data-testid="stBaseButton-secondary"]:hover {
    border-color: rgba(16, 17, 20, 0.14);
    background: rgba(255, 255, 255, 0.96);
    color: var(--sifecat-ink);
}

[data-testid="stSidebar"] .stButton > button,
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
    background: #ffffff;
    color: var(--sifecat-ink);
    border: 1px solid rgba(15, 23, 42, 0.12);
    box-shadow: none;
}

@media (max-width: 900px) {
    .stApp [data-testid="block-container"] {
        padding-top: 0.8rem;
        padding-left: 0.85rem;
        padding-right: 0.85rem;
    }

    .sifecat-hero h1 {
        font-size: 1.9rem;
    }

    .sifecat-hero {
        padding: 1.2rem 1rem 1rem 1rem;
    }

    .sifecat-suggestions {
        gap: 0.45rem;
    }
}
</style>
"""


def inicialitzar_estat():
    if "missatges" not in st.session_state:
        st.session_state.missatges = []
    if "pregunta_preparada" not in st.session_state:
        st.session_state.pregunta_preparada = None
    if "objectiu_actual" not in st.session_state:
        st.session_state.objectiu_actual = list(OBJECTIUS_USUARI.keys())[0]
    if "historial" not in st.session_state:
        st.session_state.historial = []
    if "upload_key" not in st.session_state:
        st.session_state.upload_key = 0


def preparar_pregunta(pregunta):
    st.session_state.pregunta_preparada = pregunta


def guardar_documents_pujats(documents):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    guardats = []
    for document in documents:
        desti = RAW_DIR / Path(document.name).name
        desti.write_bytes(document.getbuffer())
        guardats.append(desti.name)
    return guardats


def actualitzar_base_documental(documents):
    guardats = guardar_documents_pujats(documents)
    processar_documents(RAW_DIR, PROCESSED_DIR)
    construir_index(PROCESSED_DIR / "chunks.json", INDEX_DIR)
    st.session_state.upload_key += 1
    return guardats


def parsejar_entrada_chat(entrada_chat):
    if entrada_chat is None:
        return "", []

    if isinstance(entrada_chat, str):
        return entrada_chat.strip(), []

    text = ""
    files = []

    if isinstance(entrada_chat, dict):
        text = str(entrada_chat.get("text", "")).strip()
        files = list(entrada_chat.get("files", []) or [])
        return text, files

    text = str(getattr(entrada_chat, "text", "") or "").strip()
    files = list(getattr(entrada_chat, "files", []) or [])
    return text, files


def netejar_conversa():
    if st.session_state.missatges:
        primer_missatge = next(
            (m["text"] for m in st.session_state.missatges if m["rol"] == "user"),
            "Conversa sense títol",
        )
        titol = primer_missatge[:50] + ("..." if len(primer_missatge) > 50 else "")
        st.session_state.historial.insert(0, {
            "titol": titol,
            "missatges": list(st.session_state.missatges),
        })
    st.session_state.missatges = []
    st.session_state.pregunta_preparada = None


def restaurar_conversa(index):
    st.session_state.missatges = list(st.session_state.historial[index]["missatges"])
    st.session_state.pregunta_preparada = None


def renderitzar_fonts(fragments):
    if not fragments:
        return

    with st.expander("Fonts i cites utilitzades", expanded=False):
        for index, fragment in enumerate(fragments, start=1):
            text = fragment.get("text", "").strip().replace("\n", " ")
            resum = text[:280] + ("..." if len(text) > 280 else "")
            st.markdown(
                f"""
                <div class="sifecat-source">
                    <strong>[{index}]</strong><br>
                    <strong>{fragment.get('font', 'Document')}</strong><br>
                    <code>{fragment.get('id', 'sense-id')}</code><br>
                    <code>Fragment citat a la resposta: [{index}]</code>
                    <p>{resum}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


@st.cache_resource
def crear_logo_gencat(size: int = 80) -> Image.Image:
    img = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)
    color = (179, 0, 0)
    try:
        fnt = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(size * 0.44))
    except Exception:
        fnt = ImageFont.load_default()
    draw.text((int(size * 0.07), int(size * 0.03)), "gen", font=fnt, fill=color)
    draw.text((int(size * 0.07), int(size * 0.50)), "cat", font=fnt, fill=color)
    return img


@st.cache_resource
def crear_avatar_assistent(size: int = 96) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.ellipse((4, 4, size - 4, size - 4), fill=(231, 239, 247, 255))
    draw.ellipse((18, 18, size - 18, size - 18), fill=(247, 212, 191, 255))
    draw.rounded_rectangle((18, 60, size - 18, size - 6), radius=22, fill=(44, 73, 102, 255))
    draw.pieslice((14, 10, size - 14, 66), start=180, end=360, fill=(91, 56, 44, 255))
    draw.ellipse((26, 40, 34, 48), fill=(76, 127, 174, 255))
    draw.ellipse((62, 40, 70, 48), fill=(76, 127, 174, 255))
    draw.rounded_rectangle((20, 34, 40, 52), radius=6, outline=(28, 38, 52, 255), width=3)
    draw.rounded_rectangle((56, 34, 76, 52), radius=6, outline=(28, 38, 52, 255), width=3)
    draw.line((40, 43, 56, 43), fill=(28, 38, 52, 255), width=3)
    draw.arc((34, 54, 62, 68), start=15, end=165, fill=(176, 118, 108, 255), width=2)

    return img


st.set_page_config(
    page_title="Assistent SIFECAT",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
inicialitzar_estat()

index_disponible = (INDEX_DIR / "index.faiss").exists()

with st.sidebar:
    st.markdown("### Assistent SIFECAT")
    st.caption("Assistent virtual SIFECAT per a consultes operatives, certificació i anàlisi documental amb traçabilitat de fonts.")
    st.divider()
    st.button("Netejar conversa", use_container_width=True, on_click=netejar_conversa)

    st.divider()
    st.markdown("**En quin punt estàs?**")
    objectiu = st.radio(
        "Selecciona el teu objectiu principal",
        list(OBJECTIUS_USUARI.keys()),
        index=list(OBJECTIUS_USUARI.keys()).index(st.session_state.objectiu_actual),
        label_visibility="collapsed",
    )
    st.session_state.objectiu_actual = objectiu
    st.caption("Tria una necessitat i et proposaré consultes útils per començar.")

    st.markdown("**Suggeriments**")
    for index, exemple in enumerate(OBJECTIUS_USUARI[objectiu]):
        key = f"objectiu_{objectiu}_{index}"
        st.button(
            exemple,
            key=key,
            use_container_width=True,
            on_click=preparar_pregunta,
            args=(exemple,),
        )

    if st.session_state.historial:
        st.divider()
        st.markdown("**Els teus xats**")
        for i, conv in enumerate(st.session_state.historial):
            st.button(
                conv["titol"],
                key=f"hist_{i}",
                use_container_width=True,
                on_click=restaurar_conversa,
                args=(i,),
            )

st.markdown('<div class="sifecat-shell">', unsafe_allow_html=True)
st.markdown(
    """
    <section class="sifecat-hero">
        <h1>En què et puc ajudar avui?</h1>
        <p>
            Assistent virtual SIFECAT dissenyat per donar suport professional en operacions,
            certificació, indicadors i elaboració d'informes amb fonts verificables.
        </p>
    </section>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.missatges:
    st.markdown(
        """
        <div class="sifecat-empty">
            <strong>Comença amb una consulta concreta</strong>
            <p>Pots escriure directament què necessites fer, començar amb una consulta suggerida o pujar documents perquè també els tingui en compte.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sifecat-suggestions">', unsafe_allow_html=True)
    for index, exemple in enumerate(EXEMPLES_PREGUNTES):
        st.button(
            exemple,
            key=f"hero_exemple_{index}",
            use_container_width=False,
            on_click=preparar_pregunta,
            args=(exemple,),
        )
    st.markdown('</div>', unsafe_allow_html=True)

if not index_disponible:
    st.info("Encara no hi ha cap índex disponible. Puja documents des del panell inferior i els indexaré perquè els puguis consultar.")

for msg in st.session_state.missatges:
    avatar = crear_logo_gencat() if msg["rol"] == "user" else crear_avatar_assistent()
    with st.chat_message(msg["rol"], avatar=avatar):
        st.write(msg["text"])
        if msg["rol"] == "assistant":
            renderitzar_fonts(msg.get("sources", []))

entrada_chat = st.chat_input(
    "Escriu la teva consulta sobre SIFECAT, operacions o certificació...",
    accept_file="multiple",
    file_type=[ext.lstrip(".") for ext in sorted(SUPPORTED_EXTENSIONS)],
)
pregunta, documents_pujats = parsejar_entrada_chat(entrada_chat)

if documents_pujats:
    with st.spinner("Estic incorporant els documents i actualitzant l'índex..."):
        guardats = actualitzar_base_documental(documents_pujats)
    st.success("Documents afegits correctament: " + ", ".join(guardats))
    index_disponible = True

if not pregunta and st.session_state.pregunta_preparada:
    pregunta = st.session_state.pregunta_preparada
    st.session_state.pregunta_preparada = None

if pregunta and not index_disponible:
    st.warning("Abans de poder respondre, necessito tenir com a mínim un document indexat. Puja documents des del panell inferior i ho preparo per tu.")
elif pregunta:
    with st.chat_message("user", avatar=crear_logo_gencat()):
        st.write(pregunta)
    st.session_state.missatges.append({"rol": "user", "text": pregunta})

    with st.chat_message("assistant", avatar=crear_avatar_assistent()):
        carregant_placeholder = st.empty()
        carregant_placeholder.markdown(
            """
            <div class="sifecat-loading">
                <div class="sifecat-loading-dots">
                    <span class="sifecat-loading-dot"></span>
                    <span class="sifecat-loading-dot"></span>
                    <span class="sifecat-loading-dot"></span>
                </div>
                Deixa'm pensar un moment, ara et responc…
            </div>
            """,
            unsafe_allow_html=True,
        )
        try:
            fragments = cercar(pregunta, INDEX_DIR, top_k=DEFAULT_TOP_K)
            resposta = generar_resposta(
                pregunta,
                fragments,
                perfil_resposta=DEFAULT_PERFIL_RESPOSTA,
            )
            carregant_placeholder.empty()
            st.write(resposta)
            renderitzar_fonts(fragments)
            st.session_state.missatges.append(
                {
                    "rol": "assistant",
                    "text": resposta,
                    "sources": fragments,
                }
            )
        except Exception as e:
            carregant_placeholder.empty()
            st.error(
                "Ara mateix no he pogut completar la resposta. "
                "Si vols, torna-ho a provar o revisa que la clau del model i l'índex estiguin disponibles. "
                f"Detall tècnic: {e}"
            )

st.markdown("</div>", unsafe_allow_html=True)
