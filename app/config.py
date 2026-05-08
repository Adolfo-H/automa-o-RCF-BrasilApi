import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

CNAES = [
    #"6920602",  # consultoria/auditoria tributaria
    "4622200",  # Comércio atacadista de soja
    "4632001",  # Comércio atacadista de cereais e leguminosas beneficiados
    "115600",  # Cultivo de Soja
    "111302",  # Cultivo de Milho
    "1071600"  # Fabricação de açúcar VHP (Very High Polarization)
]

UFS = ["PR", "SP", "MT", "GO", "RS", "MG", "DF", "BA", "PE", "PA", "AM", "RO", "AP", "MS", "TO"]

PORTES = [5]  
CAPITAL_SOCIAL_MINIMO = 1_000_000.0
CAPITAL_SOCIAL_ACEITAR_ZERO = True
NATUREZAS_JURIDICAS = ["2062", "2046", "2054", "2143"]

MAX_WORKERS = int(os.getenv("MAX_WORKERS", "1"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "25"))
REQUEST_INTERVAL_SECONDS = float(os.getenv("REQUEST_INTERVAL_SECONDS", "2.0"))
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5"))
BACKOFF_BASE_SECONDS = float(os.getenv("BACKOFF_BASE_SECONDS", "3.0"))


