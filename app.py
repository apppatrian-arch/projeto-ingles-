import difflib
import json
import random
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from deep_translator import GoogleTranslator
from streamlit_mic_recorder import speech_to_text

BASE_DIR = Path(__file__).parent
BARALHO_PATH = BASE_DIR / "baralho.json"
PROGRESSO_PATH = BASE_DIR / "progresso.json"
IDIOMA_VOZ = {"pt": "pt-BR", "en": "en-US"}
CATEGORIAS = ["Geral", "Cotidiano", "Viagem", "Negócios"]
DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

st.set_page_config(page_title="Estudo de Inglês", page_icon="📘", layout="centered")


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


def traduzir(texto, origem, destino):
    return GoogleTranslator(source=origem, target=destino).translate(texto)


def normalizar(texto):
    texto = texto.lower().strip()
    texto = re.sub(r"[^\w\s]", "", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto


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
if "_forcar_pagina" in st.session_state:
    st.session_state["pagina"] = st.session_state.pop("_forcar_pagina")

st.markdown(
    """
    <style>
    .block-container { padding-top: 4.5rem; padding-bottom: 2rem; }
    h1 { font-size: 1.4rem !important; margin-bottom: 0.3rem !important; }
    h2, h3 { font-size: 1.05rem !important; margin-top: 0.2rem !important; margin-bottom: 0.3rem !important; }
    div[data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
    hr { margin: 0.6rem 0 !important; }
    .stButton > button { padding: 0.3rem 0.6rem; }
    .st-key-linha-botoes div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        gap: 0.5rem !important;
    }
    .st-key-linha-botoes div[data-testid="stColumn"] {
        min-width: 0 !important;
        width: 100% !important;
        flex: 1 1 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("📘 Estudo de Inglês")

with st.sidebar:
    pagina = st.radio(
        "Página",
        ["📖 Praticar", "📊 Revisão de erros", "🗓️ Meu tempo de uso"],
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
        categorias_selecionadas = st.multiselect("Categorias do baralho", CATEGORIAS, default=CATEGORIAS)
        if st.session_state.foco_frases:
            st.caption(f"🎯 Modo foco: {len(st.session_state.foco_frases)} frase(s) selecionada(s)")
            if st.button("Sair do modo foco"):
                st.session_state.foco_frases = set()
                st.session_state.frase_atual = None
                st.rerun()

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
    st.subheader("Traduzir e ouvir")
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

    if texto_trad.strip():
        traducao_trad = traduzir(texto_trad.strip(), idioma_cod_trad, idioma_alvo_trad)
        st.caption(f"Tradução: {traducao_trad}")
        colo1, colo2 = st.columns(2)
        with colo1:
            falar(texto_trad.strip(), IDIOMA_VOZ[idioma_cod_trad], "🔊 Original")
        with colo2:
            falar(traducao_trad, IDIOMA_VOZ[idioma_alvo_trad], "🔊 Tradução")

    st.divider()
    st.subheader("Adicionar frase ao baralho")
    idioma_deck = st.radio("Vou escrever em:", ["Português", "Inglês"], horizontal=True, key="idioma_deck")
    idioma_cod_deck = "pt" if idioma_deck == "Português" else "en"
    idioma_alvo_deck = "en" if idioma_cod_deck == "pt" else "pt"
    frase_deck = st.text_input("Sua palavra ou frase", key="frase_deck")
    categoria_deck = st.selectbox("Categoria", CATEGORIAS, key="categoria_deck")

    if st.button("Adicionar"):
        if frase_deck.strip():
            traducao_deck = traduzir(frase_deck.strip(), idioma_cod_deck, idioma_alvo_deck)
            if idioma_cod_deck == "pt":
                pt_deck, en_deck = frase_deck.strip(), traducao_deck
            else:
                en_deck, pt_deck = frase_deck.strip(), traducao_deck
            st.session_state.baralho.append({"pt": pt_deck, "en": en_deck, "categoria": categoria_deck})
            salvar_baralho(st.session_state.baralho)
            st.success(f"Adicionada em {categoria_deck}! 🇧🇷 {pt_deck}  ·  🇺🇸 {en_deck}")


def sortear_frase():
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


if pagina == "📖 Praticar":
    if fonte == "Baralho embutido":
        if st.session_state.frase_atual is None:
            sortear_frase()

        st.subheader("Traduza a frase abaixo:")
        origem_label = "Português" if st.session_state.direcao_atual == "pt->en" else "Inglês"
        destino_label = "Inglês" if st.session_state.direcao_atual == "pt->en" else "Português"
        origem_cod, destino_cod = st.session_state.direcao_atual.split("->")
        st.info(f"**{origem_label} → {destino_label}**\n\n> {st.session_state.frase_atual}")
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

        resposta_usuario = st.text_area("Sua tradução:", key="resposta_usuario")

        with st.container(key="linha-botoes"):
            col1, col2 = st.columns(2)
            with col1:
                verificar = st.button("Verificar", use_container_width=True)
            with col2:
                proxima = st.button("Próxima frase", use_container_width=True)

        if verificar and st.session_state.frase_atual:
            origem, destino = st.session_state.direcao_atual.split("->")
            st.session_state.traducao_referencia = traduzir(st.session_state.frase_atual, origem, destino)
            st.session_state.revelado = True
            if not st.session_state.registrado:
                st.session_state.pontuacao = calcular_similaridade(resposta_usuario, st.session_state.traducao_referencia)
                st.session_state.progresso.append({
                    "data": datetime.now().isoformat(timespec="seconds"),
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
            falar(st.session_state.traducao_referencia, IDIOMA_VOZ[destino_cod], "🔊 Ouvir tradução")

            pontuacao = st.session_state.pontuacao
            if pontuacao >= 80:
                emoji_score = "🟢"
            elif pontuacao >= 50:
                emoji_score = "🟡"
            else:
                emoji_score = "🔴"
            st.metric(f"{emoji_score} Similaridade com a tradução de referência", f"{pontuacao:.0f}%")
            st.progress(min(int(pontuacao), 100))

        if proxima:
            sortear_frase()
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

        if st.button("Traduzir"):
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
                st.write(f"{emoji} {pct:.0f}% · **{registro['frase_original']}** → {registro['traducao_referencia']}")

elif pagina == "📊 Revisão de erros":
    if not st.session_state.progresso:
        st.info("Ainda não há histórico de prática. Pratique algumas frases primeiro.")
    else:
        df = pd.DataFrame(st.session_state.progresso)
        resumo = (
            df.groupby("frase_original")["similaridade"]
            .agg(tentativas="count", media="mean", pior="min")
            .reset_index()
            .sort_values("media")
        )
        ultima_traducao = (
            df.drop_duplicates("frase_original", keep="last")
            .set_index("frase_original")["traducao_referencia"]
        )
        resumo["traducao"] = resumo["frase_original"].map(ultima_traducao)

        st.caption(f"{len(resumo)} frases distintas praticadas · {len(df)} tentativas no total")

        tabela = resumo[["frase_original", "traducao", "tentativas", "media", "pior"]].copy()
        tabela["media"] = tabela["media"].round(0).astype(int)
        tabela["pior"] = tabela["pior"].round(0).astype(int)
        tabela.columns = ["Frase", "Tradução", "Tentativas", "Média (%)", "Pior (%)"]
        st.dataframe(tabela, use_container_width=True, hide_index=True)

        piores = resumo[resumo["media"] < 60]
        if not piores.empty:
            st.subheader("🎯 Foco sugerido (média abaixo de 60%)")
            for _, row in piores.iterrows():
                st.write(f"- **{row['frase_original']}** → {row['traducao']} ({row['media']:.0f}%, {int(row['tentativas'])} tentativa(s))")
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
