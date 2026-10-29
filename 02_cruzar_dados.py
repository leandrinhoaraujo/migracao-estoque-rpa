"""
Etapa 2: Cruzamento Inteligente de Dados (Fuzzy & Part-Number Matching)
----------------------------------------------------------------------
Cruza os produtos exportados do sistema ERP com os dados extraídos do catálogo/PDF.
Aplica algoritmos de normalização de texto e correspondência exata de part-number
para separar itens com 100% de certeza e itens com divergência para revisão manual.
"""

import sys
import re
from pathlib import Path
import pandas as pd
from config import EXCEL_ESTOQUE_EXTRAIDO, EXCEL_SISTEMA, EXCEL_CRUZAMENTO_FINAL

def clean_text(s):
    if not isinstance(s, str):
        return ""
    return s.strip().upper()

def executar_cruzamento(caminho_sistema=None, caminho_catalogo=None, saida_excel=None):
    arq_sistema = Path(caminho_sistema) if caminho_sistema else EXCEL_SISTEMA
    arq_catalogo = Path(caminho_catalogo) if caminho_catalogo else EXCEL_ESTOQUE_EXTRAIDO
    arq_saida = Path(saida_excel) if saida_excel else EXCEL_CRUZAMENTO_FINAL

    if not arq_catalogo.exists():
        print(f"[ERRO] Planilha de catálogo extraído não encontrada: {arq_catalogo}")
        print("Execute primeiro a 'Etapa 1' (01_extrair_pdf.py).")
        return None

    if not arq_sistema.exists():
        print(f"[ERRO] Planilha exportada do sistema não encontrada: {arq_sistema}")
        print("Exporte a planilha do seu ERP e coloque em 'data/' ou passe o caminho como argumento.")
        return None

    print(f"[*] Carregando dados do catálogo: {arq_catalogo.name}")
    df_cat = pd.read_excel(arq_catalogo)

    print(f"[*] Carregando dados do sistema ERP: {arq_sistema.name}")
    df_sys_raw = pd.read_excel(arq_sistema)

    # Identifica cabeçalhos e coluna de produto
    if 'Produto' in df_sys_raw.columns:
        df_sys = df_sys_raw.copy()
    else:
        df_sys = df_sys_raw.iloc[1:].copy()
        df_sys.columns = [str(c) for c in df_sys_raw.iloc[0]]

    col_prod = [c for c in df_sys.columns if 'PRODUTO' in str(c).upper() or 'DESCRI' in str(c).upper()]
    nome_col_prod = col_prod[0] if col_prod else df_sys.columns[0]

    df_cat['clean_desc'] = df_cat['Descricao'].apply(clean_text)
    df_sys['clean_prod'] = df_sys[nome_col_prod].apply(clean_text)

    matched_rows = []
    manual_rows = []

    print("[*] Iniciando algoritmo de correspondência...")

    for idx, sys_row in df_sys.iterrows():
        sys_name = sys_row['clean_prod']
        if not sys_name:
            continue

        sys_tokens_norm = [re.sub(r'[\s/]+', '', t) for t in sys_name.split()]
        sys_norm = re.sub(r'[\s/]+', '', sys_name)

        found = []
        for _, cat_row in df_cat.iterrows():
            cat_desc = cat_row['clean_desc']
            if len(cat_desc) < 3:
                continue
            cat_norm = re.sub(r'[\s/]+', '', cat_desc)

            # Bate se o código/modelo estiver nos tokens do produto do sistema
            if cat_norm in sys_tokens_norm:
                found.append(cat_row)
            elif len(cat_norm) >= 5 and cat_norm in sys_norm:
                found.append(cat_row)

        if len(found) == 1:
            chosen = found[0]
            matched_rows.append({
                "Produto_Sistema": sys_row[nome_col_prod],
                "Descricao_Catalogo": chosen['Descricao'],
                "Item_Catalogo": chosen['Item'],
                "Preco_Custo_Novo": chosen['Preco_Custo'],
                "Preco_Venda_Novo": chosen['Preco_Venda'],
                "Estoque_Catalogo": chosen.get('Estoque', ''),
                "Status": "100% CONFIRMADO (CÓDIGO ÚNICO)"
            })
        elif len(found) > 1:
            # Desempate pelo match mais específico
            best = None
            for cand in found:
                cand_norm = re.sub(r'[\s/]+', '', cand['clean_desc'])
                if cand_norm in sys_tokens_norm:
                    if best is None or len(cand_norm) > len(re.sub(r'[\s/]+', '', best['clean_desc'])):
                        best = cand

            if best is not None:
                matched_rows.append({
                    "Produto_Sistema": sys_row[nome_col_prod],
                    "Descricao_Catalogo": best['Descricao'],
                    "Item_Catalogo": best['Item'],
                    "Preco_Custo_Novo": best['Preco_Custo'],
                    "Preco_Venda_Novo": best['Preco_Venda'],
                    "Estoque_Catalogo": best.get('Estoque', ''),
                    "Status": "100% CONFIRMADO (MATCH EXATO DE CÓDIGO)"
                })
            else:
                manual_rows.append({
                    "Produto_Sistema": sys_row[nome_col_prod],
                    "Motivo": f"Múltiplas opções encontradas no catálogo ({len(found)})",
                    "Opcoes_Encontradas": "; ".join([f['Descricao'] for f in found[:4]])
                })
        else:
            manual_rows.append({
                "Produto_Sistema": sys_row[nome_col_prod],
                "Motivo": "Não encontrado no catálogo ou descrição divergente",
                "Opcoes_Encontradas": ""
            })

    df_matched = pd.DataFrame(matched_rows)
    df_manual = pd.DataFrame(manual_rows)

    arq_saida.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(arq_saida, engine='openpyxl') as writer:
        df_matched.to_excel(writer, sheet_name='AUTOMATIZAR (100% CERTEZA)', index=False)
        df_manual.to_excel(writer, sheet_name='FAZER MANUAL', index=False)

    print("\n" + "="*50)
    print("RESULTADO DO CRUZAMENTO")
    print("="*50)
    print(f"Total produtos analisados : {len(df_sys)}")
    print(f"Itens 100% Confirmados    : {len(df_matched)} ({len(df_matched)/len(df_sys)*100:.1f}%)")
    print(f"Itens para Revisão Manual : {len(df_manual)} ({len(df_manual)/len(df_sys)*100:.1f}%)")
    print(f"Planilha consolidada salva: {arq_saida}")
    return df_matched, df_manual

if __name__ == "__main__":
    param_sys = sys.argv[1] if len(sys.argv) > 1 else None
    param_cat = sys.argv[2] if len(sys.argv) > 2 else None
    executar_cruzamento(param_sys, param_cat)
