from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Decisões e Precedentes — CREA-MS", layout="wide")
st.title("Decisões e Precedentes de Fiscalização — CREA-MS")
st.caption("Consulta ampla às decisões públicas. A triagem automática é indicativa; confirme sempre o documento oficial.")

gz = Path("dados/documentos.csv.gz")
csv = Path("dados/documentos.csv")
try:
    if gz.exists():
        df = pd.read_csv(gz, compression="gzip", keep_default_na=False, low_memory=False, encoding="utf-8-sig")
    elif csv.exists():
        df = pd.read_csv(csv, keep_default_na=False, low_memory=False, encoding="utf-8-sig")
    else:
        st.error("Não encontrei dados/documentos.csv.gz nem dados/documentos.csv no repositório.")
        st.stop()
except Exception as exc:
    st.error(f"Falha ao carregar a base: {exc}")
    st.stop()

if df.empty:
    st.warning("A base está vazia.")
    st.stop()

for col in ["ano","orgao","titulo_documento","url_documento","texto_extraido",
            "triagem_automatica","termos_encontrados","trecho_relevante","status_extracao"]:
    if col not in df.columns: df[col] = ""
df["ano_num"] = pd.to_numeric(df["ano"], errors="coerce").fillna(0).astype(int)

c1,c2,c3 = st.columns(3)
with c1:
    years = sorted([int(y) for y in df["ano_num"].unique() if y > 0], reverse=True)
    year = st.selectbox("Ano", ["Todos"] + years)
with c2:
    organs = sorted([str(o) for o in df["orgao"].unique() if str(o).strip()])
    organ = st.selectbox("Órgão", ["Todos"] + organs)
with c3:
    triages = ["Todos"] + sorted([str(t) for t in df["triagem_automatica"].unique() if str(t).strip()])
    triage = st.selectbox("Classificação automática", triages)

query = st.text_input("Pesquisar em qualquer decisão",
    placeholder="Ex.: número da decisão, ART, registro, atribuições, empresa, nulidade, nome...")
filtered = df.copy()
if year != "Todos": filtered = filtered[filtered["ano_num"] == int(year)]
if organ != "Todos": filtered = filtered[filtered["orgao"] == organ]
if triage != "Todos": filtered = filtered[filtered["triagem_automatica"] == triage]
if query.strip():
    q = query.casefold()
    mask = pd.Series(False, index=filtered.index)
    for col in ["titulo_documento","termos_encontrados","trecho_relevante","texto_extraido"]:
        mask |= filtered[col].astype(str).str.casefold().str.contains(q, regex=False, na=False)
    filtered = filtered[mask]

a,b,c = st.columns(3)
a.metric("Documentos encontrados", len(filtered))
b.metric("Candidatos a nulidade/arquivamento", int(filtered["triagem_automatica"].astype(str).str.startswith("Analisar possível").sum()))
c.metric("PDFs sem texto extraível", int(filtered["status_extracao"].astype(str).str.contains("OCR", case=False, na=False).sum()))
st.download_button("Exportar resultado filtrado (CSV)",
    filtered.drop(columns=["ano_num"], errors="ignore").to_csv(index=False).encode("utf-8-sig"),
    "consulta_decisoes_creams.csv", "text/csv")
st.dataframe(filtered[["ano","orgao","titulo_documento","triagem_automatica","termos_encontrados","url_documento"]],
    use_container_width=True, hide_index=True,
    column_config={"url_documento": st.column_config.LinkColumn("Decisão original", display_text="Abrir documento")})

st.subheader("Detalhes da decisão")
if len(filtered):
    ids = filtered.index.tolist()
    selected = st.selectbox("Selecione uma decisão", ids,
        format_func=lambda i: f'{filtered.loc[i, "ano"]} | {filtered.loc[i, "orgao"]} | {filtered.loc[i, "titulo_documento"]}')
    row = filtered.loc[selected]
    st.markdown(f'**Documento oficial:** [{row["titulo_documento"]}]({row["url_documento"]})')
    st.write("**Classificação automática:**", row["triagem_automatica"])
    st.write("**Termos encontrados:**", row["termos_encontrados"] or "Nenhum termo sinalizador")
    st.text_area("Trecho relevante", str(row["trecho_relevante"]), height=150)
    with st.expander("Texto integral extraído do PDF"):
        st.text_area("Texto integral", str(row["texto_extraido"]), height=420, key=f"texto_{selected}")
else:
    st.info("Nenhuma decisão corresponde aos filtros.")
st.info("A pesquisa considera o texto extraído disponível. PDFs digitalizados sem camada de texto podem exigir OCR. A classificação automática não determina, por si só, o resultado jurídico.")
