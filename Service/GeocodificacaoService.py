import json
import threading
import time
import unicodedata
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from Config import (
    GEOCODIFICACAO_INTERVALO,
    GEOCODIFICACAO_REVERSA_URL,
    GEOCODIFICACAO_TIMEOUT,
    GEOCODIFICACAO_URL,
    GEOCODIFICACAO_USER_AGENT,
)
from DTOs.CoordenadasLocalidadeResponseDTO import (
    CoordenadasLocalidadeResponseDTO,
)
from DTOs.EnderecoLocalidadeResponseDTO import (
    EnderecoLocalidadeResponseDTO,
)
from Enum.Estado import Estado
from Exception.exception import (
    ElementoNaoEncontradoException,
    ServicoExternoIndisponivelException,
)


FONTE = "OpenStreetMap/Nominatim"


def _normalizar(valor: str) -> str:
    texto = unicodedata.normalize("NFKD", str(valor))
    sem_acentos = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )
    return " ".join(sem_acentos.casefold().split())


_NOMES_ESTADOS = {
    _normalizar(nome): uf
    for nome, uf in {
        "Acre": "AC",
        "Alagoas": "AL",
        "Amapá": "AP",
        "Amazonas": "AM",
        "Bahia": "BA",
        "Ceará": "CE",
        "Distrito Federal": "DF",
        "Espírito Santo": "ES",
        "Goiás": "GO",
        "Maranhão": "MA",
        "Mato Grosso": "MT",
        "Mato Grosso do Sul": "MS",
        "Minas Gerais": "MG",
        "Pará": "PA",
        "Paraíba": "PB",
        "Paraná": "PR",
        "Pernambuco": "PE",
        "Piauí": "PI",
        "Rio de Janeiro": "RJ",
        "Rio Grande do Norte": "RN",
        "Rio Grande do Sul": "RS",
        "Rondônia": "RO",
        "Roraima": "RR",
        "Santa Catarina": "SC",
        "São Paulo": "SP",
        "Sergipe": "SE",
        "Tocantins": "TO",
    }.items()
}


class GeocodificacaoService:

    _cache_coordenadas = {}
    _cache_enderecos = {}
    _lock = threading.Lock()
    _ultima_requisicao = 0.0

    def buscar_coordenadas(
        self,
        cidade,
        estado,
    ) -> CoordenadasLocalidadeResponseDTO:
        cidade = self._validar_cidade(cidade)
        estado = self._validar_estado(estado)
        chave = (cidade.casefold(), estado.value)

        cache = self._cache_coordenadas.get(chave)

        if cache is not None:
            return cache

        dados = self._requisicao_json(
            GEOCODIFICACAO_URL,
            {
                "city": cidade,
                "state": estado.value,
                "country": "Brazil",
                "format": "jsonv2",
                "limit": 1,
                "addressdetails": 1,
            },
        )

        if not isinstance(dados, list):
            raise ServicoExternoIndisponivelException(
                "O serviço de coordenadas retornou uma resposta inválida."
            )

        if not dados:
            raise ElementoNaoEncontradoException(
                f"Não foi possível encontrar coordenadas para "
                f"{cidade}/{estado.value}."
            )

        resultado = dados[0]

        try:
            latitude = round(float(resultado["lat"]), 6)
            longitude = round(float(resultado["lon"]), 6)
        except (KeyError, TypeError, ValueError) as erro:
            raise ServicoExternoIndisponivelException(
                "O serviço de coordenadas retornou uma resposta inválida."
            ) from erro

        dto = CoordenadasLocalidadeResponseDTO(
            Latitude=latitude,
            Longitude=longitude,
            Endereco=resultado.get("display_name"),
            Fonte=FONTE,
        )
        self._cache_coordenadas[chave] = dto

        return dto

    def buscar_endereco(
        self,
        latitude,
        longitude,
    ) -> EnderecoLocalidadeResponseDTO:
        latitude = self._validar_coordenada(
            latitude,
            "latitude",
            -90,
            90,
        )
        longitude = self._validar_coordenada(
            longitude,
            "longitude",
            -180,
            180,
        )
        chave = (round(latitude, 6), round(longitude, 6))

        cache = self._cache_enderecos.get(chave)

        if cache is not None:
            return cache

        dados = self._requisicao_json(
            GEOCODIFICACAO_REVERSA_URL,
            {
                "lat": latitude,
                "lon": longitude,
                "format": "jsonv2",
                "addressdetails": 1,
            },
        )

        if not isinstance(dados, dict):
            raise ServicoExternoIndisponivelException(
                "O serviço de coordenadas retornou uma resposta inválida."
            )

        if not dados or dados.get("error"):
            raise ElementoNaoEncontradoException(
                "Não foi possível encontrar cidade e estado para as "
                "coordenadas informadas."
            )

        endereco = dados.get("address")

        if not isinstance(endereco, dict):
            raise ElementoNaoEncontradoException(
                "Não foi possível encontrar cidade e estado para as "
                "coordenadas informadas."
            )

        cidade = self._extrair_cidade(endereco)
        estado = self._extrair_estado(endereco)

        if not cidade or estado is None:
            raise ElementoNaoEncontradoException(
                "Não foi possível encontrar cidade e estado para as "
                "coordenadas informadas."
            )

        dto = EnderecoLocalidadeResponseDTO(
            Cidade=cidade,
            Estado=estado,
            Endereco=dados.get("display_name"),
            Fonte=FONTE,
        )
        self._cache_enderecos[chave] = dto

        return dto

    @classmethod
    def _requisicao_json(cls, url: str, parametros: dict):
        cls._aguardar_intervalo()
        url_completa = f"{url}?{urlencode(parametros)}"
        requisicao = Request(
            url_completa,
            headers={
                "User-Agent": GEOCODIFICACAO_USER_AGENT,
                "Accept": "application/json",
                "Accept-Language": "pt-BR",
            },
        )

        try:
            with urlopen(
                requisicao,
                timeout=GEOCODIFICACAO_TIMEOUT,
            ) as resposta:
                conteudo = resposta.read().decode("utf-8")
        except (URLError, TimeoutError, OSError) as erro:
            raise ServicoExternoIndisponivelException(
                "Não foi possível consultar o serviço de coordenadas. "
                "Tente novamente mais tarde."
            ) from erro

        try:
            return json.loads(conteudo)
        except json.JSONDecodeError as erro:
            raise ServicoExternoIndisponivelException(
                "O serviço de coordenadas retornou uma resposta inválida."
            ) from erro

    @classmethod
    def _aguardar_intervalo(cls):
        with cls._lock:
            agora = time.monotonic()
            espera = GEOCODIFICACAO_INTERVALO - (
                agora - cls._ultima_requisicao
            )

            if espera > 0:
                time.sleep(espera)

            cls._ultima_requisicao = time.monotonic()

    @staticmethod
    def _validar_cidade(cidade) -> str:
        if not isinstance(cidade, str) or not cidade.strip():
            raise ValueError(
                "Informe a cidade para buscar as coordenadas."
            )

        return " ".join(cidade.split())

    @staticmethod
    def _validar_estado(estado) -> Estado:
        if not isinstance(estado, str) or not estado.strip():
            raise ValueError("Informe o estado (UF).")

        try:
            return Estado(estado.strip().upper())
        except ValueError as erro:
            raise ValueError("O estado informado é inválido.") from erro

    @staticmethod
    def _validar_coordenada(
        valor,
        nome: str,
        minimo: float,
        maximo: float,
    ) -> float:
        if valor is None or not str(valor).strip():
            raise ValueError(f"Informe a {nome}.")

        try:
            numero = float(str(valor).replace(",", "."))
        except ValueError as erro:
            raise ValueError(f"Informe uma {nome} válida.") from erro

        if not minimo <= numero <= maximo:
            raise ValueError(
                f"A {nome} deve estar entre {minimo} e {maximo}."
            )

        return numero

    @staticmethod
    def _extrair_cidade(endereco: dict) -> str | None:
        for chave in (
            "city",
            "town",
            "municipality",
            "village",
            "hamlet",
        ):
            valor = endereco.get(chave)

            if valor:
                return valor

        return None

    @classmethod
    def _extrair_estado(cls, endereco: dict) -> Estado | None:
        iso = endereco.get("ISO3166-2-lvl4")

        if isinstance(iso, str) and "-" in iso:
            uf = iso.rsplit("-", 1)[-1].strip().upper()

            try:
                return Estado(uf)
            except ValueError:
                pass

        nome = endereco.get("state")

        if not nome:
            return None

        uf = _NOMES_ESTADOS.get(_normalizar(nome))

        if uf is None:
            try:
                return Estado(str(nome).strip().upper())
            except ValueError:
                return None

        return Estado(uf)
