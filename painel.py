from pathlib import Path
import pandas as pd
import streamlit as st
st.set_page_config(page_title="Precedentes de Fiscalização — CREA-MS",layout="wide")
st.title("Decisões e Precedentes de Fiscalização — CREA-MS")
st.caption("Índice local de documentos públicos. A triagem de nulidades é automática e deve ser validada pela leitura da decisão.")
p=Path("dados/documentos.csv")
if not p.exists():
    st.warning("Ainda não há dados. Execute atualizar.bat."); st.stop()
df=pd.read_csv(p,keep_default_na=False)
if df.empty:
    st.info("Nenhum documento foi indexado. Confira a saída do coletor."); st.stop()
for c in ["ano","orgao","titulo_documento","url_documento","texto_extraido","triagem_automatica","termos_encontrados","trecho_relevante","status_extracao"]:
    if c not in df: df[c]=""
df["ano_num"]=pd.to_numeric(df["ano"],errors="coerce").fillna(0).astype(int)
a,b,c=st.columns(3)
with a:
    ys=sorted([int(y) for y in df.ano_num.unique() if y>0],reverse=True)
    yr=st.selectbox("Ano",["Todos"]+ys)
with b:
    orgs=sorted([o for o in df.orgao.unique() if o])
    org=st.selectbox("Órgão",["Todos"]+orgs)
with c:
    mode=st.selectbox("Triagem",["Todos","Analisar possível nulidade/arquivamento","Revisar documento: termo relevante encontrado"])
q=st.text_input("Pesquisar no texto ou título",placeholder="nulidade, auto de infração, falta de fundamentação, ART...")
x=df.copy()
if yr!="Todos": x=x[x.ano_num==int(yr)]
if org!="Todos": x=x[x.orgao==org]
if mode!="Todos": x=x[x.triagem_automatica==mode]
if q.strip():
    qq=q.casefold()
    x=x[x.titulo_documento.astype(str).str.casefold().str.contains(qq,na=False)|x.texto_extraido.astype(str).str.casefold().str.contains(qq,na=False)|x.termos_encontrados.astype(str).str.casefold().str.contains(qq,na=False)]
k1,k2,k3=st.columns(3)
k1.metric("Documentos filtrados",len(x))
k2.metric("Candidatos a nulidade/arquivamento",int(x.triagem_automatica.str.startswith("Analisar possível").sum()))
k3.metric("Sem texto extraível",int(x.status_extracao.str.contains("OCR",case=False).sum()))
st.download_button("Exportar resultado filtrado CSV",x.drop(columns=["ano_num"],errors="ignore").to_csv(index=False).encode("utf-8-sig"),"consulta_creams.csv","text/csv")
st.dataframe(x[["ano","orgao","titulo_documento","triagem_automatica","termos_encontrados","url_documento"]],use_container_width=True,hide_index=True,
 column_config={"url_documento":st.column_config.LinkColumn("Decisão original",display_text="Abrir documento")})
st.subheader("Analisar decisão")
if len(x):
    ids=x.index.tolist()
    i=st.selectbox("Documento",ids,format_func=lambda j:f'{x.loc[j,"ano"]} | {x.loc[j,"orgao"]} | {x.loc[j,"titulo_documento"]}')
    r=x.loc[i]
    st.markdown(f'**Documento original:** [{r["titulo_documento"]}]({r["url_documento"]})')
    st.write("**Triagem automática:**",r["triagem_automatica"])
    st.write("**Termos sinalizadores:**",r["termos_encontrados"] or "Nenhum")
    st.text_area("Trecho indicativo",str(r["trecho_relevante"]),height=120)
    st.text_area("Texto extraído",str(r["texto_extraido"]),height=360)
st.info("Não trate a presença das palavras 'nulidade', 'nulo' ou 'arquivamento' como conclusão automática. A decisão pode mencionar nulidade para afastá-la, citar precedente ou tratar de assunto diferente.")
