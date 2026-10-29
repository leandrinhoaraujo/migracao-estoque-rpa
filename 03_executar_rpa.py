"""
Etapa 3: Automação RPA de Digitação em Sistema Desktop
------------------------------------------------------
Simula a interação com telas de cadastro/grades de dados (ex: DevExpress Grid),
filtrando os produtos e inserindo os preços de Custo, Custo Inicial e Venda.

REGRAS DE SEGURANÇA:
1. FAILSAFE ativo: mover o mouse para qualquer canto da tela aborta o robô na hora.
2. O robô NUNCA clica no botão "Gravar". A gravação permanece sob decisão humana.
3. Controle de lotes e log de progresso para evitar duplicidade.
"""

import sys
import os
import time
import ctypes
from pathlib import Path
import pandas as pd
import pyautogui
import pyperclip
from config import (
    EXCEL_CRUZAMENTO_FINAL, ARQUIVO_LOG_PROCESSADOS,
    TEMPO_FILTRO_SEGUNDOS, QTD_SHIFT_TABS_RETORNO,
    TAMANHO_LOTE_PADRAO, PAUSA_ENTRE_COMANDOS
)

def conectar_desktop_interativo():
    """Garante foco e permissão de entrada no desktop interativo do Windows."""
    try:
        GENERIC_ALL = 0x10000000
        hdesk = ctypes.windll.user32.OpenDesktopW('default', 0, False, GENERIC_ALL)
        if hdesk:
            ctypes.windll.user32.SetThreadDesktop(hdesk)
    except Exception as e:
        print(f"[AVISO] Não foi possível redefinir o desktop do thread: {e}")

def carregar_itens_pendentes(planilha=None):
    caminho = Path(planilha) if planilha else EXCEL_CRUZAMENTO_FINAL
    if not caminho.exists():
        print(f"[ERRO] Planilha de dados confirmados não encontrada: {caminho}")
        print("Execute primeiro a 'Etapa 2' (02_cruzar_dados.py).")
        return []

    df = pd.read_excel(caminho, sheet_name=0)
    processados = set()

    if ARQUIVO_LOG_PROCESSADOS.exists():
        with open(ARQUIVO_LOG_PROCESSADOS, "r", encoding="utf-8") as f:
            processados = set(line.strip() for line in f if line.strip())

    itens = []
    for _, row in df.iterrows():
        nome = str(row['Produto_Sistema']).strip()
        if nome not in processados:
            itens.append({
                "nome": nome,
                "custo": str(row['Preco_Custo_Novo']).strip(),
                "venda": str(row['Preco_Venda_Novo']).strip()
            })
    return itens

def registrar_processado(nome):
    ARQUIVO_LOG_PROCESSADOS.parent.mkdir(parents=True, exist_ok=True)
    with open(ARQUIVO_LOG_PROCESSADOS, "a", encoding="utf-8") as f:
        f.write(nome + "\n")

def executar_rpa(lote=None, planilha=None):
    conectar_desktop_interativo()

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = PAUSA_ENTRE_COMANDOS

    itens = carregar_itens_pendentes(planilha)
    total_pendente = len(itens)

    if total_pendente == 0:
        print("[OK] Todos os produtos da lista já foram processados!")
        return

    tamanho_lote = int(lote) if lote else TAMANHO_LOTE_PADRAO
    itens_lote = itens[:tamanho_lote]

    print("="*65)
    print("ROBÔ DE DIGITAÇÃO AUTOMÁTICA EM SISTEMA DESKTOP")
    print(f"Total pendente na lista: {total_pendente} produtos")
    print(f"Lote a ser executado   : {len(itens_lote)} produtos")
    print(f"Tempo de filtro        : {TEMPO_FILTRO_SEGUNDOS}s")
    print("="*65)
    print("[ATENÇÃO] Você tem 5 SEGUNDOS para clicar e deixar a tela do ERP ATIVA.")
    print("Para abortar a qualquer momento: puxe o mouse para qualquer canto da tela.")
    print("="*65)

    for i in range(5, 0, -1):
        print(f"Iniciando em {i}...")
        time.sleep(1)

    for idx, item in enumerate(itens_lote, 1):
        print(f"[{idx}/{len(itens_lote)}] Inserindo: {item['nome']} (Custo: {item['custo']} | Venda: {item['venda']})")

        # 1. Abre a caixa de busca da grade (Ctrl + F)
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.2)

        # 2. Cola o nome exato do produto para filtrar
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        pyperclip.copy(item['nome'])
        pyautogui.hotkey('ctrl', 'v')

        # 3. Aguarda o tempo de filtro do sistema
        time.sleep(TEMPO_FILTRO_SEGUNDOS)

        # 4. Seleciona a linha filtrada
        pyautogui.press('down')
        time.sleep(0.2)

        # 5. Navega até o campo de Custo (2 Tabs: Ativo -> Custo)
        pyautogui.press('tab')
        time.sleep(0.1)
        pyautogui.press('tab')
        time.sleep(0.1)

        # 6. Digita Preço de Custo
        pyautogui.write(item['custo'])
        time.sleep(0.15)

        # 7. Tab para Custo Inicial e digita
        pyautogui.press('tab')
        time.sleep(0.1)
        pyautogui.write(item['custo'])
        time.sleep(0.15)

        # 8. Tab para Preço de Venda e digita
        pyautogui.press('tab')
        time.sleep(0.1)
        pyautogui.write(item['venda'])
        time.sleep(0.15)

        # 9. Confirma a linha
        pyautogui.press('enter')
        time.sleep(0.2)

        # 10. Retorna cursor para o início da grade (Shift+Tab)
        for _ in range(QTD_SHIFT_TABS_RETORNO):
            pyautogui.hotkey('shift', 'tab')
            time.sleep(0.08)
        time.sleep(0.3)

        # Registra no log de progresso
        registrar_processado(item['nome'])

    print("\n" + "="*65)
    print(f"[CONCLUÍDO] Lote de {len(itens_lote)} produtos finalizado!")
    print("O robô NÃO clicou em Gravar. Revise na tela e salve manualmente.")
    print("="*65)

if __name__ == "__main__":
    param_lote = sys.argv[1] if len(sys.argv) > 1 else None
    executar_rpa(param_lote)
