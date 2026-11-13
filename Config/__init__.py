import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent.parent / ".env")


GEOCODIFICACAO_URL = os.getenv(
    "GEOCODIFICACAO_URL",
    "https://nominatim.openstreetmap.org/search",
).rstrip("/")

GEOCODIFICACAO_REVERSA_URL = os.getenv(
    "GEOCODIFICACAO_REVERSA_URL",
    "https://nominatim.openstreetmap.org/reverse",
).rstrip("/")

GEOCODIFICACAO_TIMEOUT = float(
    os.getenv("GEOCODIFICACAO_TIMEOUT", "10")
)

GEOCODIFICACAO_INTERVALO = float(
    os.getenv("GEOCODIFICACAO_INTERVALO", "1.1")
)

GEOCODIFICACAO_USER_AGENT = os.getenv(
    "GEOCODIFICACAO_USER_AGENT",
    "AnaliseDeDadosMeteorologicos/1.0",
)
