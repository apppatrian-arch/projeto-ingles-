import concurrent.futures
import difflib
import json
import random
import re
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from deep_translator import GoogleTranslator, MyMemoryTranslator
from streamlit_mic_recorder import speech_to_text

BASE_DIR = Path(__file__).parent
BARALHO_PATH = BASE_DIR / "baralho.json"
PROGRESSO_PATH = BASE_DIR / "progresso.json"
AVATAR_PATH = BASE_DIR / "avatar.jpg"
IDIOMA_VOZ = {"pt": "pt-BR", "en": "en-US"}
CATEGORIAS = ["Geral", "Cotidiano", "Viagem", "Negócios", "🎵 Música"]
DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

PALAVRAS_EMOJI = [
    (["aeroporto", "airport"], "✈️"),
    (["voo", "voos", "flight", "flights"], "🛫"),
    (["mala", "malas", "luggage", "bagagem"], "🧳"),
    (["passagem", "passagens", "ticket", "tickets"], "🎫"),
    (["passaporte", "passport"], "🛂"),
    (["hotel", "hoteis", "hotéis"], "🏨"),
    (["quarto", "room"], "🛏️"),
    (["carro", "car", "carona", "ride"], "🚗"),
    (["táxi", "taxi"], "🚕"),
    (["trem", "train"], "🚆"),
    (["dinheiro", "money"], "💰"),
    (["wi-fi", "wifi"], "📶"),
    (["reunião", "reunioes", "reuniões", "meeting"], "💼"),
    (["contrato", "contract"], "📄"),
    (["orçamento", "orcamento", "budget"], "📊"),
    (["vendas", "sales"], "📈"),
    (["cliente", "clientes", "client", "customer"], "🤝"),
    (["empresa", "company"], "🏢"),
    (["email", "e-mail"], "📧"),
    (["relatório", "relatorio", "report"], "📋"),
    (["prazo", "deadline"], "⏳"),
    (["funcionários", "funcionarios", "employees"], "👥"),
    (["restaurante", "restaurant"], "🍽️"),
    (["café", "cafe", "coffee"], "☕"),
    (["mercado", "grocery"], "🛒"),
    (["leite", "milk"], "🥛"),
    (["chuva", "chovendo", "rain", "raining"], "🌧️"),
    (["filme", "filmes", "movie", "movies"], "🎬"),
    (["chave", "chaves", "keys"], "🔑"),
    (["praia", "beach"], "🏖️"),
    (["viagem", "viajar", "trip", "travel"], "🧳"),
    (["cidade", "city", "downtown"], "🏙️"),
    (["casa", "home", "house"], "🏠"),
    (["trabalho", "emprego", "job"], "💼"),
    (["banheiro", "bathroom"], "🚻"),
    (["ajuda", "ajudar", "help"], "🆘"),
    (["amigo", "amigos", "friend", "friends"], "👬"),
    (["família", "familia", "family"], "👨‍👩‍👧"),
    (["faculdade", "college"], "🎓"),
    (["exame", "exam"], "📝"),
    (["férias", "ferias", "vacation"], "🏖️"),
    (["manhã", "manha", "morning"], "🌅"),
    (["noite", "night"], "🌙"),
    (["cedo", "early"], "⏰"),
    (["hoje", "today"], "📅"),
    (["amanhã", "amanha", "tomorrow"], "📆"),
    (["ontem", "yesterday"], "🗓️"),
    (["preço", "preco", "desconto", "price", "discount"], "🏷️"),
    (["equipe", "team"], "🧑‍🤝‍🧑"),
    (["sistema", "system"], "💻"),
    (["marketing"], "📢"),
    (["telefone", "phone"], "📱"),
    (["janela", "window"], "🪟"),
    (["trânsito", "transito", "traffic"], "🚦"),
    (["vizinho", "neighbor"], "🏘️"),
    (["barulho", "noise"], "🔊"),
    (["paciência", "paciencia", "patience"], "🧘"),
    (["cozinhar", "cook", "cooking"], "🍳"),
    (["dormir", "sleep"], "😴"),
    (["acordar", "wake"], "⏰"),
    (["estudar", "study", "studied", "estudado"], "📚"),
    (["aprender", "learn", "learning"], "🧠"),
    (["economizar", "save"], "💵"),
    (["fome", "hungry"], "🍔"),
    (["cansado", "tired"], "😴"),
    (["produto", "product"], "📦"),
    (["pedido", "order"], "🧾"),
    (["nome", "name"], "🪪"),
    (["chorando", "chorar", "crying", "cry"], "😢"),
    (["feliz", "happy"], "😄"),
    (["proposta", "proposal"], "📑"),
    (["negociar", "negotiate", "negócio", "negocio", "deal"], "🤝"),
]

DICIONARIO_RAPIDO_EN_PT = {
    "the": "o/a", "a": "um/uma", "an": "um/uma", "is": "é/está", "are": "são/estão",
    "am": "sou/estou", "was": "era/estava", "were": "eram/estavam", "be": "ser/estar",
    "to": "para", "of": "de", "in": "em", "on": "em/sobre", "at": "em/às",
    "for": "para", "this": "isso/esse", "that": "aquilo/aquele", "these": "estes",
    "you": "você", "i": "eu", "we": "nós", "he": "ele", "she": "ela", "it": "isso/ele/ela",
    "they": "eles/elas", "do": "fazer", "does": "faz", "did": "fez", "done": "feito",
    "not": "não", "and": "e", "or": "ou", "but": "mas", "with": "com", "without": "sem",
    "from": "de", "have": "ter/tenho", "has": "tem", "had": "tinha", "having": "tendo",
    "will": "vai/irá", "would": "iria", "can": "pode", "could": "poderia", "should": "deveria",
    "my": "meu/minha", "your": "seu/sua", "his": "dele", "her": "dela",
    "our": "nosso/nossa", "their": "deles/delas", "what": "o que/qual",
    "where": "onde", "when": "quando", "why": "por que", "how": "como",
    "who": "quem", "please": "por favor", "yes": "sim", "no": "não",
    "there": "lá/ali", "here": "aqui", "very": "muito", "so": "então/tão",
    "now": "agora", "just": "só/apenas", "also": "também", "again": "de novo",
    "before": "antes", "after": "depois", "because": "porque", "if": "se",
    "need": "preciso", "want": "quero", "like": "gosto/como", "get": "conseguir/pegar",
}
DICIONARIO_RAPIDO_PT_EN = {
    "o": "the", "a": "the/a", "os": "the", "as": "the", "um": "a/an", "uma": "a/an",
    "é": "is", "são": "are", "está": "is", "estão": "are", "de": "of/from",
    "para": "to/for", "em": "in/on", "com": "with", "sem": "without", "que": "that/what",
    "eu": "i", "você": "you", "ele": "he", "ela": "she", "nós": "we",
    "eles": "they", "elas": "they", "não": "not/no", "sim": "yes", "e": "and",
    "ou": "or", "mas": "but", "meu": "my", "minha": "my", "seu": "your",
    "sua": "your", "nosso": "our", "nossa": "our", "onde": "where",
    "quando": "when", "como": "how", "quem": "who",
    "qual": "which/what", "isso": "this/that", "esse": "this", "aquilo": "that",
    "aqui": "here", "lá": "there", "muito": "very", "agora": "now",
    "também": "also", "antes": "before", "depois": "after", "porque": "because",
    "se": "if", "preciso": "need", "quero": "want", "gosto": "like",
    "vamos": "let's/we go", "tenho": "i have", "tem": "has/there is",
}


SCENAS_HISTORIA = [
    {
        "nome": "Aeroporto",
        "emoji": "✈️",
        "categoria": "Viagem",
        "narrativa": "Você acabou de desembarcar e precisa passar pelo guichê do aeroporto.",
    },
    {
        "nome": "Escritório",
        "emoji": "💼",
        "categoria": "Negócios",
        "narrativa": "Agora você está numa reunião de negócios importante.",
    },
    {
        "nome": "Loja",
        "emoji": "🛍️",
        "categoria": "Cotidiano",
        "narrativa": "Você entra numa loja para resolver uma pendência do dia a dia.",
    },
]

st.set_page_config(page_title="Duo Cido", page_icon="📘", layout="centered")


def falar(texto, idioma, label="🔊 Ouvir"):
    texto_js = json.dumps(texto)
    idioma_js = json.dumps(idioma)
    html = f"""
    <button style="display:flex;align-items:center;justify-content:center;gap:6px;
        width:100%;box-sizing:border-box;padding:0.5em 0.4em;border-radius:6px;
        border:1px solid #ccc;cursor:pointer;background:#f0f2f6;color:inherit;
        font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"
        onclick='window.speechSynthesis.cancel();
                 var u=new SpeechSynthesisUtterance({texto_js});
                 u.lang={idioma_js};
                 window.speechSynthesis.speak(u);'>
        {label}
    </button>
    """
    components.html(html, height=42)


def cronometro_estudo(segundos_iniciais):
    html = f"""
    <div id="cronometro-caixa" style="display:flex;align-items:center;justify-content:center;
        gap:0.4rem;background:rgba(255,255,255,0.18);border:2px solid rgba(255,255,255,0.3);
        border-radius:14px;padding:0.5rem;font-weight:800;font-size:1.05rem;color:inherit;
        font-family:'Nunito',sans-serif;">
        ⏱️ Tempo de estudo: <span id="cronometro-tempo">00:00</span>
    </div>
    <script>
    (function() {{
        let s = {segundos_iniciais};
        const el = document.getElementById('cronometro-tempo');
        function formatar(t) {{
            const h = Math.floor(t / 3600);
            const m = Math.floor((t % 3600) / 60);
            const sec = t % 60;
            const pad = n => String(n).padStart(2, '0');
            return h > 0 ? (pad(h) + ':' + pad(m) + ':' + pad(sec)) : (pad(m) + ':' + pad(sec));
        }}
        el.textContent = formatar(s);
        setInterval(function() {{
            s += 1;
            el.textContent = formatar(s);
        }}, 1000);
    }})();
    </script>
    """
    components.html(html, height=55)


def carregar_baralho():
    with open(BARALHO_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_baralho(baralho):
    with open(BARALHO_PATH, "w", encoding="utf-8") as f:
        json.dump(baralho, f, ensure_ascii=False, indent=2)


def carregar_progresso():
    if PROGRESSO_PATH.exists():
        with open(PROGRESSO_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def salvar_progresso(registros):
    with open(PROGRESSO_PATH, "w", encoding="utf-8") as f:
        json.dump(registros, f, ensure_ascii=False, indent=2)


def _chamar_com_limite(func, tempo_limite=6):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func)
        return future.result(timeout=tempo_limite)


def traduzir(texto, origem, destino):
    texto = (texto or "").strip()
    if not texto:
        return ""
    provedores = [
        lambda: GoogleTranslator(source=origem, target=destino).translate(texto),
        lambda: MyMemoryTranslator(
            source=IDIOMA_VOZ.get(origem, origem), target=IDIOMA_VOZ.get(destino, destino)
        ).translate(texto),
    ]
    for provedor in provedores:
        try:
            resultado = _chamar_com_limite(provedor, tempo_limite=6)
            if resultado:
                return resultado
        except Exception:
            pass
    st.error(
        "⚠️ Não consegui traduzir agora — os serviços de tradução parecem instáveis "
        "no momento. Tente novamente em alguns segundos."
    )
    st.stop()


@st.cache_data(show_spinner=False)
def traduzir_palavra_cache(palavra, origem, destino):
    palavra = (palavra or "").strip()
    if not palavra:
        return None
    dicionario = DICIONARIO_RAPIDO_EN_PT if origem == "en" else DICIONARIO_RAPIDO_PT_EN
    if palavra.lower() in dicionario:
        return dicionario[palavra.lower()]
    provedores = [
        lambda: GoogleTranslator(source=origem, target=destino).translate(palavra),
        lambda: MyMemoryTranslator(
            source=IDIOMA_VOZ.get(origem, origem), target=IDIOMA_VOZ.get(destino, destino)
        ).translate(palavra),
    ]
    for provedor in provedores:
        try:
            resultado = _chamar_com_limite(provedor, tempo_limite=6)
            if resultado:
                return resultado
        except Exception:
            pass
    return None


def _escapar_html(texto):
    return (
        (texto or "")
        .replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def frase_clicavel(frase, origem_cod, destino_cod, cabecalho):
    frase = frase or ""
    tokens = re.findall(r"\w+(?:'\w+)?|\s+|[^\w\s]", frase, flags=re.UNICODE)
    partes_html = []
    cache_local = {}
    for token in tokens:
        if re.fullmatch(r"\w+(?:'\w+)?", token, flags=re.UNICODE):
            chave = token.lower()
            if chave not in cache_local:
                cache_local[chave] = traduzir_palavra_cache(chave, origem_cod, destino_cod) or "?"
            partes_html.append(
                f'<span class="palavra-clicavel" data-palavra="{_escapar_html(token)}" '
                f'data-trad="{_escapar_html(cache_local[chave])}">{_escapar_html(token)}</span>'
            )
        else:
            partes_html.append(_escapar_html(token))
    frase_html = "".join(partes_html)
    cabecalho_html = _escapar_html(cabecalho)

    html = f"""
    <div style="background:rgba(99,102,241,0.08); border:1.5px solid rgba(99,102,241,0.25);
        border-radius:14px; padding:0.7rem 0.9rem; font-family:'Inter',-apple-system,sans-serif;">
        <div style="font-weight:700; color:#C7D2FE; font-size:0.8rem; margin-bottom:0.35rem;">{cabecalho_html}</div>
        <div style="font-size:1.1rem; font-weight:700; color:#F1F5F9; line-height:1.6;">{frase_html}</div>
        <div id="popup-traducao" style="display:none; margin-top:0.4rem; padding:0.35rem 0.6rem;
            background:rgba(16,185,129,0.15); border:1px solid rgba(16,185,129,0.4); border-radius:8px;
            font-size:0.85rem; color:#6EE7B7; font-weight:600;"></div>
        <div style="font-size:0.68rem; color:#64748B; margin-top:0.3rem;">👆 toque em uma palavra para ver o significado</div>
    </div>
    <style>
        .palavra-clicavel {{
            cursor:pointer;
            border-bottom:2px dotted rgba(99,102,241,0.6);
            padding-bottom:1px;
        }}
        .palavra-clicavel:active {{ color:#818CF8; }}
    </style>
    <script>
        document.querySelectorAll('.palavra-clicavel').forEach(function(el) {{
            el.addEventListener('click', function() {{
                var popup = document.getElementById('popup-traducao');
                popup.textContent = el.dataset.palavra + ' → ' + el.dataset.trad;
                popup.style.display = 'block';
            }});
        }});
    </script>
    """
    components.html(html, height=145, scrolling=True)


def normalizar(texto):
    texto = texto.lower().strip()
    texto = re.sub(r"[^\w\s]", "", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto


def emojis_da_frase(frase, maximo=2):
    tokens = set(normalizar(frase or "").split())
    encontrados = []
    for palavras, emoji in PALAVRAS_EMOJI:
        if emoji in encontrados:
            continue
        if tokens & set(palavras):
            encontrados.append(emoji)
        if len(encontrados) >= maximo:
            break
    return encontrados


def mostrar_emojis_frase(frase):
    emojis = emojis_da_frase(frase)
    if emojis:
        st.markdown(
            f"<div style='font-size:2.2rem; text-align:center; margin:0.2rem 0;'>{' '.join(emojis)}</div>",
            unsafe_allow_html=True,
        )


def montar_dados_biblioteca(categorias, ordem):
    itens = [
        item for item in st.session_state.baralho
        if item.get("categoria", "Geral") in categorias
    ] or st.session_state.baralho
    itens = list(itens)
    if ordem == "Aleatório":
        random.shuffle(itens)
    dados = []
    for item in itens:
        emojis = emojis_da_frase(f"{item['en']} {item['pt']}")
        dados.append({"en": item["en"], "pt": item["pt"], "emoji": " ".join(emojis)})
    return dados


def reprodutor_biblioteca(dados):
    dados_json = json.dumps(dados, ensure_ascii=False)
    total = len(dados)
    estilo_botao = (
        "flex:1; padding:0.6rem 0.5rem; border-radius:12px; border:1.5px solid rgba(99,102,241,0.4);"
        "background:rgba(99,102,241,0.12); color:#F1F5F9; font-size:1.1rem; cursor:pointer;"
        "font-family:'Inter',-apple-system,sans-serif;"
    )
    html = f"""
    <div style="background:rgba(99,102,241,0.08); border:1.5px solid rgba(99,102,241,0.25);
        border-radius:16px; padding:1rem 1.2rem; font-family:'Inter',-apple-system,sans-serif; text-align:center;">
        <div id="rb-progresso" style="font-size:0.8rem; color:#94A3B8; margin-bottom:0.5rem;">Frase 1 de {total}</div>
        <div id="rb-emoji" style="font-size:2rem; margin-bottom:0.4rem; min-height:2.4rem;"></div>
        <div id="rb-en" style="font-size:1.15rem; font-weight:700; color:#F1F5F9; margin-bottom:0.3rem;"></div>
        <div id="rb-pt" style="font-size:1.05rem; font-weight:600; color:#6EE7B7; min-height:1.4rem;"></div>
        <div style="display:flex; gap:0.5rem; justify-content:center; margin-top:1rem;">
            <button id="rb-anterior" style="{estilo_botao}">⏮️</button>
            <button id="rb-playpause" style="{estilo_botao}">▶️</button>
            <button id="rb-proximo" style="{estilo_botao}">⏭️</button>
        </div>
    </div>
    <script>
    (function() {{
        const dados = {dados_json};
        let pos = 0;
        let tocando = false;
        let tokenAtual = 0;

        function atualizarTela() {{
            const item = dados[pos];
            document.getElementById('rb-progresso').textContent = 'Frase ' + (pos + 1) + ' de ' + dados.length;
            document.getElementById('rb-emoji').textContent = item.emoji || '';
            document.getElementById('rb-en').textContent = item.en;
            document.getElementById('rb-pt').textContent = item.pt;
        }}

        function falarSequencia(meuToken) {{
            const item = dados[pos];
            window.speechSynthesis.cancel();
            const uEn = new SpeechSynthesisUtterance(item.en);
            uEn.lang = 'en-US';
            uEn.onend = function() {{
                if (meuToken !== tokenAtual) return;
                const uPt = new SpeechSynthesisUtterance(item.pt);
                uPt.lang = 'pt-BR';
                uPt.onend = function() {{
                    if (meuToken !== tokenAtual) return;
                    if (tocando) {{
                        setTimeout(function() {{
                            if (meuToken !== tokenAtual) return;
                            avancar();
                        }}, 1000);
                    }}
                }};
                window.speechSynthesis.speak(uPt);
            }};
            window.speechSynthesis.speak(uEn);
        }}

        function tocarAtual() {{
            atualizarTela();
            tokenAtual++;
            falarSequencia(tokenAtual);
        }}

        function avancar() {{
            pos = (pos + 1) % dados.length;
            tocarAtual();
        }}

        function voltar() {{
            pos = (pos - 1 + dados.length) % dados.length;
            tocarAtual();
        }}

        document.getElementById('rb-playpause').addEventListener('click', function() {{
            tocando = !tocando;
            this.textContent = tocando ? '⏸️' : '▶️';
            if (tocando) {{
                tocarAtual();
            }} else {{
                tokenAtual++;
                window.speechSynthesis.cancel();
            }}
        }});
        document.getElementById('rb-proximo').addEventListener('click', function() {{
            avancar();
        }});
        document.getElementById('rb-anterior').addEventListener('click', function() {{
            voltar();
        }});

        atualizarTela();
    }})();
    </script>
    """
    components.html(html, height=260)


def calcular_similaridade(resposta, referencia):
    a, b = normalizar(resposta), normalizar(referencia)
    if not a:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio() * 100


def formatar_minutos(minutos):
    minutos = int(round(minutos))
    if minutos < 60:
        return f"{minutos} min"
    return f"{minutos // 60}h {minutos % 60:02d}min"


if "baralho" not in st.session_state:
    st.session_state.baralho = carregar_baralho()
if "progresso" not in st.session_state:
    st.session_state.progresso = carregar_progresso()
if "frase_atual" not in st.session_state:
    st.session_state.frase_atual = None
if "direcao_atual" not in st.session_state:
    st.session_state.direcao_atual = None
if "revelado" not in st.session_state:
    st.session_state.revelado = False
if "traducao_referencia" not in st.session_state:
    st.session_state.traducao_referencia = ""
if "registrado" not in st.session_state:
    st.session_state.registrado = False
if "pontuacao" not in st.session_state:
    st.session_state.pontuacao = 0.0
if "foco_frases" not in st.session_state:
    st.session_state.foco_frases = set()
if "historia_indice" not in st.session_state:
    st.session_state.historia_indice = 0
if "historia_frase" not in st.session_state:
    st.session_state.historia_frase = None
if "historia_revelado" not in st.session_state:
    st.session_state.historia_revelado = False
if "audio_frase" not in st.session_state:
    st.session_state.audio_frase = None
if "audio_revelado" not in st.session_state:
    st.session_state.audio_revelado = False
if "audio_registrado" not in st.session_state:
    st.session_state.audio_registrado = False
if "audio_pontuacao" not in st.session_state:
    st.session_state.audio_pontuacao = 0.0
if "audio_referencia" not in st.session_state:
    st.session_state.audio_referencia = ""
if "sessao_inicio" not in st.session_state:
    st.session_state.sessao_inicio = datetime.now()
if "_forcar_pagina" in st.session_state:
    st.session_state["pagina"] = st.session_state.pop("_forcar_pagina")
if st.session_state.pop("_limpar_resposta", False):
    st.session_state["resposta_usuario"] = ""
    st.session_state["resposta_ouvir"] = ""
    st.session_state["leitura_texto"] = ""
if st.session_state.pop("_limpar_audio", False):
    st.session_state["resposta_audio"] = ""

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    html, body, [class*="css"], .stMarkdown, .stButton, .stTextInput, .stTextArea {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* ===== BACKGROUND E LAYOUT ===== */
    .stApp {
        background: radial-gradient(ellipse at 20% 0%, rgba(99,102,241,0.08) 0%, transparent 50%),
                    radial-gradient(ellipse at 80% 100%, rgba(16,185,129,0.06) 0%, transparent 50%),
                    #0B0E14 !important;
    }

    .block-container {
        padding-top: 4rem !important;
        padding-bottom: 3rem !important;
        max-width: 720px !important;
    }

    /* ===== TIPOGRAFIA ===== */
    h1 {
        font-size: 1.75rem !important;
        font-weight: 900 !important;
        margin-bottom: 0.5rem !important;
        background: linear-gradient(135deg, #F1F5F9 0%, #94A3B8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.02em;
    }

    h2, h3 {
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        margin-top: 0.4rem !important;
        margin-bottom: 0.5rem !important;
        color: #E2E8F0 !important;
        letter-spacing: -0.01em;
    }

    p, li, .stMarkdown {
        color: #CBD5E1 !important;
        line-height: 1.65 !important;
    }

    div[data-testid="stVerticalBlock"] { gap: 0.6rem !important; }

    hr {
        margin: 1rem 0 !important;
        border: none !important;
        height: 1px !important;
        background: rgba(148,163,184,0.12) !important;
    }

    /* ===== BOTÕES MODERNOS ===== */
    .stButton > button, [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-primary"] {
        padding: 0.6rem 1.2rem !important;
        border-radius: 14px !important;
        font-weight: 700 !important;
        letter-spacing: 0.01em;
        font-size: 0.85rem !important;
        border-width: 1.5px !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        font-family: 'Inter', sans-serif !important;
        position: relative;
        overflow: hidden;
    }

    .stButton > button::before {
        content: '';
        position: absolute;
        inset: 0;
        background: rgba(255,255,255,0);
        transition: background 0.2s ease;
    }

    .stButton > button:hover::before {
        background: rgba(255,255,255,0.08);
    }

    .stButton > button:active {
        transform: translateY(1px) scale(0.98) !important;
    }

    /* Primary button - gradient indigo */
    [data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #6366F1 0%, #818CF8 100%) !important;
        border-color: rgba(99,102,241,0.5) !important;
        color: #fff !important;
        box-shadow: 0 4px 14px rgba(99,102,241,0.35), 0 0 0 1px rgba(99,102,241,0.2) inset !important;
    }

    [data-testid="stBaseButton-primary"]:hover {
        box-shadow: 0 6px 24px rgba(99,102,241,0.45), 0 0 0 1px rgba(99,102,241,0.3) inset !important;
        transform: translateY(-1px) !important;
    }

    [data-testid="stBaseButton-primary"]:active {
        box-shadow: 0 2px 8px rgba(99,102,241,0.25) !important;
    }

    /* Secondary button - glassmorphism */
    [data-testid="stBaseButton-secondary"] {
        background: rgba(255,255,255,0.04) !important;
        border-color: rgba(255,255,255,0.1) !important;
        color: #CBD5E1 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
    }

    [data-testid="stBaseButton-secondary"]:hover {
        background: rgba(255,255,255,0.08) !important;
        border-color: rgba(255,255,255,0.18) !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.2) !important;
        transform: translateY(-1px) !important;
    }

    /* ===== CAMPOS DE TEXTO ===== */
    [data-testid="stTextInputRootElement"], [data-testid="stTextAreaRootElement"] {
        border-radius: 14px !important;
        border-width: 1.5px !important;
        border-color: rgba(148,163,184,0.2) !important;
        background: rgba(15,23,42,0.6) !important;
        transition: all 0.25s ease !important;
    }

    [data-testid="stTextInputRootElement"]:focus-within,
    [data-testid="stTextAreaRootElement"]:focus-within {
        border-color: rgba(99,102,241,0.6) !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.12), 0 4px 20px rgba(99,102,241,0.08) !important;
        background: rgba(15,23,42,0.8) !important;
    }

    [data-testid="stTextInputRootElement"] input,
    [data-testid="stTextAreaRootElement"] textarea {
        font-size: 1.05rem !important;
        font-family: 'Inter', sans-serif !important;
        color: #F1F5F9 !important;
    }

    [data-testid="stTextInputRootElement"] input::placeholder,
    [data-testid="stTextAreaRootElement"] textarea::placeholder {
        color: rgba(148,163,184,0.5) !important;
    }

    /* ===== ALERTAS MODERNOS ===== */
    [data-testid="stAlert"] {
        border-radius: 16px !important;
        border-width: 1.5px !important;
        padding: 1rem 1.2rem !important;
        backdrop-filter: blur(12px) !important;
        animation: fadeInUp 0.4s ease !important;
    }

    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }

    [data-testid="stAlert"] p {
        font-size: 1.05rem !important;
        line-height: 1.6rem !important;
    }

    [data-testid="stAlert"] blockquote p {
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        line-height: 1.7rem !important;
        color: #F1F5F9 !important;
    }

    /* Info alert - glassmorphism indigo */
    [data-testid="stAlert-container-info"] {
        background: rgba(99,102,241,0.08) !important;
        border-color: rgba(99,102,241,0.25) !important;
    }

    /* Success alert - glassmorphism emerald */
    [data-testid="stAlert-container-success"] {
        background: rgba(16,185,129,0.08) !important;
        border-color: rgba(16,185,129,0.25) !important;
    }

    /* Warning alert - glassmorphism amber */
    [data-testid="stAlert-container-warning"] {
        background: rgba(245,158,11,0.08) !important;
        border-color: rgba(245,158,11,0.25) !important;
    }

    /* Error alert - glassmorphism rose */
    [data-testid="stAlert-container-error"] {
        background: rgba(244,63,94,0.08) !important;
        border-color: rgba(244,63,94,0.25) !important;
    }

    /* ===== MÉTRICAS MODERNAS ===== */
    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.03);
        border-radius: 16px;
        padding: 1rem 1.1rem;
        border: 1.5px solid rgba(255,255,255,0.06);
        backdrop-filter: blur(8px);
        transition: all 0.25s ease;
    }

    [data-testid="stMetric"]:hover {
        border-color: rgba(99,102,241,0.2);
        background: rgba(255,255,255,0.05);
    }

    [data-testid="stMetricLabel"] p {
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: unset !important;
        font-size: 0.75rem !important;
        line-height: 1.1rem !important;
        color: #94A3B8 !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #F1F5F9 0%, #CBD5E1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* ===== EXPANDERS ===== */
    [data-testid="stExpander"] {
        border-radius: 16px !important;
        overflow: hidden;
        border: 1.5px solid rgba(148,163,184,0.1) !important;
        background: rgba(255,255,255,0.02) !important;
        backdrop-filter: blur(8px);
    }

    [data-testid="stExpanderToggleIcon"] {
        color: #94A3B8 !important;
    }

    /* ===== PROGRESS BAR ===== */
    [data-testid="stProgress"] > div > div {
        border-radius: 999px !important;
        background: rgba(255,255,255,0.06) !important;
        height: 8px !important;
    }

    [data-testid="stProgress"] > div > div > div {
        border-radius: 999px !important;
        background: linear-gradient(90deg, #6366F1 0%, #10B981 100%) !important;
        box-shadow: 0 0 12px rgba(99,102,241,0.4) !important;
        transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    /* ===== MULTISELECT CHIPS ===== */
    [data-baseweb="tag"] {
        border-radius: 999px !important;
        background: rgba(99,102,241,0.15) !important;
        border: 1px solid rgba(99,102,241,0.3) !important;
        color: #C7D2FE !important;
        font-weight: 500 !important;
        font-size: 0.8rem !important;
        transition: all 0.2s ease;
    }

    [data-baseweb="tag"]:hover {
        background: rgba(99,102,241,0.25) !important;
        transform: scale(1.02);
    }

    /* ===== SIDEBAR MODERNA ===== */
    [data-testid="stSidebar"] {
        background: rgba(11,14,20,0.85) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(148,163,184,0.08) !important;
    }

    [data-testid="stSidebar"] .stRadio > div {
        background: transparent !important;
        gap: 4px !important;
    }

    [data-testid="stSidebar"] .stRadio label {
        padding: 8px 12px !important;
        border-radius: 10px !important;
        transition: all 0.2s ease !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        color: #94A3B8 !important;
    }

    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(99,102,241,0.08) !important;
        color: #C7D2FE !important;
    }

    [data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] input:checked + div {
        background: rgba(99,102,241,0.15) !important;
        color: #818CF8 !important;
        font-weight: 700 !important;
        border-left: 3px solid #6366F1;
    }

    /* ===== RADIO BUTTONS HORIZONTAIS ===== */
    .stRadio > div[role="radiogroup"] {
        gap: 6px !important;
    }

    .stRadio > div[role="radiogroup"] label {
        border-radius: 10px !important;
        padding: 6px 12px !important;
        font-size: 0.82rem !important;
        transition: all 0.2s ease !important;
    }

    /* ===== SELECT BOX ===== */
    .stSelectbox > div > div {
        border-radius: 12px !important;
        border-color: rgba(148,163,184,0.15) !important;
        background: rgba(15,23,42,0.5) !important;
    }

    .stSelectbox > div > div:hover {
        border-color: rgba(99,102,241,0.4) !important;
    }

    /* ===== DATAFRAME ===== */
    [data-testid="stDataFrame"] {
        border-radius: 16px !important;
        overflow: hidden;
        border: 1.5px solid rgba(148,163,184,0.1) !important;
    }

    [data-testid="stDataFrame"] th {
        background: rgba(99,102,241,0.08) !important;
        color: #C7D2FE !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }

    [data-testid="stDataFrame"] td {
        color: #CBD5E1 !important;
        font-size: 0.9rem !important;
    }

    /* ===== CAPTIONS E TEXTOS PEQUENOS ===== */
    .stCaption {
        color: #64748B !important;
        font-size: 0.8rem !important;
    }

    /* ===== BALLOONS ===== */
    [data-testid="stBalloons"] {
        z-index: 9999 !important;
    }

    /* ===== LINHA DE BOTÕES ===== */
    .st-key-linha-botoes div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        gap: 0.6rem !important;
    }

    .st-key-linha-botoes div[data-testid="stColumn"] {
        min-width: 0 !important;
        width: 100% !important;
        flex: 1 1 0 !important;
    }

    /* ===== CARDS CUSTOMIZADOS ===== */
    .st-key-card-traduzir {
        background: rgba(99,102,241,0.06);
        border: 1.5px solid rgba(99,102,241,0.18);
        border-radius: 16px;
        padding: 1rem 1rem 0.3rem;
        backdrop-filter: blur(8px);
        transition: all 0.25s ease;
    }

    .st-key-card-traduzir:hover {
        border-color: rgba(99,102,241,0.3);
        background: rgba(99,102,241,0.09);
    }

    .st-key-card-traduzir [data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #6366F1 0%, #818CF8 100%) !important;
        border-color: rgba(99,102,241,0.5) !important;
        box-shadow: 0 4px 14px rgba(99,102,241,0.35) !important;
    }

    .st-key-card-adicionar {
        background: rgba(16,185,129,0.06);
        border: 1.5px solid rgba(16,185,129,0.18);
        border-radius: 16px;
        padding: 1rem 1rem 0.3rem;
        backdrop-filter: blur(8px);
        transition: all 0.25s ease;
    }

    .st-key-card-adicionar:hover {
        border-color: rgba(16,185,129,0.3);
        background: rgba(16,185,129,0.09);
    }

    .st-key-card-adicionar [data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #10B981 0%, #34D399 100%) !important;
        border-color: rgba(16,185,129,0.5) !important;
        box-shadow: 0 4px 14px rgba(16,185,129,0.35) !important;
    }

    /* ===== CARD CENA HISTÓRIA ===== */
    .st-key-cena-historia {
        background: rgba(99,102,241,0.06);
        border: 1.5px solid rgba(99,102,241,0.18);
        border-radius: 20px;
        padding: 1.4rem 1.2rem;
        text-align: center;
        backdrop-filter: blur(12px);
        animation: fadeInUp 0.5s ease;
        position: relative;
        overflow: hidden;
    }

    .st-key-cena-historia::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #6366F1, #10B981);
    }

    .st-key-cena-historia h2 {
        font-size: 1.5rem !important;
        margin: 0 !important;
        background: linear-gradient(135deg, #F1F5F9 0%, #818CF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* ===== SCORE BADGES ===== */
    .score-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 999px;
        font-weight: 700;
        font-size: 0.85rem;
        font-family: 'Inter', sans-serif;
    }

    .score-badge-green {
        background: rgba(16,185,129,0.12);
        border: 1px solid rgba(16,185,129,0.3);
        color: #34D399;
    }

    .score-badge-yellow {
        background: rgba(245,158,11,0.12);
        border: 1px solid rgba(245,158,11,0.3);
        color: #FBBF24;
    }

    .score-badge-red {
        background: rgba(244,63,94,0.12);
        border: 1px solid rgba(244,63,94,0.3);
        color: #FB7185;
    }

    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }

    ::-webkit-scrollbar-track {
        background: transparent;
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(148,163,184,0.2);
        border-radius: 999px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(148,163,184,0.35);
    }

    /* ===== DIVIDER NO SIDEBAR ===== */
    [data-testid="stSidebar"] hr {
        background: rgba(148,163,184,0.08) !important;
    }

    /* ===== SLIDER (se houver) ===== */
    [data-testid="stSlider"] > div > div > div {
        background: linear-gradient(90deg, #6366F1, #818CF8) !important;
    }

    /* ===== LOADING SPINNER ===== */
    [data-testid="stSpinner"] > div {
        border-top-color: #6366F1 !important;
        border-right-color: rgba(99,102,241,0.3) !important;
    }

    /* ===== TELA PEQUENA: menos espaço pra caber mais conteudo sem rolar ===== */
    @media (max-width: 600px) {
        .block-container {
            padding-top: 1.2rem !important;
            padding-bottom: 1.5rem !important;
        }
        .app-header { margin-bottom: 0.5rem !important; }
        .app-header .app-header-emoji { font-size: 1.5rem !important; margin-bottom: 0 !important; }
        .app-header h1 { font-size: 1.15rem !important; }
        .app-header p { display: none !important; }
        div[data-testid="stVerticalBlock"] { gap: 0.35rem !important; }
        hr { margin: 0.5rem 0 !important; }
        [data-testid="stAlert"] { padding: 0.6rem 0.8rem !important; }
        h2, h3 { margin-top: 0.15rem !important; margin-bottom: 0.25rem !important; font-size: 1rem !important; }
        [data-testid="stTextAreaRootElement"] textarea { min-height: 70px !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===== HEADER MODERNO =====
st.markdown(
    """
    <div class="app-header" style="text-align:center; margin-bottom:1.5rem; animation: fadeInDown 0.6s ease;">
        <div class="app-header-emoji" style="font-size:2.5rem; margin-bottom:0.3rem;">📘</div>
        <h1 style="margin:0; font-size:1.8rem;">Duo Cido</h1>
        <p style="color:#64748B; font-size:0.9rem; margin-top:0.3rem;">
            Aprenda inglês de forma interativa e divertida
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    pagina = st.radio(
        "Página",
        ["📖 Praticar", "🎧 Só áudio", "🗺️ Modo História", "📊 Revisão de erros", "🗓️ Meu tempo de uso"],
        key="pagina",
    )

    st.divider()
    st.header("Configurações")
    if pagina == "📖 Praticar":
        direcao_escolhida = st.radio(
            "Direção da tradução",
            ["Português → Inglês", "Inglês → Português", "Aleatório"],
            index=2,
        )
        fonte = st.radio("Fonte da frase", ["Baralho embutido", "Digitar minha frase"])
        if fonte == "Baralho embutido":
            modo_exercicio = st.radio(
                "Modo de exercício",
                ["✍️ Traduzir", "🎧 Ouvir e traduzir", "🗣️ Ler e falar"],
                key="modo_exercicio",
            )
        categorias_selecionadas = st.multiselect("Categorias do baralho", CATEGORIAS, default=CATEGORIAS)
        if st.session_state.foco_frases:
            st.caption(f"🎯 Modo foco: {len(st.session_state.foco_frases)} frase(s) selecionada(s)")
            if st.button("Sair do modo foco"):
                st.session_state.foco_frases = set()
                st.session_state.frase_atual = None
                st.rerun()
    elif pagina == "🎧 Só áudio":
        categorias_audio = st.multiselect(
            "Categorias do baralho", CATEGORIAS, default=CATEGORIAS, key="cat_audio"
        )
        ordem_biblioteca = st.radio(
            "Ordem da biblioteca de áudio", ["Sequencial", "Aleatório"], horizontal=True, key="ordem_biblioteca"
        )

    st.divider()
    st.subheader("Progresso")
    total = len(st.session_state.progresso)
    if total:
        media = sum(r.get("similaridade", 0) for r in st.session_state.progresso) / total
        st.metric("Frases praticadas", total)
        st.metric("Similaridade média", f"{media:.0f}%")
    else:
        st.caption("Nenhuma frase praticada ainda.")

    st.divider()
    with st.container(key="card-traduzir"):
        st.subheader("🔊 Traduzir e ouvir")
        st.caption("Ferramenta livre: escreva ou fale uma palavra/frase e ouça nos dois idiomas. Não salva nada.")
        idioma_trad = st.radio("Vou escrever em:", ["Português", "Inglês"], horizontal=True, key="idioma_trad")
        idioma_cod_trad = "pt" if idioma_trad == "Português" else "en"
        idioma_alvo_trad = "en" if idioma_cod_trad == "pt" else "pt"

        texto_falado_trad = speech_to_text(
            language=IDIOMA_VOZ[idioma_cod_trad],
            start_prompt="🎤 Falar palavra/frase",
            stop_prompt="⏹️ Parar gravação",
            just_once=True,
            use_container_width=True,
            key="stt_trad",
        )
        if texto_falado_trad:
            st.session_state["texto_trad"] = texto_falado_trad

        texto_trad = st.text_input("Sua palavra ou frase", key="texto_trad")
        st.button("Traduzir", key="btn_traduzir_trad", use_container_width=True, type="primary")

        if texto_trad.strip():
            traducao_trad = traduzir(texto_trad.strip(), idioma_cod_trad, idioma_alvo_trad)
            st.caption(f"Tradução: {traducao_trad}")
            colo1, colo2 = st.columns(2)
            with colo1:
                falar(texto_trad.strip(), IDIOMA_VOZ[idioma_cod_trad], "🔊 Original")
            with colo2:
                falar(traducao_trad, IDIOMA_VOZ[idioma_alvo_trad], "🔊 Tradução")

    st.divider()
    with st.container(key="card-adicionar"):
        st.subheader("📥 Adicionar frase ao baralho")
        st.caption("Cadastra a frase de vez no baralho, pra ela entrar no sorteio das próximas práticas.")
        idioma_deck = st.radio("Vou escrever em:", ["Português", "Inglês"], horizontal=True, key="idioma_deck")
        idioma_cod_deck = "pt" if idioma_deck == "Português" else "en"
        idioma_alvo_deck = "en" if idioma_cod_deck == "pt" else "pt"
        frase_deck = st.text_input("Sua palavra ou frase", key="frase_deck")
        categoria_deck = st.selectbox("Categoria", CATEGORIAS, key="categoria_deck")

        if st.button("Adicionar", type="primary", use_container_width=True):
            if frase_deck.strip():
                traducao_deck = traduzir(frase_deck.strip(), idioma_cod_deck, idioma_alvo_deck)
                if idioma_cod_deck == "pt":
                    pt_deck, en_deck = frase_deck.strip(), traducao_deck
                else:
                    en_deck, pt_deck = frase_deck.strip(), traducao_deck
                st.session_state.baralho.append({"pt": pt_deck, "en": en_deck, "categoria": categoria_deck})
                salvar_baralho(st.session_state.baralho)
                st.success(f"Adicionada em {categoria_deck}! 🇧🇷 {pt_deck}  ·  🇺🇸 {en_deck}")


def sortear_frase(limpar_resposta=False):
    pool = st.session_state.baralho
    if st.session_state.foco_frases:
        pool = [
            item for item in pool
            if item["pt"] in st.session_state.foco_frases or item["en"] in st.session_state.foco_frases
        ] or pool
    candidatos = [
        item for item in pool
        if item.get("categoria", "Geral") in categorias_selecionadas
    ] or pool
    item = random.choice(candidatos)
    if direcao_escolhida == "Português → Inglês":
        direcao = "pt->en"
    elif direcao_escolhida == "Inglês → Português":
        direcao = "en->pt"
    else:
        direcao = random.choice(["pt->en", "en->pt"])

    origem_texto = item["pt"] if direcao == "pt->en" else item["en"]
    st.session_state.frase_atual = origem_texto
    st.session_state.direcao_atual = direcao
    st.session_state.revelado = False
    st.session_state.traducao_referencia = ""
    st.session_state.registrado = False
    st.session_state.pontuacao = 0.0
    if limpar_resposta:
        st.session_state["_limpar_resposta"] = True


def sortear_frase_audio(limpar_resposta=False):
    pool = [
        item for item in st.session_state.baralho
        if item.get("categoria", "Geral") in categorias_audio
    ] or st.session_state.baralho
    item = random.choice(pool)
    st.session_state.audio_frase = item["en"]
    st.session_state.audio_revelado = False
    st.session_state.audio_registrado = False
    st.session_state.audio_pontuacao = 0.0
    st.session_state.audio_referencia = ""
    if limpar_resposta:
        st.session_state["_limpar_audio"] = True


if pagina == "📖 Praticar":
    cronometro_estudo(int((datetime.now() - st.session_state.sessao_inicio).total_seconds()))
    if fonte == "Baralho embutido":
        if st.session_state.frase_atual is None:
            sortear_frase()

        if st.session_state.get("_modo_anterior") != modo_exercicio:
            st.session_state["_modo_anterior"] = modo_exercicio
            st.session_state.revelado = False
            st.session_state.traducao_referencia = ""
            st.session_state.registrado = False
            st.session_state.pontuacao = 0.0
            st.session_state["resposta_usuario"] = ""
            st.session_state["resposta_ouvir"] = ""
            st.session_state["leitura_texto"] = ""

        origem_label = "Português" if st.session_state.direcao_atual == "pt->en" else "Inglês"
        destino_label = "Inglês" if st.session_state.direcao_atual == "pt->en" else "Português"
        origem_cod, destino_cod = st.session_state.direcao_atual.split("->")

        if modo_exercicio == "✍️ Traduzir":
            if st.session_state.revelado and st.session_state.traducao_referencia:
                col_ouvir_orig, col_ouvir_trad = st.columns(2)
                with col_ouvir_orig:
                    falar(st.session_state.frase_atual, IDIOMA_VOZ[origem_cod], "🔊 Frase original")
                with col_ouvir_trad:
                    falar(st.session_state.traducao_referencia, IDIOMA_VOZ[destino_cod], "🔊 Tradução")
            else:
                falar(st.session_state.frase_atual, IDIOMA_VOZ[origem_cod], "🔊 Ouvir frase original")

            texto_falado = speech_to_text(
                language=IDIOMA_VOZ[destino_cod],
                start_prompt="🎤 Falar minha tradução",
                stop_prompt="⏹️ Parar gravação",
                just_once=True,
                use_container_width=True,
                key="stt_baralho",
            )
            if texto_falado:
                st.session_state["resposta_usuario"] = texto_falado

            st.subheader("Traduza a frase abaixo:")
            mostrar_emojis_frase(st.session_state.frase_atual)
            frase_clicavel(st.session_state.frase_atual, origem_cod, destino_cod, f"{origem_label} → {destino_label}")

            resposta_usuario = st.text_area("Sua tradução:", key="resposta_usuario")

            with st.container(key="linha-botoes"):
                col1, col2 = st.columns(2)
                with col1:
                    verificar = st.button("Verificar", use_container_width=True, key="verificar_traduzir", type="primary")
                with col2:
                    proxima = st.button("Próxima frase", use_container_width=True, key="proxima_traduzir")

            if verificar and st.session_state.frase_atual:
                origem, destino = st.session_state.direcao_atual.split("->")
                st.session_state.traducao_referencia = traduzir(st.session_state.frase_atual, origem, destino)
                st.session_state.revelado = True
                if not st.session_state.registrado:
                    st.session_state.pontuacao = calcular_similaridade(resposta_usuario, st.session_state.traducao_referencia)
                    st.session_state.progresso.append({
                        "data": datetime.now().isoformat(timespec="seconds"),
                        "modo": "✍️ Traduzir",
                        "direcao": st.session_state.direcao_atual,
                        "frase_original": st.session_state.frase_atual,
                        "resposta_usuario": resposta_usuario,
                        "traducao_referencia": st.session_state.traducao_referencia,
                        "similaridade": st.session_state.pontuacao,
                    })
                    salvar_progresso(st.session_state.progresso)
                    st.session_state.registrado = True
                    st.rerun()

            if st.session_state.revelado and st.session_state.traducao_referencia:
                st.success(f"**Tradução de referência:** {st.session_state.traducao_referencia}")

                pontuacao = st.session_state.pontuacao
                emoji_score = "🟢" if pontuacao >= 80 else "🟡" if pontuacao >= 50 else "🔴"
                st.metric(f"{emoji_score} Similaridade com a tradução de referência", f"{pontuacao:.0f}%")
                st.progress(min(int(pontuacao), 100))

            if proxima:
                sortear_frase(limpar_resposta=True)
                st.rerun()

        elif modo_exercicio == "🎧 Ouvir e traduzir":
            st.subheader("Ouça o áudio e escreva a tradução:")
            st.caption(f"{origem_label} → {destino_label} · a frase fica escondida até você verificar")
            falar(st.session_state.frase_atual, IDIOMA_VOZ[origem_cod], "🔊 Ouvir frase (pode repetir)")

            texto_falado_ouvir = speech_to_text(
                language=IDIOMA_VOZ[destino_cod],
                start_prompt="🎤 Falar minha tradução",
                stop_prompt="⏹️ Parar gravação",
                just_once=True,
                use_container_width=True,
                key="stt_ouvir",
            )
            if texto_falado_ouvir:
                st.session_state["resposta_ouvir"] = texto_falado_ouvir

            resposta_ouvir = st.text_area("Sua tradução (pelo que você ouviu):", key="resposta_ouvir")

            with st.container(key="linha-botoes"):
                col1, col2 = st.columns(2)
                with col1:
                    verificar = st.button("Verificar", use_container_width=True, key="verificar_ouvir", type="primary")
                with col2:
                    proxima = st.button("Próxima frase", use_container_width=True, key="proxima_ouvir")

            if verificar and st.session_state.frase_atual:
                origem, destino = st.session_state.direcao_atual.split("->")
                st.session_state.traducao_referencia = traduzir(st.session_state.frase_atual, origem, destino)
                st.session_state.revelado = True
                if not st.session_state.registrado:
                    st.session_state.pontuacao = calcular_similaridade(resposta_ouvir, st.session_state.traducao_referencia)
                    st.session_state.progresso.append({
                        "data": datetime.now().isoformat(timespec="seconds"),
                        "modo": "🎧 Ouvir e traduzir",
                        "direcao": st.session_state.direcao_atual,
                        "frase_original": st.session_state.frase_atual,
                        "resposta_usuario": resposta_ouvir,
                        "traducao_referencia": st.session_state.traducao_referencia,
                        "similaridade": st.session_state.pontuacao,
                    })
                    salvar_progresso(st.session_state.progresso)
                    st.session_state.registrado = True
                    st.rerun()

            if st.session_state.revelado and st.session_state.traducao_referencia:
                mostrar_emojis_frase(st.session_state.frase_atual)
                st.info(f"**Frase original ({origem_label}):** {st.session_state.frase_atual}")
                st.success(f"**Tradução de referência:** {st.session_state.traducao_referencia}")
                falar(st.session_state.traducao_referencia, IDIOMA_VOZ[destino_cod], "🔊 Ouvir tradução")

                pontuacao = st.session_state.pontuacao
                emoji_score = "🟢" if pontuacao >= 80 else "🟡" if pontuacao >= 50 else "🔴"
                st.metric(f"{emoji_score} Similaridade com a tradução de referência", f"{pontuacao:.0f}%")
                st.progress(min(int(pontuacao), 100))

            if proxima:
                sortear_frase(limpar_resposta=True)
                st.rerun()

        else:
            st.subheader("Leia a frase abaixo em voz alta:")
            mostrar_emojis_frase(st.session_state.frase_atual)
            frase_clicavel(st.session_state.frase_atual, origem_cod, destino_cod, origem_label)
            falar(st.session_state.frase_atual, IDIOMA_VOZ[origem_cod], "🔊 Ouvir pronúncia correta")

            texto_falado_leitura = speech_to_text(
                language=IDIOMA_VOZ[origem_cod],
                start_prompt="🎤 Falar a frase",
                stop_prompt="⏹️ Parar gravação",
                just_once=True,
                use_container_width=True,
                key="stt_leitura",
            )
            if texto_falado_leitura:
                st.session_state["leitura_texto"] = texto_falado_leitura

            leitura_texto = st.session_state.get("leitura_texto", "")
            if leitura_texto:
                st.caption(f'🎙️ O que foi reconhecido da sua fala: "{leitura_texto}"')

            with st.container(key="linha-botoes"):
                col1, col2 = st.columns(2)
                with col1:
                    verificar = st.button("Verificar leitura", use_container_width=True, key="verificar_leitura", type="primary")
                with col2:
                    proxima = st.button("Próxima frase", use_container_width=True, key="proxima_leitura")

            if verificar and st.session_state.frase_atual:
                if not leitura_texto:
                    st.warning("Fale a frase primeiro usando o botão 🎤 Falar a frase antes de verificar.")
                else:
                    st.session_state.revelado = True
                    if not st.session_state.registrado:
                        st.session_state.pontuacao = calcular_similaridade(leitura_texto, st.session_state.frase_atual)
                        st.session_state.progresso.append({
                            "data": datetime.now().isoformat(timespec="seconds"),
                            "modo": "🗣️ Ler e falar",
                            "direcao": st.session_state.direcao_atual,
                            "frase_original": st.session_state.frase_atual,
                            "resposta_usuario": leitura_texto,
                            "traducao_referencia": st.session_state.frase_atual,
                            "similaridade": st.session_state.pontuacao,
                        })
                        salvar_progresso(st.session_state.progresso)
                        st.session_state.registrado = True
                        st.rerun()

            if st.session_state.revelado:
                pontuacao = st.session_state.pontuacao
                emoji_score = "🟢" if pontuacao >= 80 else "🟡" if pontuacao >= 50 else "🔴"
                st.metric(f"{emoji_score} Precisão da leitura", f"{pontuacao:.0f}%")
                st.progress(min(int(pontuacao), 100))

            if proxima:
                sortear_frase(limpar_resposta=True)
                st.rerun()

    else:
        st.subheader("Digite sua frase")
        direcao_manual = st.radio("Traduzir de:", ["Português → Inglês", "Inglês → Português"], horizontal=True)
        origem_manual = "pt" if direcao_manual == "Português → Inglês" else "en"
        destino_manual = "en" if direcao_manual == "Português → Inglês" else "pt"

        texto_falado_livre = speech_to_text(
            language=IDIOMA_VOZ[origem_manual],
            start_prompt="🎤 Falar frase",
            stop_prompt="⏹️ Parar gravação",
            just_once=True,
            use_container_width=True,
            key="stt_livre",
        )
        if texto_falado_livre:
            st.session_state["texto_livre"] = texto_falado_livre

        texto_livre = st.text_area("Frase (em português ou inglês):", key="texto_livre")

        if st.button("Traduzir", type="primary", use_container_width=True):
            if texto_livre.strip():
                resultado = traduzir(texto_livre, origem_manual, destino_manual)
                st.success(resultado)
                falar(resultado, IDIOMA_VOZ[destino_manual], "🔊 Ouvir tradução")

    if st.session_state.progresso:
        st.divider()
        with st.expander("Histórico recente"):
            for registro in reversed(st.session_state.progresso[-10:]):
                pct = registro.get("similaridade", 0)
                emoji = "🟢" if pct >= 80 else "🟡" if pct >= 50 else "🔴"
                modo_r = registro.get("modo", "✍️ Traduzir")
                st.write(f"{emoji} {pct:.0f}% · `{modo_r}` · **{registro['frase_original']}** → {registro['traducao_referencia']}")

elif pagina == "🎧 Só áudio":
    cronometro_estudo(int((datetime.now() - st.session_state.sessao_inicio).total_seconds()))
    st.subheader("🎧 Só áudio: ouça e traduza para o português")
    st.caption("A frase fica escondida — clique em ouvir, escreva ou fale sua tradução em português.")

    if st.session_state.audio_frase is None:
        sortear_frase_audio()

    falar(st.session_state.audio_frase, IDIOMA_VOZ["en"], "🔊 Ouvir frase (pode repetir)")

    texto_falado_audio = speech_to_text(
        language=IDIOMA_VOZ["pt"],
        start_prompt="🎤 Falar minha tradução",
        stop_prompt="⏹️ Parar gravação",
        just_once=True,
        use_container_width=True,
        key="stt_audio",
    )
    if texto_falado_audio:
        st.session_state["resposta_audio"] = texto_falado_audio

    resposta_audio = st.text_area("Sua tradução (em português):", key="resposta_audio")

    with st.container(key="linha-botoes"):
        col1, col2 = st.columns(2)
        with col1:
            verificar_audio = st.button(
                "Verificar", type="primary", use_container_width=True, key="verificar_audio"
            )
        with col2:
            proxima_audio = st.button(
                "Próxima frase", use_container_width=True, key="proxima_audio"
            )

    if verificar_audio and st.session_state.audio_frase:
        referencia = traduzir(st.session_state.audio_frase, "en", "pt")
        st.session_state.audio_referencia = referencia
        st.session_state.audio_revelado = True
        if not st.session_state.audio_registrado:
            st.session_state.audio_pontuacao = calcular_similaridade(resposta_audio, referencia)
            st.session_state.progresso.append({
                "data": datetime.now().isoformat(timespec="seconds"),
                "modo": "🎧 Só áudio",
                "direcao": "en->pt",
                "frase_original": st.session_state.audio_frase,
                "resposta_usuario": resposta_audio,
                "traducao_referencia": referencia,
                "similaridade": st.session_state.audio_pontuacao,
            })
            salvar_progresso(st.session_state.progresso)
            st.session_state.audio_registrado = True
            st.rerun()

    if st.session_state.audio_revelado:
        mostrar_emojis_frase(st.session_state.audio_frase)
        st.info(f"**Frase original (Inglês):** {st.session_state.audio_frase}")
        st.success(f"**Tradução de referência:** {st.session_state.audio_referencia}")
        falar(st.session_state.audio_referencia, IDIOMA_VOZ["pt"], "🔊 Ouvir tradução")

        pontuacao = st.session_state.audio_pontuacao
        emoji_score = "🟢" if pontuacao >= 80 else "🟡" if pontuacao >= 50 else "🔴"
        st.metric(f"{emoji_score} Similaridade com a tradução de referência", f"{pontuacao:.0f}%")
        st.progress(min(int(pontuacao), 100))

    if proxima_audio:
        sortear_frase_audio(limpar_resposta=True)
        st.rerun()

    st.divider()
    st.subheader("🎼 Ouvir toda a biblioteca")
    st.caption(
        "Escuta passiva: cada frase toca primeiro em inglês, depois em português, "
        "avançando sozinha para a próxima — sem precisar acertar nada."
    )
    dados_biblioteca = montar_dados_biblioteca(categorias_audio, ordem_biblioteca)
    reprodutor_biblioteca(dados_biblioteca)

elif pagina == "🗺️ Modo História":
    cronometro_estudo(int((datetime.now() - st.session_state.sessao_inicio).total_seconds()))
    if st.session_state.historia_indice >= len(SCENAS_HISTORIA):
        st.balloons()
        st.success("🎉 Você completou a jornada de hoje! Volte amanhã para praticar mais um pouco.")
        if st.button("🔁 Recomeçar jornada", type="primary", use_container_width=True):
            st.session_state.historia_indice = 0
            st.session_state.historia_frase = None
            st.session_state.historia_revelado = False
            st.rerun()
    else:
        cena = SCENAS_HISTORIA[st.session_state.historia_indice]
        st.progress(st.session_state.historia_indice / len(SCENAS_HISTORIA))
        st.caption(f"Cena {st.session_state.historia_indice + 1} de {len(SCENAS_HISTORIA)}")

        with st.container(key="cena-historia"):
            if AVATAR_PATH.exists():
                colav, coltxt = st.columns([1, 3])
                with colav:
                    st.image(str(AVATAR_PATH), width=100)
                with coltxt:
                    st.markdown(f"## {cena['emoji']} {cena['nome']}")
                    st.write(cena["narrativa"])
            else:
                st.markdown(f"## {cena['emoji']} {cena['nome']}")
                st.write(cena["narrativa"])

        if st.session_state.historia_frase is None:
            pool = [
                item for item in st.session_state.baralho
                if item.get("categoria", "Geral") == cena["categoria"]
            ] or st.session_state.baralho
            item = random.choice(pool)
            direcao = random.choice(["pt->en", "en->pt"])
            st.session_state.historia_frase = item["pt"] if direcao == "pt->en" else item["en"]
            st.session_state.historia_direcao = direcao
            st.session_state.historia_revelado = False

        origem_cod, destino_cod = st.session_state.historia_direcao.split("->")
        origem_label = "Português" if origem_cod == "pt" else "Inglês"
        destino_label = "Inglês" if destino_cod == "en" else "Português"

        falar(st.session_state.historia_frase, IDIOMA_VOZ[origem_cod], "🔊 Ouvir frase")
        mostrar_emojis_frase(st.session_state.historia_frase)
        frase_clicavel(st.session_state.historia_frase, origem_cod, destino_cod, f"{origem_label} → {destino_label}")

        resposta_historia = st.text_input(
            "Sua tradução:", key=f"resposta_historia_{st.session_state.historia_indice}"
        )

        if not st.session_state.historia_revelado:
            if st.button("Verificar", type="primary", use_container_width=True):
                referencia = traduzir(st.session_state.historia_frase, origem_cod, destino_cod)
                pontuacao = calcular_similaridade(resposta_historia, referencia)
                st.session_state.historia_referencia = referencia
                st.session_state.historia_pontuacao = pontuacao
                st.session_state.historia_revelado = True
                st.session_state.progresso.append({
                    "data": datetime.now().isoformat(timespec="seconds"),
                    "modo": "🗺️ Modo História",
                    "cena": cena["nome"],
                    "direcao": st.session_state.historia_direcao,
                    "frase_original": st.session_state.historia_frase,
                    "resposta_usuario": resposta_historia,
                    "traducao_referencia": referencia,
                    "similaridade": pontuacao,
                })
                salvar_progresso(st.session_state.progresso)
                st.rerun()
        else:
            st.success(f"**Tradução de referência:** {st.session_state.historia_referencia}")
            pontuacao = st.session_state.historia_pontuacao
            emoji_score = "🟢" if pontuacao >= 80 else "🟡" if pontuacao >= 50 else "🔴"
            st.metric(f"{emoji_score} Precisão", f"{pontuacao:.0f}%")
            st.progress(min(int(pontuacao), 100))

            proximo_rotulo = (
                "➡️ Avançar para a próxima cena"
                if st.session_state.historia_indice < len(SCENAS_HISTORIA) - 1
                else "🏁 Concluir jornada"
            )
            if st.button(proximo_rotulo, type="primary", use_container_width=True):
                st.session_state.historia_indice += 1
                st.session_state.historia_frase = None
                st.session_state.historia_revelado = False
                st.rerun()

elif pagina == "📊 Revisão de erros":
    if not st.session_state.progresso:
        st.info("Ainda não há histórico de prática. Pratique algumas frases primeiro.")
    else:
        df = pd.DataFrame(st.session_state.progresso)
        if "modo" not in df.columns:
            df["modo"] = "✍️ Traduzir"
        else:
            df["modo"] = df["modo"].fillna("✍️ Traduzir")

        resumo = (
            df.groupby(["frase_original", "modo"])["similaridade"]
            .agg(tentativas="count", media="mean", pior="min")
            .reset_index()
            .sort_values("media")
        )
        ultima_traducao = df.drop_duplicates(["frase_original", "modo"], keep="last")[
            ["frase_original", "modo", "traducao_referencia"]
        ]
        resumo = resumo.merge(ultima_traducao, on=["frase_original", "modo"], how="left")
        resumo = resumo.rename(columns={"traducao_referencia": "traducao"})

        st.caption(f"{len(resumo)} combinações de frase+modo praticadas · {len(df)} tentativas no total")

        tabela = resumo[["frase_original", "modo", "traducao", "tentativas", "media", "pior"]].copy()
        tabela["media"] = tabela["media"].round(0).astype(int)
        tabela["pior"] = tabela["pior"].round(0).astype(int)
        tabela.columns = ["Frase", "Modo", "Tradução", "Tentativas", "Média (%)", "Pior (%)"]
        st.dataframe(tabela, use_container_width=True, hide_index=True)

        piores = resumo[resumo["media"] < 60]
        if not piores.empty:
            st.subheader("🎯 Foco sugerido (média abaixo de 60%)")
            for _, row in piores.iterrows():
                st.write(f"- `{row['modo']}` **{row['frase_original']}** → {row['traducao']} ({row['media']:.0f}%, {int(row['tentativas'])} tentativa(s))")
            if st.button("🔁 Praticar essas frases agora"):
                st.session_state.foco_frases = set(piores["frase_original"]) | set(piores["traducao"])
                st.session_state["_forcar_pagina"] = "📖 Praticar"
                st.session_state.frase_atual = None
                st.rerun()
        else:
            st.success("Nenhuma frase com média abaixo de 60% — bom trabalho!")

else:
    if not st.session_state.progresso:
        st.info("Ainda não há histórico de prática. Pratique algumas frases primeiro.")
    else:
        LIMITE_MINUTOS = 10  # intervalos maiores que isso viram pausa, não contam como uso contínuo

        df = pd.DataFrame(st.session_state.progresso)
        if "modo" not in df.columns:
            df["modo"] = "✍️ Traduzir"
        else:
            df["modo"] = df["modo"].fillna("✍️ Traduzir")
        df["data_hora"] = pd.to_datetime(df["data"])
        df = df.sort_values("data_hora").reset_index(drop=True)
        df["dia"] = df["data_hora"].dt.date
        df["dia_semana"] = df["data_hora"].dt.dayofweek.map(lambda i: DIAS_SEMANA[i])
        df["mes"] = df["data_hora"].dt.to_period("M").astype(str)
        df["ano"] = df["data_hora"].dt.year

        intervalo_min = df["data_hora"].diff().dt.total_seconds().div(60)
        df["minutos_ativos"] = intervalo_min.clip(upper=LIMITE_MINUTOS).fillna(0)

        dias_unicos = sorted(df["dia"].unique())
        melhor_streak = streak = 1
        for i in range(1, len(dias_unicos)):
            if (dias_unicos[i] - dias_unicos[i - 1]).days == 1:
                streak += 1
            else:
                streak = 1
            melhor_streak = max(melhor_streak, streak)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Dias praticados", len(dias_unicos))
        col2.metric("Tentativas totais", len(df))
        col3.metric("Sequência mais longa", f"{melhor_streak} dia(s)")
        col4.metric("⏱️ Tempo ativo estimado", formatar_minutos(df["minutos_ativos"].sum()))
        st.caption(
            f"Estimativa: soma dos intervalos entre tentativas, limitando cada intervalo a "
            f"{LIMITE_MINUTOS} min para não contar pausas longas como uso."
        )

        st.subheader("Tentativas por modo de exercício")
        st.caption("Inclui tradução escrita, escuta (Ouvir e traduzir) e fala (Ler e falar).")
        st.bar_chart(df.groupby("modo").size())

        st.subheader("Minutos ativos por modo de exercício")
        st.bar_chart(df.groupby("modo")["minutos_ativos"].sum())

        st.subheader("Atividade por dia da semana")
        por_dia_semana = df.groupby("dia_semana").size().reindex(DIAS_SEMANA, fill_value=0)
        st.bar_chart(por_dia_semana)

        st.subheader("Minutos ativos por dia da semana")
        min_dia_semana = df.groupby("dia_semana")["minutos_ativos"].sum().reindex(DIAS_SEMANA, fill_value=0)
        st.bar_chart(min_dia_semana)

        st.subheader("Atividade por mês")
        st.bar_chart(df.groupby("mes").size())

        st.subheader("Minutos ativos por mês")
        st.bar_chart(df.groupby("mes")["minutos_ativos"].sum())

        st.subheader("Atividade por ano")
        st.bar_chart(df.groupby("ano").size())

        st.subheader("Minutos ativos por ano")
        st.bar_chart(df.groupby("ano")["minutos_ativos"].sum())

        st.subheader("Linha do tempo (por dia)")
        st.line_chart(df.groupby("dia").size())
