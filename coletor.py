from __future__ import annotations
import hashlib, re, time
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin, urlparse
import pandas as pd
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

BASE = "https://transparencia.creams.org.br"
COLEGIADOS = BASE + "/transparencia_crea/colegiados/"
PLENARIO = BASE + "/transparencia_crea/decisoes-plenarias/"
OUT = Path("dados")
PDF_DIR = OUT / "pdfs"
OUT.mkdir(exist_ok=True)
PDF_DIR.mkdir(exist_ok=True)
DB_GZ, DB_CSV = OUT / "documentos.csv.gz", OUT / "documentos.csv"
TIMEOUT = 40
S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0 (compatible; ConsultaPublicaCREAMS/2.0)"})
TERMS = ["nulidade","nulo","nula","anulação","anulado","anulada","arquivamento","arquivar",
         "insubsistência","insubsistente","vício formal","falta de fundamentação",
         "cerceamento de defesa","descrição dos fatos","dispositivo legal","auto de infração"]

def get(url):
    try:
        r = S.get(url, timeout=TIMEOUT); r.raise_for_status(); return r
    except Exception as e:
        print(f"[AVISO] {url} :: {e}"); return None

def clean(s): return re.sub(r"\s+", " ", s or "").strip()

def pdf_text(data):
    try:
        reader = PdfReader(BytesIO(data))
        return "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    except Exception as e:
        print(f"[AVISO] Falha na extração do PDF: {e}"); return ""

def save_pdf(url, data):
    p = PDF_DIR / (hashlib.sha1(url.encode()).hexdigest()[:18] + ".pdf")
    if not p.exists(): p.write_bytes(data)
    return str(p)

def links_from_page(url):
    r = get(url)
    if not r: return [], ""
    soup = BeautifulSoup(r.text, "html.parser")
    title = clean(soup.title.get_text(" ", strip=True) if soup.title else "")
    found = []
    for a in soup.select("a[href]"):
        label = clean(a.get_text(" ", strip=True)); href = urljoin(url, a["href"])
        if urlparse(href).netloc != urlparse(BASE).netloc or href == url: continue
        found.append((label, href))
    return list(dict.fromkeys(found)), title


def discover_index_pages():
    """Descobre páginas anuais disponíveis a partir de 2025."""
    found = []

    for index_url in (COLEGIADOS, PLENARIO):
        links, _ = links_from_page(index_url)

        for label, url in links:
            m = re.search(r"\b(20\d{2})\b", label)
            low = label.casefold()

            if not m or not any(
                x in low for x in ("decis", "plenari", "plenári")
            ):
                continue

            year = int(m.group(1))

            # Ignora páginas anteriores a 2025
            if year < 2025:
                continue

            om = re.search(r"\b(CEA|CEECA|CEEEM|CEEST)\b", label, re.I)

            organ = (
                "Plenário"
                if ("plenari" in low or "plenári" in low)
                else (om.group(1).upper() if om else "Câmara/Colegiado")
            )

            found.append({
                "orgao": organ,
                "ano": year,
                "pagina": url,
                "rotulo": label,
            })

    unique = {item["pagina"]: item for item in found}
    return list(unique.values())


def discover_pdf_records():
    pages = discover_index_pages(); docs = []
    for pg in pages:
        print(f'[PÁGINA] {pg["orgao"]} {pg["ano"]}: {pg["pagina"]}')
        links, _ = links_from_page(pg["pagina"])
        for label, url in links:
            if ".pdf" in url.lower().split("?")[0]:
                docs.append({"ano": pg["ano"], "orgao": pg["orgao"],
                    "titulo_documento": label or Path(urlparse(url).path).name,
                    "url_documento": url, "pagina_origem": pg["pagina"], "tipo_documento": "PDF"})
            elif re.search(r"decis|sessão|sessao|reunião|reuniao|colegiad", label, re.I):
                sublinks, _ = links_from_page(url)
                for label2, url2 in sublinks:
                    if ".pdf" in url2.lower().split("?")[0]:
                        docs.append({"ano": pg["ano"], "orgao": pg["orgao"],
                            "titulo_documento": label2 or label or Path(urlparse(url2).path).name,
                            "url_documento": url2, "pagina_origem": url, "tipo_documento": "PDF"})
        time.sleep(0.1)
    # Additional discovery for plenary yearly pages.

links, _ = links_from_page(PLENARIO)
for label, url in links:
    m = re.search(r"\b(20\d{2})\b", label)
    if not m or "decis" not in label.casefold():
        continue
    year = int(m.group(1))
    if year < 2025:
        continue
    sublinks, _ = links_from_page(url)

        for title, pdf_url in sublinks:
            if ".pdf" in pdf_url.lower().split("?")[0]:
                docs.append({"ano": year, "orgao": "Plenário",
                    "titulo_documento": title or Path(urlparse(pdf_url).path).name,
                    "url_documento": pdf_url, "pagina_origem": url, "tipo_documento": "PDF"})
    unique = {}
    for d in docs:
        key = d["url_documento"]
        if key not in unique or (unique[key]["orgao"] == "Câmara/Colegiado" and d["orgao"] != "Câmara/Colegiado"):
            unique[key] = d
    return list(unique.values()), pages

def classify(text):
    low = (text or "").casefold(); matched = [t for t in TERMS if t in low]
    ai = any(x in low for x in ("auto de infração","auto de infracao","processo de fiscalização","processo de fiscalizacao"))
    disposition = any(x in low for x in ("nulidade","nulo","nula","anulação","anulado","anulada","arquivamento","insubsistência","insubsistente"))
    cat = "Analisar possível nulidade/arquivamento" if ai and disposition else ("Revisar documento: termo relevante encontrado" if matched else "Sem termo sinalizador")
    return cat, "; ".join(matched)

def snippet(text, terms, width=260):
    if not text: return ""
    low = text.casefold(); positions = [low.find(t.casefold()) for t in terms if low.find(t.casefold()) >= 0]
    if not positions: return re.sub(r"\s+", " ", text[:width]).strip()
    i = min(positions); return re.sub(r"\s+", " ", text[max(0, i-100):i+width]).strip()

def load_existing():
    if DB_GZ.exists():
        print(f"[INFO] Reutilizando base compactada {DB_GZ}")
        return pd.read_csv(DB_GZ, compression="gzip", keep_default_na=False, low_memory=False, encoding="utf-8-sig")
    if DB_CSV.exists():
        print(f"[INFO] Importando base CSV existente {DB_CSV}")
        return pd.read_csv(DB_CSV, keep_default_na=False, low_memory=False, encoding="utf-8-sig")
    print("[INFO] Base anterior não encontrada; será criada nova.")
    return pd.DataFrame()

def main():
    existing = load_existing()
    old_urls = set(existing["url_documento"].astype(str)) if not existing.empty and "url_documento" in existing.columns else set()
    records, pages = discover_pdf_records()
    print(f"[INFO] Páginas anuais: {len(pages)}; PDFs encontrados: {len(records)}")
    new_records = [d for d in records if d["url_documento"] not in old_urls]
    print(f"[INFO] Já cadastrados: {len(old_urls)}; novos para processar: {len(new_records)}")
    new_docs = []
    for i, d in enumerate(new_records, 1):
        print(f'[PDF {i}/{len(new_records)}] {d["titulo_documento"]}')
        r = get(d["url_documento"]); data = b""; path = ""; txt = ""
        if r and (r.content[:4] == b"%PDF" or "pdf" in r.headers.get("content-type", "").lower()):
            data = r.content; path = save_pdf(d["url_documento"], data); txt = pdf_text(data)
        status = "Texto extraído" if txt else ("PDF sem texto extraível/OCR necessário" if data else "Falha no download")
        category, terms = classify(txt)
        d.update({"texto_extraido": txt[:150000], "arquivo_local": path, "status_extracao": status,
            "triagem_automatica": category, "termos_encontrados": terms,
            "trecho_relevante": snippet(txt, terms.split("; ") if terms else TERMS),
            "hash_conteudo": hashlib.sha256(data).hexdigest() if data else ""})
        new_docs.append(d); time.sleep(0.1)
    new_df = pd.DataFrame(new_docs)
    if existing.empty: combined = new_df
    elif new_df.empty: combined = existing
    else: combined = pd.concat([existing, new_df], ignore_index=True, sort=False)
    if not combined.empty and "url_documento" in combined.columns:
        combined = combined.drop_duplicates(subset=["url_documento"], keep="last")
    combined.to_csv(DB_GZ, index=False, encoding="utf-8-sig", compression={"method": "gzip", "mtime": 0})
    pd.DataFrame(pages).to_csv(OUT / "fontes_anuais.csv", index=False, encoding="utf-8-sig")
    print(f"[OK] Total na base: {len(combined)}; novos nesta execução: {len(new_docs)}")
    print(f"[OK] Base compactada: {DB_GZ} ({DB_GZ.stat().st_size / (1024*1024):.2f} MB)")
    print("[INFO] O CSV original não foi alterado; triagem automática exige conferência oficial.")

if __name__ == "__main__":
    main()
