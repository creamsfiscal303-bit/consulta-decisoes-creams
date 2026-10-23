from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Decisões e Precedentes — CREA-MS", layout="wide")
st.title("Decisões e Precedentes de Fiscalização — CREA-MS")
st.caption("Índice de documentos públicos. A triagem automática é indicativa; confira sempre a decisão original.")

DATA = Path("dados/documentos.csv")
if not DATA.exists():
    st.error("A base dados/documentos.csv não foi encontrada. Envie o CSV para a pasta dados do GitHub.")
    st.stop()

try:
    df = pd.read_csv(DATA, keep_default_na=False, low_memory=False, encoding="utf-8-sig")
except Exception as e:
    st.error(f"Não foi possível ler a base CSV: {e}")
    st.stop()

if df.empty:
    st.warning("O arquivo CSV está vazio.")
    st.stop()

for col in ["ano", "orgao", "titulo_documento", "url_documento",
            "status_extracao", "triagem_automatica", "termos_encontrados",
            "trecho_relevante"]:
    if col not in df.columns:
        df[col] = ""

# A base otimizada não inclui o texto integral dos PDFs.
df["ano_num"] = pd.to_numeric(df["ano"], errors="coerce").fillna(0).astype(int)

a, b, c = st.columns(3)
with a:
    years = sorted([int(y) for y in df["ano_num"].unique() if y > 0], reverse=True)
    year = st.selectbox("Ano", ["Todos"] + years)
with b:
    organs = sorted([str(o) for o in df["orgao"].unique() if str(o).strip()])
    organ = st.selectbox("Órgão", ["Todos"] + organs)
with c:
    triages = ["Todos"] + sorted([str(t) for t in df["triagem_automatica"].unique() if str(t).strip()])
    triage = st.selectbox("Triagem", triages)

query = st.text_input(
    "Pesquisar por título, termos encontrados ou trecho relevante",
    placeholder="Ex.: nulidade, auto de infração, falta de fundamentação, ART"
)

filtered = df.copy()
if year != "Todos":
    filtered = filtered[filtered["ano_num"] == int(year)]
if organ != "Todos":
    filtered = filtered[filtered["orgao"] == organ]
if triage != "Todos":
    filtered = filtered[filtered["triagem_automatica"] == triage]

if query.strip():
    q = query.casefold()
    mask = (
        filtered["titulo_documento"].astype(str).str.casefold().str.contains(q, na=False)
        | filtered["termos_encontrados"].astype(str).str.casefold().str.contains(q, na=False)
        | filtered["trecho_relevante"].astype(str).str.casefold().str.contains(q, na=False)
    )
    filtered = filtered[mask]

m1, m2, m3 = st.columns(3)
m1.metric("Documentos filtrados", len(filtered))
m2.metric(
    "Candidatos a nulidade/arquivamento",
    int(filtered["triagem_automatica"].astype(str).str.startswith("Analisar possível").sum())
)
m3.metric(
    "PDFs sem texto extraível",
    int(filtered["status_extracao"].astype(str).str.contains("OCR", case=False, na=False).sum())
)

csv = filtered.drop(columns=["ano_num"], errors="ignore").to_csv(index=False).encode("utf-8-sig")
st.download_button("Exportar resultado filtrado (CSV)", csv, "consulta_creams.csv", "text/csv")

st.dataframe(
    filtered[["ano", "orgao", "titulo_documento", "triagem_automatica",
              "termos_encontrados", "url_documento"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "url_documento": st.column_config.LinkColumn("Decisão original", display_text="Abrir documento")
    }
)

st.subheader("Analisar documento")
if len(filtered):
    ids = filtered.index.tolist()
    chosen = st.selectbox(
        "Selecione um documento",
        ids,
        format_func=lambda i: (
            f'{filtered.loc[i, "ano"]} | {filtered.loc[i, "orgao"]} | '
            f'{filtered.loc[i, "titulo_documento"]}'
        )
    )
    row = filtered.loc[chosen]
    st.markdown(f'**Documento oficial:** [{row["titulo_documento"]}]({row["url_documento"]})')
    st.write("**Triagem:**", row["triagem_automatica"])
    st.write("**Termos sinalizadores:**", row["termos_encontrados"] or "Nenhum")
    st.text_area("Trecho indicativo", str(row["trecho_relevante"]), height=160)
else:
    st.info("Nenhum documento corresponde aos filtros.")

st.warning(
    "A base publicada contém campos resumidos, não o texto integral dos PDFs. "
    "A busca não encontrará termos que apareçam somente no corpo completo do documento. "
    "A presença de palavras como 'nulidade' ou 'arquivamento' não prova que o auto foi anulado. "
    "Leia a decisão oficial no link."
)
