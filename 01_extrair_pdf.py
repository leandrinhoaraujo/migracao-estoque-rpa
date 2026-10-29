"""
Etapa 1: Extração e Estruturação de Dados do PDF
------------------------------------------------
Lê relatórios e catálogos em formato PDF (inclusive com dezenas de páginas),
extraindo os itens e tabelas de preços para planilhas limpas (Excel/CSV).
"""

import sys
import re
from pathlib import Path
import pdfplumber
import pandas as pd
from config import PDF_ENTRADA, EXCEL_ESTOQUE_EXTRAIDO, CSV_ESTOQUE_EXTRAIDO

def extrair_catalogo_pdf(caminho_pdf=None, salvar_excel=None, salvar_csv=None):
    caminho = Path(caminho_pdf) if caminho_pdf else PDF_ENTRADA
    saida_excel = Path(salvar_excel) if salvar_excel else EXCEL_ESTOQUE_EXTRAIDO
    saida_csv = Path(salvar_csv) if salvar_csv else CSV_ESTOQUE_EXTRAIDO

    if not caminho.exists():
        print(f"[ERRO] Arquivo PDF não encontrado: {caminho}")
        print("Coloque o PDF na pasta 'data/' ou informe o caminho como argumento:")
        print("Exemplo: python 01_extrair_pdf.py meu_arquivo.pdf")
        return None

    # Padrão para identificar início de linha com código (ex: 1234-5) e números no padrão BR
    item_pattern = re.compile(r"^(\d+-\d+)\s+(.*)")
    num_pattern = re.compile(r'^-?\d{1,3}(?:\.\d{3})*,\d{2}$')

    rows = []
    print(f"[*] Iniciando extração do PDF: {caminho.name}")

    with pdfplumber.open(caminho) as pdf:
        total_paginas = len(pdf.pages)
        print(f"[*] Total de páginas detectadas: {total_paginas}")

        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")
            for line in lines:
                line = line.strip()
                m = item_pattern.match(line)
                if not m:
                    continue

                item_code = m.group(1)
                rest = m.group(2).strip()
                tokens = rest.split()

                # As últimas 6 colunas numéricas contêm os valores da tabela
                # [Estoque, Preço Custo, Preço Venda, Total Custo, Total Venda, Margem %]
                if len(tokens) >= 8:
                    estoque, preco_custo, preco_venda, tot_custo, tot_venda, pct = tokens[-6:]

                    if (num_pattern.match(pct) and num_pattern.match(tot_venda) and
                        num_pattern.match(tot_custo) and num_pattern.match(preco_venda) and
                        num_pattern.match(preco_custo) and num_pattern.match(estoque)):

                        middle = tokens[:-6]

                        # Primeiro token opcionalmente é o código numérico/barras interno
                        numero = middle[0] if (middle and middle[0].isdigit()) else ""
                        if numero:
                            middle = middle[1:]

                        # Identifica NCM e Unidade no final dos tokens intermediários
                        if len(middle) >= 2:
                            if middle[-1] == '.' and len(middle) >= 3 and middle[-2] == '.':
                                ncm = ". ."
                                unidade = middle[-3]
                                desc_tokens = middle[:-3]
                            elif re.match(r'^\d{4}\.\d{2}\.\d{2}$', middle[-1]) or middle[-1].replace('.', '').isdigit():
                                ncm = middle[-1]
                                unidade = middle[-2]
                                desc_tokens = middle[:-2]
                            else:
                                ncm = middle[-1]
                                unidade = middle[-2] if len(middle) >= 2 else ""
                                desc_tokens = middle[:-2]
                        else:
                            ncm = ""
                            unidade = ""
                            desc_tokens = middle

                        descricao = " ".join(desc_tokens).strip()

                        rows.append({
                            "Item": item_code,
                            "Numero": numero,
                            "Descricao": descricao,
                            "Unidade": unidade,
                            "NCM": ncm,
                            "Estoque": estoque,
                            "Preco_Custo": preco_custo,
                            "Preco_Venda": preco_venda,
                            "Total_Custo": tot_custo,
                            "Total_Venda": tot_venda,
                            "Margem_Pct": pct,
                            "Pagina": page_num
                        })

    if not rows:
        print("[!] Nenhum item identificado com o padrão esperado.")
        return None

    df = pd.DataFrame(rows)
    saida_excel.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(saida_excel, index=False)
    df.to_csv(saida_csv, index=False, sep=";", encoding="utf-8-sig")

    print(f"[OK] Sucesso! {len(df)} produtos extraídos do PDF.")
    print(f" -> Planilha salva em: {saida_excel}")
    print(f" -> CSV salvo em: {saida_csv}")
    return df

if __name__ == "__main__":
    param_pdf = sys.argv[1] if len(sys.argv) > 1 else None
    extrair_catalogo_pdf(param_pdf)
