import streamlit as st

from response_engine import generar_resposta
from search_engine import cercar
from settings import INDEX_DIR

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
    --sifecat-ink: #101114;
    --sifecat-muted: #667085;
    --sifecat-soft: #8d95a3;
    --sifecat-line: rgba(16, 17, 20, 0.08);
    --sifecat-surface: rgba(255, 255, 255, 0.72);
    --sifecat-shadow: 0 24px 80px rgba(17, 24, 39, 0.10);
    --sifecat-shadow-soft: 0 14px 36px rgba(17, 24, 39, 0.08);
    --sifecat-accent: #111827;
    --sifecat-accent-soft: rgba(17, 24, 39, 0.06);
}

.stApp {
    background:
        radial-gradient(circle at top left, rgba(255, 255, 255, 0.95), transparent 28%),
        radial-gradient(circle at 85% 18%, rgba(203, 213, 225, 0.34), transparent 22%),
        radial-gradient(circle at 25% 78%, rgba(226, 232, 240, 0.72), transparent 30%),
        linear-gradient(180deg, #f8f8f7 0%, #eef1f6 48%, #edf0f5 100%);
    color: var(--sifecat-ink);
    font-family: 'Plus Jakarta Sans', sans-serif;
}

.stApp > header {
    background: transparent;
}

.stApp [data-testid="block-container"] {
    max-width: 100%;
    padding-top: 1.4rem;
    padding-bottom: 2rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.74) 0%, rgba(247, 248, 250, 0.72) 100%);
    border-right: 1px solid rgba(255, 255, 255, 0.55);
    backdrop-filter: blur(28px);
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
    padding: 0.15rem 0 1.4rem 0;
}

.sifecat-hero {
    position: relative;
    overflow: hidden;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.82), rgba(255, 255, 255, 0.58));
    border: 1px solid rgba(255, 255, 255, 0.62);
    border-radius: 34px;
    padding: 1.8rem 2rem 1.35rem 2rem;
    box-shadow: var(--sifecat-shadow);
    backdrop-filter: blur(32px);
    margin-bottom: 0.75rem;
    width: 100%;
}

.sifecat-hero::before {
    content: "";
    position: absolute;
    inset: auto -8% -18% auto;
    width: 280px;
    height: 280px;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(203, 213, 225, 0.42), transparent 62%);
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
    font-size: 3rem;
    line-height: 0.98;
    letter-spacing: -0.05em;
    margin: 0;
    color: var(--sifecat-ink);
    max-width: none;
    white-space: nowrap;
    text-align: justify;
    text-align-last: left;
    text-justify: inter-word;
}

.sifecat-hero p {
    margin: 0.85rem 0 0 0;
    color: var(--sifecat-muted);
    max-width: 76rem;
    font-size: 0.98rem;
    line-height: 1.68;
    text-align: justify;
}

.sifecat-empty {
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.72), rgba(255, 255, 255, 0.48));
    border: 1px solid rgba(255, 255, 255, 0.64);
    border-radius: 28px;
    padding: 0.9rem 1rem;
    margin: 0.3rem 0 0.85rem 0;
    box-shadow: var(--sifecat-shadow-soft);
    backdrop-filter: blur(24px);
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
    display: grid;
    grid-template-columns: repeat(2, minmax(280px, 1fr));
    gap: 0.85rem;
    margin-top: 0.9rem;
    width: 100%;
    max-width: 100%;
}

.sifecat-loading {
    display: inline-flex;
    align-items: center;
    gap: 0.55rem;
    padding: 0.78rem 0.95rem;
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.72);
    border: 1px solid rgba(16, 17, 20, 0.08);
    color: var(--sifecat-muted);
    font-size: 0.92rem;
    box-shadow: var(--sifecat-shadow-soft);
}

.sifecat-loading-dot {
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: #111827;
    opacity: 0.85;
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

[data-testid="stChatMessage"] {
    background: transparent;
    padding: 0;
}

[data-testid="stChatMessage"] [data-testid="chatAvatarIcon-user"] {
    background: linear-gradient(135deg, #111827, #4b5563);
    color: white;
}

[data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] {
    background: linear-gradient(135deg, #dbe3f0, #ffffff);
    color: #111827;
    border: 1px solid rgba(16, 17, 20, 0.08);
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li {
    line-height: 1.72;
    color: var(--sifecat-ink);
}

[data-testid="stChatMessage"] {
    margin-bottom: 0.75rem;
}

[data-testid="stChatMessageContent"] {
    background: rgba(255, 255, 255, 0.62);
    border: 1px solid rgba(255, 255, 255, 0.68);
    border-radius: 26px;
    padding: 1rem 1.05rem;
    box-shadow: var(--sifecat-shadow-soft);
    backdrop-filter: blur(20px);
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] {
    background: linear-gradient(135deg, rgba(17, 24, 39, 0.96), rgba(55, 65, 81, 0.92));
    border: 1px solid rgba(255, 255, 255, 0.08);
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] p {
    color: #f8fafc;
}

[data-testid="stChatInput"] {
    background: transparent;
}

[data-testid="stChatInput"] > div {
    border-radius: 28px !important;
    border: 1px solid rgba(255, 255, 255, 0.72) !important;
    background: rgba(255, 255, 255, 0.78) !important;
    box-shadow: var(--sifecat-shadow-soft) !important;
    backdrop-filter: blur(24px);
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
    border-radius: 999px;
    border: 1px solid rgba(16, 17, 20, 0.08);
    background: rgba(255, 255, 255, 0.78);
    color: var(--sifecat-ink);
    font-weight: 500;
    box-shadow: 0 8px 18px rgba(17, 24, 39, 0.06);
}

.sifecat-suggestions .stButton > button {
    min-height: 72px;
    border-radius: 22px;
    justify-content: flex-start;
    text-align: left;
    padding: 1rem 1.15rem;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.72));
    border: 1px solid rgba(17, 24, 39, 0.08);
    box-shadow: 0 12px 30px rgba(17, 24, 39, 0.06);
    font-size: 0.96rem;
    line-height: 1.35;
}

.sifecat-suggestions .stButton > button:hover {
    transform: translateY(-1px);
    border-color: rgba(17, 24, 39, 0.16);
}

.stButton > button:hover,
[data-testid="stBaseButton-secondary"]:hover {
    border-color: rgba(16, 17, 20, 0.14);
    background: rgba(255, 255, 255, 0.96);
    color: var(--sifecat-ink);
}

[data-testid="stSidebar"] .stButton > button,
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
    background: rgba(255, 255, 255, 0.86);
    color: var(--sifecat-ink);
    border: 1px solid rgba(16, 17, 20, 0.06);
    box-shadow: none;
}

@media (max-width: 900px) {
    .stApp [data-testid="block-container"] {
        padding-top: 0.8rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .sifecat-hero h1 {
        font-size: 2.55rem;
    }

    .sifecat-hero {
        padding: 1.5rem 1.15rem 1.15rem 1.15rem;
    }

    .sifecat-suggestions {
        grid-template-columns: 1fr;
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


def netejar_conversa():
    st.session_state.missatges = []
    st.session_state.pregunta_preparada = None


def renderitzar_fonts(fragments):
    if not fragments:
        return

    with st.expander("Fonts recuperades", expanded=False):
        for fragment in fragments:
            text = fragment.get("text", "").strip().replace("\n", " ")
            resum = text[:280] + ("..." if len(text) > 280 else "")
            st.markdown(
                f"""
                <div class="sifecat-source">
                    <strong>{fragment.get('font', 'Document')}</strong><br>
                    <code>{fragment.get('id', 'sense-id')}</code>
                    <p>{resum}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


st.set_page_config(
    page_title="Assistent SIFECAT",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
inicialitzar_estat()

if not (INDEX_DIR / "index.faiss").exists():
    st.error("No s'ha trobat l'índex de cerca a data/index. Genera'l abans d'executar l'app.")
    st.stop()

with st.sidebar:
    st.markdown("### Assistent SIFECAT")
    st.caption("Entén SIFECAT, respon preguntes i accelera decisions amb context real.")
    st.divider()
    if st.button("Netejar conversa", use_container_width=True):
        netejar_conversa()
        st.rerun()

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
        if st.button(exemple, key=key, use_container_width=True):
            st.session_state.pregunta_preparada = exemple
            st.rerun()

st.markdown('<div class="sifecat-shell">', unsafe_allow_html=True)
st.markdown(
    """
    <section class="sifecat-hero">
        <span class="sifecat-kicker">Assistent que entén SIFECAT</span>
        <h1>En què et puc ajudar avui?</h1>
        <p>
            Entén la documentació i l'operativa de SIFECAT, respon preguntes sobre processos,
            certificació, operacions i indicadors, i t'ajuda a redactar informes, enquestes i
            avaluacions amb el context real disponible al teu entorn de treball.
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
            <p>Pots escriure directament què necessites fer o començar amb una d'aquestes consultes.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sifecat-suggestions">', unsafe_allow_html=True)
    for index, exemple in enumerate(EXEMPLES_PREGUNTES):
        if st.button(exemple, key=f"hero_exemple_{index}", use_container_width=False):
            st.session_state.pregunta_preparada = exemple
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

for index, msg in enumerate(st.session_state.missatges):
    with st.chat_message(msg["rol"]):
        st.write(msg["text"])
        if msg["rol"] == "assistant":
            renderitzar_fonts(msg.get("sources", []))

pregunta = st.chat_input("Fes una pregunta sobre SIFECAT, operacions o certificació...")
if not pregunta and st.session_state.pregunta_preparada:
    pregunta = st.session_state.pregunta_preparada
    st.session_state.pregunta_preparada = None

if pregunta:
    with st.chat_message("user"):
        st.write(pregunta)
    st.session_state.missatges.append({"rol": "user", "text": pregunta})

    with st.chat_message("assistant"):
        carregant_placeholder = st.empty()
        carregant_placeholder.markdown(
            """
            <div class="sifecat-loading">
                <span class="sifecat-loading-dot"></span>
                Analitzant documents i preparant una resposta contextualitzada...
            </div>
            """,
            unsafe_allow_html=True,
        )
        try:
            fragments = cercar(pregunta, INDEX_DIR)
            resposta = generar_resposta(pregunta, fragments)
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
            st.error(f"Error: {e}")

st.markdown("</div>", unsafe_allow_html=True)
