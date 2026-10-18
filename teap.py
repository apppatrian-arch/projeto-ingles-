"""Curso preparatório para o TEAP (Test of English for Academic Purposes).

O TEAP (Tese Prime) avalia só leitura de textos acadêmicos em inglês: 2 textos e
20 questões objetivas (10 por texto), em 1h30, em quatro áreas do conhecimento.
Este módulo traz o guia da prova, estratégias, vocabulário acadêmico e simulados.
"""
import json
import random
import time
from datetime import datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

DADOS = Path(__file__).parent / "teap_dados"
AREAS = ["Biológicas/Saúde", "Exatas/Tecnológicas", "Humanas/Sociais", "Agrárias/Veterinárias"]
DURACAO_PROVA_MIN = 90
MODO_SIMULADO = "🎓 TEAP Simulado"
MODO_VOCABULARIO = "🎓 TEAP Vocabulário"
SECOES = ["📋 A prova", "🧠 Estratégias", "📚 Vocabulário", "📝 Simulado", "📈 Desempenho"]

TIPOS = {
    "localizacao": {
        "rotulo": "Localização de informação",
        "como": [
            "Leia a pergunta primeiro e sublinhe mentalmente as **palavras-chave** (nomes, números, termos técnicos).",
            "Procure essas palavras no texto (scanning). A resposta quase sempre está **perto** delas, às vezes com sinônimos.",
            "Cuidado com alternativas que repetem palavras do texto mas dizem outra coisa.",
        ],
    },
    "referencia": {
        "rotulo": "Referência pronominal",
        "como": [
            "Volte **uma ou duas frases** antes do pronome (it, they, this, these, which, such, those, their).",
            "Substitua o pronome pela alternativa e releia: a frase precisa continuar fazendo sentido.",
            "Verifique singular/plural: *it/this/which* → um elemento; *they/these/those* → vários.",
            "*This* e *which* podem se referir a uma **ideia inteira**, não só a uma palavra.",
        ],
    },
    "vocabulario": {
        "rotulo": "Compreensão de vocabulário",
        "como": [
            "Use o **contexto**: o que a frase antes e depois diz sobre a palavra?",
            "Palavras comuns podem ter sentido diferente em texto acadêmico (*address* = tratar de, *account for* = explicar).",
            "Teste cada alternativa no lugar da palavra e veja qual mantém o sentido do trecho.",
            "Confira prefixos e sufixos (*un-*, *re-*, *-less*, *-able*) e o glossário da prova.",
        ],
    },
    "sentenca": {
        "rotulo": "Compreensão detalhada (sentença)",
        "como": [
            "Quebre a frase longa em partes: **sujeito → verbo → complemento**. Procure o verbo principal.",
            "Atenção a negações (*not, no, rarely, hardly*) e a conectivos de contraste (*although, whereas, despite*).",
            "A alternativa certa costuma ser uma **paráfrase**, não uma cópia do texto.",
        ],
    },
    "paragrafo": {
        "rotulo": "Compreensão detalhada (parágrafo)",
        "como": [
            "Leia o parágrafo todo e ache a **frase-tópico** (geralmente a primeira ou a última).",
            "Pergunte: qual é o papel do parágrafo? Define, compara, dá exemplo, apresenta um problema ou uma solução?",
            "Elimine alternativas que citam um detalhe verdadeiro mas **não resumem** o parágrafo.",
        ],
    },
    "ideia_central": {
        "rotulo": "Ideia central",
        "como": [
            "Leia título, primeiro e último parágrafos: eles costumam trazer a tese e a conclusão.",
            "A ideia central cobre o **texto inteiro**; alternativas muito específicas ou muito amplas estão erradas.",
            "Desconfie de alternativas com *always, never, only, all* quando o texto usa linguagem cautelosa (*may, tend to*).",
        ],
    },
}

FALSOS_COGNATOS = [
    ("actually", "na verdade", "atualmente"),
    ("currently", "atualmente", "correntemente"),
    ("eventually", "por fim, no final", "eventualmente"),
    ("pretend", "fingir", "pretender"),
    ("intend", "pretender", "—"),
    ("push", "empurrar", "puxar"),
    ("library", "biblioteca", "livraria (bookstore)"),
    ("college", "faculdade, ensino superior", "colégio"),
    ("parents", "pais (mãe e pai)", "parentes (relatives)"),
    ("realize", "perceber, dar-se conta", "realizar"),
    ("resume", "retomar", "resumir (summarize)"),
    ("attend", "comparecer, assistir (aula)", "atender"),
    ("support", "apoiar, sustentar", "suportar (tolerate)"),
    ("sensible", "sensato, razoável", "sensível (sensitive)"),
    ("lecture", "palestra, aula expositiva", "leitura (reading)"),
    ("fabric", "tecido", "fábrica (factory)"),
    ("assist", "ajudar", "assistir (watch)"),
    ("comprehensive", "abrangente, completo", "compreensivo"),
    ("expert", "especialista", "esperto (smart)"),
    ("scholar", "estudioso, acadêmico", "escolar"),
    ("prejudice", "preconceito", "prejuízo (loss)"),
    ("preservative", "conservante", "preservativo (condom)"),
    ("exit", "saída", "êxito (success)"),
    ("novel", "romance; novo, inovador", "novela"),
    ("data", "dados", "—"),
]

CONECTIVOS = [
    ("Contraste", "however, nevertheless, nonetheless, yet, whereas, while, in contrast, on the other hand, although, even though, despite, in spite of",
     "porém, no entanto, ao passo que, embora, apesar de"),
    ("Adição", "moreover, furthermore, in addition, besides, also, as well as, not only… but also",
     "além disso, ademais, bem como, não só… mas também"),
    ("Causa", "because, since, as, due to, owing to, given that, as a result of, thanks to",
     "porque, já que, devido a, dado que"),
    ("Consequência", "therefore, thus, hence, consequently, as a result, so, accordingly, thereby",
     "portanto, assim, logo, consequentemente, desse modo"),
    ("Concessão", "albeit, even so, still, granted, notwithstanding, admittedly",
     "ainda que, mesmo assim, embora, é verdade que"),
    ("Exemplificação", "for example, for instance, such as, namely, in particular, including, e.g.",
     "por exemplo, tal como, a saber, em particular, incluindo"),
    ("Condição", "if, unless, provided that, as long as, otherwise, in case, whether",
     "se, a menos que, desde que, caso contrário, se (ou não)"),
    ("Conclusão", "in conclusion, overall, in sum, to sum up, in short, all in all, ultimately",
     "em conclusão, no geral, em resumo, em suma, no fim das contas"),
    ("Sequência / tempo", "first, then, subsequently, previously, meanwhile, afterwards, prior to, until, once",
     "primeiro, depois, posteriormente, anteriormente, enquanto isso, antes de"),
]

AFIXOS = [
    ("un-, in-/im-/il-/ir-, dis-, non-", "negação / oposto", "unlikely, impossible, irregular, disagree, nonlinear"),
    ("re-", "de novo", "reconsider, rebuild, reassess"),
    ("mis-", "errado", "misunderstand, misuse, misleading"),
    ("over- / under-", "excesso / falta", "overestimate, underrepresented"),
    ("pre- / post-", "antes / depois", "pretreatment, postgraduate"),
    ("inter- / sub- / multi-", "entre / abaixo / vários", "interaction, subgroup, multidisciplinary"),
    ("-ness, -ment, -tion, -ity", "forma substantivos", "awareness, development, adoption, availability"),
    ("-less / -ful", "sem / cheio de", "meaningless, harmful, helpful"),
    ("-able / -ible", "que pode ser", "measurable, reversible, accessible"),
    ("-ize / -ify / -en", "forma verbos", "analyze, simplify, strengthen"),
    ("-ly", "forma advérbios", "significantly, approximately, notably"),
    ("-er / -or / -ist", "quem faz (agente)", "researcher, instructor, economist"),
]


# --------------------------------------------------------------------------- dados
@st.cache_data(show_spinner=False)
def carregar_textos():
    textos = []
    if DADOS.exists():
        for arquivo in sorted(DADOS.glob("*.json")):
            if arquivo.stem == "vocabulario":
                continue
            textos.append(json.loads(arquivo.read_text(encoding="utf-8")))
    return textos


@st.cache_data(show_spinner=False)
def carregar_vocabulario():
    arquivo = DADOS / "vocabulario.json"
    if not arquivo.exists():
        return []
    return json.loads(arquivo.read_text(encoding="utf-8"))


def _registros_teap(progresso, modo):
    return [r for r in progresso if r.get("modo") == modo]


def palavras_para_revisar(progresso):
    erradas = set()
    for r in sorted(_registros_teap(progresso, MODO_VOCABULARIO), key=lambda x: x.get("data", "")):
        detalhe = r.get("detalhe", {})
        erradas |= set(detalhe.get("erradas", []))
        erradas -= set(detalhe.get("certas", []))
    return erradas


def _html_escape(texto):
    return (texto or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --------------------------------------------------------------------------- estilo
ESTILO = """
<style>
.teap-texto { background: rgba(99,102,241,0.07); border: 1.5px solid rgba(99,102,241,0.25);
    border-radius: 16px; padding: 0.9rem 1rem; margin-bottom: 0.8rem; }
.teap-texto h4 { margin: 0 0 0.5rem 0; font-size: 1.05rem; color: #E0E7FF; }
.teap-texto p { margin: 0 0 0.7rem 0; font-size: 1rem; line-height: 1.6; color: #E2E8F0; }
.teap-texto .num { display:inline-block; min-width: 1.4rem; font-weight: 800; color: #818CF8; font-size: 0.8rem; }
.teap-palavra { background: rgba(15,23,42,0.6); border: 1.5px solid rgba(99,102,241,0.35); border-radius: 16px;
    padding: 1rem; text-align: center; margin-bottom: 0.7rem; }
.teap-palavra .en { font-size: 1.8rem; font-weight: 800; color: #F1F5F9; }
.teap-palavra .meta { font-size: 0.75rem; color: #94A3B8; margin-top: 0.2rem; }
.teap-stats { display:flex; gap:0.4rem; margin: 0.2rem 0 0.8rem 0; }
.teap-stats div { flex:1; min-width:0; background: rgba(15,23,42,0.6); border:1px solid rgba(148,163,184,0.18);
    border-radius:12px; padding:0.45rem 0.3rem; text-align:center; }
.teap-stats b { display:block; font-size:1.05rem; color:#F1F5F9; }
.teap-stats span { font-size:0.65rem; color:#94A3B8; text-transform:uppercase; letter-spacing:0.03em; }
</style>
"""


# --------------------------------------------------------------------------- seções
def _secao_prova():
    st.markdown("#### Como é o TEAP")
    st.markdown(
        "<div class='teap-stats'>"
        "<div><b>2</b><span>textos</span></div>"
        "<div><b>20</b><span>questões</span></div>"
        "<div><b>1h30</b><span>de prova</span></div>"
        "<div><b>Leitura</b><span>foco</span></div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "- Dois **textos acadêmicos em inglês**, com **10 questões objetivas** cada.\n"
        "- Você escolhe a **área**: Biológicas/Saúde, Exatas/Tecnológicas, Humanas/Sociais ou Agrárias/Veterinárias.\n"
        "- Só **leitura**: não há conversação nem escrita.\n"
        "- Dicionário não é permitido; por isso treine o vocabulário e o uso do contexto."
    )
    st.caption(
        "Fonte: página oficial do exame na Tese Prime. Relatos indicam que o formato foi encurtado em 2026 "
        "(antes eram mais textos e mais tempo). Confirme sempre no edital do seu programa de pós-graduação, "
        "pois cada programa define a nota mínima exigida."
    )

    st.markdown("#### Os 6 tipos de questão")
    st.caption("Em cada texto aparecem estes tipos. Veja como atacar cada um.")
    for tipo, info in TIPOS.items():
        with st.expander(f"**{info['rotulo']}**"):
            for dica in info["como"]:
                st.markdown(f"- {dica}")

    st.markdown("#### Plano de estudo sugerido (4 semanas)")
    st.markdown(
        "- **Semana 1** — Vocabulário acadêmico (10 palavras/dia) e estratégias de leitura.\n"
        "- **Semana 2** — Um simulado por texto por dia; leia as explicações dos erros.\n"
        "- **Semana 3** — Foque nos tipos de questão com menor acerto (veja *Desempenho*).\n"
        "- **Semana 4** — Simulados completos (2 textos, 20 questões, 90 min) com cronômetro."
    )


def _secao_estrategias():
    st.markdown("#### Estratégias de leitura")
    with st.expander("⏱️ Gestão do tempo (90 minutos)", expanded=True):
        st.markdown(
            "- Reserve cerca de **40 min por texto** e deixe ~10 min de revisão.\n"
            "- **2 min**: leia título, primeiro e último parágrafos e a primeira frase de cada parágrafo (*skimming*).\n"
            "- Leia as perguntas **antes** de ler o texto inteiro, para saber o que procurar.\n"
            "- Se travar numa questão, marque e siga: não gaste mais de 3 min em uma."
        )
    with st.expander("🔍 Skimming e scanning"):
        st.markdown(
            "- **Skimming**: leitura rápida para captar o assunto e a estrutura (título, tópicos, conclusão).\n"
            "- **Scanning**: busca de uma informação específica (nome, número, termo) sem ler tudo.\n"
            "- Em artigos acadêmicos: *Abstract/Introdução* → problema; *Métodos* → como; "
            "*Resultados* → o que achou; *Discussão/Conclusão* → o que significa."
        )
    with st.expander("🔗 Conectivos e o que sinalizam"):
        st.caption("Conectivos revelam a lógica do texto: contraste, causa, exemplo, conclusão.")
        for funcao, ingles, pt in CONECTIVOS:
            st.markdown(f"**{funcao}** — {ingles}  \n:gray[{pt}]")
    with st.expander("⚠️ Falsos cognatos que enganam"):
        st.caption("Parecem português, mas têm outro sentido.")
        st.dataframe(
            [{"Inglês": en, "Significa": sig, "Não confundir com": nao} for en, sig, nao in FALSOS_COGNATOS],
            hide_index=True, use_container_width=True,
        )
    with st.expander("🧩 Prefixos e sufixos"):
        st.caption("Ajudam a deduzir palavras desconhecidas sem dicionário.")
        st.dataframe(
            [{"Afixo": a, "Ideia": i, "Exemplos": e} for a, i, e in AFIXOS],
            hide_index=True, use_container_width=True,
        )
    with st.expander("🔁 Referência pronominal na prática"):
        st.markdown(
            "Na frase *“Researchers collected samples. **These** were stored at low temperature.”*, "
            "**These** = *samples* (plural, objeto da frase anterior).\n\n"
            "Já em *“The method is cheap, **which** explains its popularity.”*, **which** = a ideia "
            "inteira de que o método é barato."
        )
    with st.expander("🧠 Palavras desconhecidas: o que fazer"):
        st.markdown(
            "1. Procure uma **definição ou exemplo** logo depois (vírgulas, travessões, *i.e.*, *such as*).\n"
            "2. Identifique a **classe** (substantivo, verbo, adjetivo) pela posição na frase.\n"
            "3. Observe **afixos** e raízes parecidas com o português.\n"
            "4. Se continuar sem entender, **ignore**: muitas questões não dependem de cada palavra."
        )


def _registrar(registrar, entrada):
    registrar(entrada)


def _secao_vocabulario(registrar, falar):
    vocab = carregar_vocabulario()
    if not vocab:
        st.info("O banco de vocabulário ainda não foi carregado.")
        return
    modo = st.radio("Modo", ["🎯 Quiz", "📖 Lista"], horizontal=True, key="teap_voc_modo", label_visibility="collapsed")
    areas = ["Todas"] + sorted({v.get("area", "Geral") for v in vocab})
    if modo == "📖 Lista":
        col1, col2 = st.columns([1, 1])
        area = col1.selectbox("Área", areas, key="teap_voc_lista_area")
        busca = col2.text_input("Buscar", key="teap_voc_busca").strip().lower()
        itens = [
            v for v in vocab
            if (area == "Todas" or v.get("area") == area)
            and (not busca or busca in v["en"].lower() or busca in v["pt"].lower())
        ]
        st.caption(f"{len(itens)} palavras")
        st.dataframe(
            [{"Inglês": v["en"], "Português": v["pt"], "Classe": v.get("classe", ""), "Exemplo": v.get("exemplo_en", "")}
             for v in itens],
            hide_index=True, use_container_width=True,
        )
        return

    erradas = palavras_para_revisar(st.session_state.progresso)
    opcoes_area = areas + ([f"⚠️ Só as que errei ({len(erradas)})"] if erradas else [])
    estado = st.session_state.get("teap_voc")

    def iniciar(area_escolhida, tamanho):
        if area_escolhida.startswith("⚠️"):
            pool = [v for v in vocab if v["en"] in erradas]
        elif area_escolhida == "Todas":
            pool = list(vocab)
        else:
            pool = [v for v in vocab if v.get("area") == area_escolhida]
        escolhidas = random.sample(pool, min(tamanho, len(pool)))
        questoes = []
        for v in escolhidas:
            candidatos = [o for o in vocab if o["pt"] != v["pt"] and o.get("classe") == v.get("classe")]
            if len(candidatos) < 3:
                candidatos = [o for o in vocab if o["pt"] != v["pt"]]
            alternativas = [v["pt"]] + [o["pt"] for o in random.sample(candidatos, 3)]
            random.shuffle(alternativas)
            questoes.append({"item": v, "alternativas": alternativas})
        st.session_state["teap_voc"] = {
            "area": area_escolhida, "questoes": questoes, "i": 0, "escolha": None,
            "certas": [], "erradas": [], "registrado": False,
        }

    if not estado:
        area_escolhida = st.selectbox("Área do vocabulário", opcoes_area, key="teap_voc_area")
        st.caption("10 palavras por rodada: escolha o significado em português.")
        st.button("▶️ Começar rodada", type="primary", use_container_width=True,
                  on_click=iniciar, args=(area_escolhida, 10))
        return

    questoes = estado["questoes"]
    total = len(questoes)

    def responder(j):
        e = st.session_state["teap_voc"]
        q = e["questoes"][e["i"]]
        e["escolha"] = j
        item = q["item"]
        (e["certas"] if q["alternativas"][j] == item["pt"] else e["erradas"]).append(item["en"])

    def avancar():
        e = st.session_state["teap_voc"]
        e["i"] += 1
        e["escolha"] = None

    def sair():
        st.session_state.pop("teap_voc", None)

    if estado["i"] >= total:
        acertos = len(estado["certas"])
        pct = 100 * acertos / total
        if not estado["registrado"]:
            registrar({
                "data": datetime.now().isoformat(timespec="seconds"),
                "modo": MODO_VOCABULARIO,
                "direcao": "en->pt",
                "frase_original": f"Quiz de vocabulário TEAP ({estado['area']})",
                "resposta_usuario": f"{acertos}/{total}",
                "traducao_referencia": ", ".join(estado["erradas"]) or "—",
                "similaridade": pct,
                "detalhe": {"certas": estado["certas"], "erradas": estado["erradas"]},
            })
            estado["registrado"] = True
        st.success(f"🏁 Rodada concluída: **{acertos}/{total}** ({pct:.0f}%)")
        if estado["erradas"]:
            st.markdown("**Para revisar:** " + ", ".join(f"`{p}`" for p in estado["erradas"]))
        c1, c2 = st.columns(2)
        c1.button("🔁 Nova rodada", type="primary", use_container_width=True, on_click=sair)
        c2.button("Voltar", use_container_width=True, on_click=sair)
        return

    q = questoes[estado["i"]]
    item = q["item"]
    st.progress(estado["i"] / total, text=f"Palavra {estado['i'] + 1} de {total}")
    st.markdown(
        f"<div class='teap-palavra'><div class='en'>{_html_escape(item['en'])}</div>"
        f"<div class='meta'>{_html_escape(item.get('classe', ''))} · {_html_escape(item.get('area', ''))}</div></div>",
        unsafe_allow_html=True,
    )
    falar(item["en"], "en-US", "🔊 Ouvir")
    if estado["escolha"] is None:
        for j, alternativa in enumerate(q["alternativas"]):
            st.button(alternativa, key=f"teap_voc_{estado['i']}_{j}", use_container_width=True,
                      on_click=responder, args=(j,))
    else:
        acertou = q["alternativas"][estado["escolha"]] == item["pt"]
        if acertou:
            st.success(f"✅ Correto! **{item['en']}** = {item['pt']}")
        else:
            st.error(f"❌ Você marcou *{q['alternativas'][estado['escolha']]}*. Correto: **{item['pt']}**")
        st.button("Próxima ➜" if estado["i"] + 1 < total else "Ver resultado ➜", type="primary",
                  use_container_width=True, on_click=avancar)
        if item.get("exemplo_en"):
            st.markdown(f"> {item['exemplo_en']}  \n> :gray[{item.get('exemplo_pt', '')}]")


def contador_regressivo(fim_ms):
    html = f"""
    <div id="c" style="font-family:Inter,-apple-system,sans-serif; display:flex; align-items:center;
        justify-content:center; gap:0.5rem; height:38px; border-radius:12px;
        background:rgba(99,102,241,0.12); border:1.5px solid rgba(99,102,241,0.35);
        color:#E0E7FF; font-weight:700; font-size:0.95rem;"></div>
    <script>
      var fim = {fim_ms};
      function pad(n) {{ return (n < 10 ? '0' : '') + n; }}
      function tick() {{
        var r = Math.max(0, Math.floor((fim - Date.now()) / 1000));
        var el = document.getElementById('c');
        el.textContent = '⏱️ Tempo restante  ' + pad(Math.floor(r / 60)) + ':' + pad(r % 60);
        if (r < 600) {{ el.style.color = '#FCA5A5'; el.style.borderColor = 'rgba(244,63,94,0.6)'; }}
      }}
      tick(); setInterval(tick, 1000);
    </script>
    """
    components.html(html, height=44)


def _texto_html(texto, indice=None):
    paragrafos = "".join(
        f"<p><span class='num'>{i}</span> {_html_escape(p)}</p>"
        for i, p in enumerate(texto["paragrafos"], start=1)
    )
    prefixo = f"Texto {indice} · " if indice else ""
    return (
        f"<div class='teap-texto'><h4>{prefixo}{_html_escape(texto['titulo'])}</h4>{paragrafos}</div>"
    )


def _secao_simulado(registrar):
    textos = carregar_textos()
    if not textos:
        st.info("Os textos do simulado ainda não foram carregados.")
        return
    sessao = st.session_state.get("teap_sessao")

    def iniciar(modo, area, texto_id):
        if modo == "completo":
            ids = [t["id"] for t in textos if t["area"] == area][:2]
        else:
            ids = [texto_id]
        st.session_state["teap_sessao"] = {
            "ids": ids, "area": area, "modo": modo, "inicio": time.time(), "resultado": None, "registrado": False,
        }

    def sair():
        st.session_state.pop("teap_sessao", None)

    if not sessao:
        area = st.selectbox("Área do conhecimento", AREAS, key="teap_area")
        da_area = [t for t in textos if t["area"] == area]
        modo = st.radio(
            "Tipo de simulado",
            ["📄 Um texto (10 questões)", "🎯 Simulado completo (2 textos, 90 min)"],
            key="teap_tipo_simulado",
        )
        if modo.startswith("📄"):
            rotulos = {t["id"]: t["titulo"] for t in da_area}
            texto_id = st.selectbox("Texto", list(rotulos), format_func=lambda i: rotulos[i], key="teap_texto")
            st.button("▶️ Começar", type="primary", use_container_width=True,
                      on_click=iniciar, args=("texto", area, texto_id))
        else:
            if len(da_area) < 2:
                st.warning("Esta área ainda não tem 2 textos.")
            else:
                st.caption("Dois textos da área e 20 questões, com cronômetro regressivo de 1h30.")
                st.button("▶️ Começar simulado completo", type="primary", use_container_width=True,
                          on_click=iniciar, args=("completo", area, None))
        return

    por_id = {t["id"]: t for t in textos}
    selecionados = [por_id[i] for i in sessao["ids"] if i in por_id]
    if not selecionados:
        sair()
        st.rerun()

    st.button("← Escolher outro", on_click=sair, key="teap_sair")
    if sessao["modo"] == "completo" and sessao["resultado"] is None:
        contador_regressivo(int((sessao["inicio"] + DURACAO_PROVA_MIN * 60) * 1000))

    resultado = sessao["resultado"]
    numero = 0
    if resultado is None:
        with st.form("teap_form"):
            for k, texto in enumerate(selecionados, start=1):
                st.markdown(_texto_html(texto, k if len(selecionados) > 1 else None), unsafe_allow_html=True)
                if texto.get("glossario"):
                    with st.expander("📖 Glossário"):
                        for termo, trad in texto["glossario"].items():
                            st.markdown(f"**{termo}** — {trad}")
                for q_i, q in enumerate(texto["questoes"], start=1):
                    numero += 1
                    st.markdown(f"**{numero}.** {q['enunciado']}")
                    st.radio(
                        f"Questão {numero}", q["alternativas"], index=None,
                        key=f"teap_q_{texto['id']}_{q_i}", label_visibility="collapsed",
                    )
            enviado = st.form_submit_button("✅ Finalizar e corrigir", type="primary", use_container_width=True)
        if enviado:
            respostas = {}
            for texto in selecionados:
                for q_i, q in enumerate(texto["questoes"], start=1):
                    escolha = st.session_state.get(f"teap_q_{texto['id']}_{q_i}")
                    respostas[f"{texto['id']}_{q_i}"] = (
                        q["alternativas"].index(escolha) if escolha in q["alternativas"] else None
                    )
            sessao["resultado"] = {"respostas": respostas, "fim": time.time()}
            st.rerun()
        return

    # ---- correção
    respostas = resultado["respostas"]
    por_tipo = {}
    acertos = total = 0
    for texto in selecionados:
        for q_i, q in enumerate(texto["questoes"], start=1):
            marcada = respostas.get(f"{texto['id']}_{q_i}")
            certo = marcada == q["correta"]
            a, t = por_tipo.get(q["tipo"], (0, 0))
            por_tipo[q["tipo"]] = (a + int(certo), t + 1)
            acertos += int(certo)
            total += 1
    pct = 100 * acertos / total
    minutos = (resultado["fim"] - sessao["inicio"]) / 60
    if not sessao["registrado"]:
        registrar({
            "data": datetime.now().isoformat(timespec="seconds"),
            "modo": MODO_SIMULADO,
            "direcao": "en->pt",
            "frase_original": " + ".join(t["titulo"] for t in selecionados),
            "resposta_usuario": f"{acertos}/{total}",
            "traducao_referencia": " | ".join(
                f"{TIPOS[tp]['rotulo']}: {a}/{t}" for tp, (a, t) in por_tipo.items()
            ),
            "similaridade": pct,
            "detalhe": {
                "area": sessao["area"], "textos": sessao["ids"], "tempo_min": round(minutos, 1),
                "por_tipo": {tp: [a, t] for tp, (a, t) in por_tipo.items()},
            },
        })
        sessao["registrado"] = True

    emoji = "🟢" if pct >= 70 else "🟡" if pct >= 50 else "🔴"
    st.markdown(f"### {emoji} {acertos}/{total} · {pct:.0f}%")
    st.caption(f"Tempo gasto: {minutos:.0f} min")
    st.markdown("**Acertos por tipo de questão**")
    for tp, (a, t) in por_tipo.items():
        st.progress(a / t, text=f"{TIPOS[tp]['rotulo']}: {a}/{t}")

    numero = 0
    for texto in selecionados:
        st.markdown(f"##### {texto['titulo']}")
        for q_i, q in enumerate(texto["questoes"], start=1):
            numero += 1
            marcada = respostas.get(f"{texto['id']}_{q_i}")
            certo = marcada == q["correta"]
            with st.expander(f"{'✅' if certo else '❌'} {numero}. {TIPOS[q['tipo']]['rotulo']}"):
                st.markdown(q["enunciado"])
                if marcada is None:
                    st.warning("Você não respondeu.")
                elif not certo:
                    st.error(f"Sua resposta: {q['alternativas'][marcada]}")
                st.success(f"Correta: {q['alternativas'][q['correta']]}")
                st.caption(q.get("explicacao", ""))
    st.button("🔁 Fazer outro simulado", type="primary", use_container_width=True, on_click=sair, key="teap_novo")


def _secao_desempenho(progresso):
    sims = _registros_teap(progresso, MODO_SIMULADO)
    quizzes = _registros_teap(progresso, MODO_VOCABULARIO)
    if not sims and not quizzes:
        st.info("Faça um simulado ou um quiz de vocabulário para ver seu desempenho aqui.")
        return
    c1, c2, c3 = st.columns(3)
    c1.metric("Simulados", len(sims))
    media_sim = sum(r["similaridade"] for r in sims) / len(sims) if sims else 0
    c2.metric("Média simulados", f"{media_sim:.0f}%" if sims else "—")
    media_voc = sum(r["similaridade"] for r in quizzes) / len(quizzes) if quizzes else 0
    c3.metric("Média vocabulário", f"{media_voc:.0f}%" if quizzes else "—")

    if sims:
        acumulado = {}
        for r in sims:
            for tp, (a, t) in r.get("detalhe", {}).get("por_tipo", {}).items():
                antigo = acumulado.get(tp, (0, 0))
                acumulado[tp] = (antigo[0] + a, antigo[1] + t)
        if acumulado:
            st.markdown("**Acerto por tipo de questão (acumulado)**")
            taxas = {TIPOS[tp]["rotulo"]: 100 * a / t for tp, (a, t) in acumulado.items() if t}
            st.bar_chart(taxas)
            fraco = min(acumulado, key=lambda tp: acumulado[tp][0] / max(acumulado[tp][1], 1))
            st.info(f"🎯 Seu ponto mais fraco: **{TIPOS[fraco]['rotulo']}**. Revise a estratégia em *🧠 Estratégias* e *📋 A prova*.")
            with st.expander(f"Como resolver: {TIPOS[fraco]['rotulo']}"):
                for dica in TIPOS[fraco]["como"]:
                    st.markdown(f"- {dica}")
        st.markdown("**Evolução dos simulados (%)**")
        st.line_chart([round(r["similaridade"]) for r in sims])
    revisar = palavras_para_revisar(progresso)
    if revisar:
        st.markdown(f"**Palavras para revisar ({len(revisar)}):** " + ", ".join(f"`{p}`" for p in sorted(revisar)))


def renderizar_teap(registrar, falar):
    """Página principal do curso. `registrar(entrada)` salva no histórico; `falar` toca o áudio."""
    st.markdown(ESTILO, unsafe_allow_html=True)
    st.subheader("🎓 Preparatório TEAP")
    st.caption("Leitura de textos acadêmicos em inglês para mestrado e doutorado.")
    secao = st.pills("Seção", SECOES, selection_mode="single", default=SECOES[0], key="teap_secao",
                     label_visibility="collapsed") or SECOES[0]
    if secao == "📋 A prova":
        _secao_prova()
    elif secao == "🧠 Estratégias":
        _secao_estrategias()
    elif secao == "📚 Vocabulário":
        _secao_vocabulario(registrar, falar)
    elif secao == "📝 Simulado":
        _secao_simulado(registrar)
    else:
        _secao_desempenho(st.session_state.progresso)
