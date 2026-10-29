"""
Módulo de Configuração Central
------------------------------
Gerencia os caminhos de arquivos e parâmetros de automação.
Permite customização via variáveis de ambiente sem expor caminhos privados.
"""

import os
from pathlib import Path

# Diretório base do projeto (relativo ao local deste script)
BASE_DIR = Path(__file__).resolve().parent

# Pasta para dados locais (não versionados pelo git)
DATA_DIR = Path(os.getenv("APP_DATA_DIR", BASE_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Caminhos dos arquivos de entrada e saída
PDF_ENTRADA = Path(os.getenv("PDF_ENTRADA", DATA_DIR / "catalogo_fornecedor.pdf"))
EXCEL_SISTEMA = Path(os.getenv("EXCEL_SISTEMA", DATA_DIR / "produtos_sistema.xlsx"))

# Arquivos gerados pelo pipeline
EXCEL_ESTOQUE_EXTRAIDO = DATA_DIR / "produtos_estoque_extraido.xlsx"
CSV_ESTOQUE_EXTRAIDO = DATA_DIR / "produtos_estoque_extraido.csv"
EXCEL_CRUZAMENTO_FINAL = DATA_DIR / "cruzamento_produtos_final.xlsx"
ARQUIVO_LOG_PROCESSADOS = DATA_DIR / "produtos_processados.log"

# Parâmetros da automação RPA
TEMPO_FILTRO_SEGUNDOS = float(os.getenv("TEMPO_FILTRO_SEGUNDOS", "2.0"))
QTD_SHIFT_TABS_RETORNO = int(os.getenv("QTD_SHIFT_TABS_RETORNO", "5"))
TAMANHO_LOTE_PADRAO = int(os.getenv("TAMANHO_LOTE_PADRAO", "20"))
PAUSA_ENTRE_COMANDOS = float(os.getenv("PAUSA_ENTRE_COMANDOS", "0.12"))
