
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Decisões e Precedentes | CREA-MS",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Identidade visual
st.markdown("""
<style>
    .stApp {
        background-color: #f4f6f9;
        color: #172b4d;
    }

    [data-testid="stHeader"] {
        background: rgba(244, 246, 249, 0.95);
    }

    .block-container {
        max-width: 1500px;
        padding-top: 1.8rem;
        padding-bottom: 3rem;
    }

    .hero {
        background: linear-gradient(120deg, #102b4e 0%, #17466b 100%);
        padding: 2rem 2.2rem;
        border-radius: 16px;
        border-bottom: 5px solid #c7a44b;
        margin-bottom: 1.3rem;
        color: white;
    }

    .hero h1 {
        color: white;
        font-size: clamp(1.65rem, 3vw, 2.35rem);
        line-height: 1.2;
        margin: 0 0 0.7rem 0;
    }

    .hero p {
        color: #e4edf6;
        font-size: 1rem;
        margin: 0;
    }

    .section-title {
        color: #153b60;
        font-size: 1.25rem;
        font-weight: 700;
        margin: 1.3rem 0 0.7rem 0;
    }

    [data-testid="stMetric"] {
        background: white;
        border: 1px solid #dce3eb;
        border-top: 3px solid #c7a44b;
        border-radius: 12px;
        padding: 1rem 1.1rem;
        box-shadow: 0 2px 8px rgba(16, 43, 78, 0.04);
    }

    [data-testid="stMetricLabel"] {
        color: #52657a;
    }

    [data-testid="stMetricValue"] {
        color: #153b60;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #dce3eb;
        border-radius: 10px;
        overflow: hidden;
    }

    div.stButton > button,
    div.stDownloadButton > button {
        border-radius: 8px;
        font-weight: 600;
    }

    .notice {
        background: #fffaf0;
        border-left: 4px solid #c7a44b;
        border-radius: 6px;
        padding: 0.9rem 1rem;
        color: #51472f;
        margin: 1rem 0;
    }

    .footer {
        color: #65758b;
        font-size: 0.85rem;
        border-top: 1px solid #dce3eb;
        padding-top: 1rem;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Cabeçalho
st.markdown("""
<div class="hero">
    <h1>⚖️ Decisões e Precedentes de Fiscalização</h1>
    <p>CREA-MS · Pesquisa de decisões administrativas para apoio à fiscalização</p>
</div>
""", unsafe_allow_html=True)

# Carregamento da base: prioriza a base compactada
gz = Path("dados/documentos.csv.gz")
csv = Path("dados/documentos.csv")

try:
    if gz.exists():
        df = pd.read_csv(
            gz,
            compression="gzip",
            keep_default_na=False,
            low_memory=False,
            encoding="utf-8-sig",
        )
    elif csv.exists():
        df = pd.read_csv(
            csv,
            keep_default_na=False,
            low_memory=False,
            encoding="utf-8-sig",
        )
    else:
        st.error(
            "Não foi encontrada a base de dados. "
            "Verifique os arquivos em dados/."
        )
        st.stop()
except Exception as exc:
    st.error(f"Falha ao carregar a base de dados: {exc}")
    st.stop()

if df.empty:
    st.warning("A base de decisões está vazia.")
    st.stop()

# Garantia das colunas esperadas
colunas = [
    "ano", "orgao", "titulo_documento", "url_documento",
    "texto_extraido", "triagem_automatica", "termos_encontrados",
    "trecho_relevante", "status_extracao",
]
for col in colunas:
    if col not in df.columns:
        df[col] = ""

df["ano_num"] = pd.to_numeric(
    df["ano"], errors="coerce"
).fillna(0).astype(int)

# Filtros
st.markdown(
    '<div class="section-title">Pesquisar decisões</div>',
    unsafe_allow_html=True,
)

with st.container(border=True):
    f1, f2, f3 = st.columns(3)

    with f1:
        years = sorted(
            [int(y) for y in df["ano_num"].unique() if y > 0],
            reverse=True,
        )
        year = st.selectbox("Ano da decisão", ["Todos"] + years)

    with f2:
        organs = sorted(
            [str(o) for o in df["orgao"].unique() if str(o).strip()]
        )
        organ = st.selectbox("Órgão julgador", ["Todos"] + organs)

    with f3:
        triages = sorted(
            [
                str(t)
                for t in df["triagem_automatica"].unique()
                if str(t).strip()
            ]
        )
        triage = st.selectbox(
            "Classificação automática", ["Todos"] + triages
        )

    query = st.text_input(
        "Pesquisar em qualquer decisão",
        placeholder=(
            "Digite um assunto, número de decisão, ART, registro, "
            "atribuições, empresa, nulidade ou nome..."
        ),
    )

    st.caption(
        "A pesquisa considera títulos, termos identificados, trechos "
        "relevantes e texto extraído dos PDFs disponíveis."
    )

# Aplicação dos filtros
filtered = df.copy()

if year != "Todos":
    filtered = filtered[filtered["ano_num"] == int(year)]

if organ != "Todos":
    filtered = filtered[filtered["orgao"] == organ]

if triage != "Todos":
    filtered = filtered[
        filtered["triagem_automatica"] == triage
    ]

if query.strip():
    q = query.strip().casefold()
    mask = pd.Series(False, index=filtered.index)

    for col in [
        "titulo_documento",
        "termos_encontrados",
        "trecho_relevante",
        "texto_extraido",
    ]:
        mask |= (
            filtered[col]
            .astype(str)
            .str.casefold()
            .str.contains(q, regex=False, na=False)
        )

    filtered = filtered[mask]

# Indicadores
st.markdown(
    '<div class="section-title">Resumo da consulta</div>',
    unsafe_allow_html=True,
)

c1, c2, c3 = st.columns(3)

c1.metric("Documentos encontrados", f"{len(filtered):,}".replace(",", "."))

candidatos = int(
    filtered["triagem_automatica"]
    .astype(str)
    .str.startswith("Analisar possível")
    .sum()
)
c2.metric("Candidatos para análise", f"{candidatos:,}".replace(",", "."))

sem_texto = int(
    filtered["status_extracao"]
    .astype(str)
    .str.contains("OCR", case=False, na=False)
    .sum()
)
c3.metric("Registros sinalizados para OCR", f"{sem_texto:,}".replace(",", "."))

# Exportação
st.download_button(
    "⬇️ Exportar resultados em CSV",
    filtered.drop(columns=["ano_num"], errors="ignore")
    .to_csv(index=False)
    .encode("utf-8-sig"),
    "consulta_decisoes_creams.csv",
    "text/csv",
)

# Tabela de resultados
st.markdown(
    '<div class="section-title">Resultados da pesquisa</div>',
    unsafe_allow_html=True,
)

if len(filtered):
    tabela = filtered[
        [
            "ano",
            "orgao",
            "titulo_documento",
            "triagem_automatica",
            "termos_encontrados",
            "url_documento",
        ]
    ].copy()

    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True,
        height=430,
        column_config={
            "ano": st.column_config.NumberColumn("Ano", format="%d"),
            "orgao": st.column_config.TextColumn("Órgão"),
            "titulo_documento": st.column_config.TextColumn(
                "Título da decisão", width="large"
            ),
            "triagem_automatica": st.column_config.TextColumn(
                "Classificação", width="medium"
            ),
            "termos_encontrados": st.column_config.TextColumn(
                "Termos identificados", width="medium"
            ),
            "url_documento": st.column_config.LinkColumn(
                "Documento oficial",
                display_text="Abrir documento",
            ),
        },
    )

    # Detalhes da decisão
    st.markdown(
        '<div class="section-title">Consultar uma decisão</div>',
        unsafe_allow_html=True,
    )

    ids = filtered.index.tolist()
    selected = st.selectbox(
        "Selecione o documento para consultar os detalhes",
        ids,
        format_func=lambda i: (
            f'{filtered.loc[i, "ano"]} | '
            f'{filtered.loc[i, "orgao"]} | '
            f'{filtered.loc[i, "titulo_documento"]}'
        ),
    )

    row = filtered.loc[selected]

    with st.container(border=True):
        st.subheader(str(row["titulo_documento"]))

        st.write(
            f'**Ano:** {row["ano"] or "Não informado"}  ·  '
            f'**Órgão:** {row["orgao"] or "Não informado"}'
        )

        if str(row["url_documento"]).strip():
            st.link_button(
                "Abrir documento oficial",
                str(row["url_documento"]),
            )

        st.write("**Classificação automática**")
        st.write(row["triagem_automatica"] or "Não classificado")

        st.write("**Termos identificados**")
        st.write(row["termos_encontrados"] or "Nenhum termo sinalizador")

        with st.expander("Trecho relevante"):
            st.text_area(
                "Trecho extraído",
                str(row["trecho_relevante"]),
                height=150,
                key=f"trecho_{selected}",
            )

        with st.expander("Texto integral extraído do PDF"):
            texto = str(row["texto_extraido"])
            if texto.strip():
                st.text_area(
                    "Conteúdo textual do documento",
                    texto,
                    height=420,
                    key=f"texto_{selected}",
                )
            else:
                st.info(
                    "Não há texto extraído para este documento. "
                    "Pode ser necessário aplicar OCR ao PDF."
                )

else:
    st.info(
        "Nenhuma decisão corresponde aos filtros informados. "
        "Tente alterar o ano, o órgão ou os termos pesquisados."
    )

# Nota técnica e rodapé
st.markdown("""
<div class="notice">
<strong>Nota de utilização:</strong> a classificação automática é
indicativa e não representa conclusão jurídica. Confirme o teor e o
contexto no documento oficial antes de utilizar um precedente.
</div>
<div class="footer">
CREA-MS · Ferramenta de apoio à pesquisa de decisões públicas.
A disponibilidade de texto depende da qualidade e da extração dos PDFs.
</div>
""", unsafe_allow_html=True)
