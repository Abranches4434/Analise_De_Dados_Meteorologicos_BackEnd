import json
import unittest
from unittest.mock import patch
from urllib.error import URLError

from support import preparar_ambiente

preparar_ambiente()

from app import app

from Config import GEOCODIFICACAO_USER_AGENT
from Service.GeocodificacaoService import GeocodificacaoService


class RespostaFalsa:

    def __init__(self, dados):
        self._conteudo = json.dumps(dados).encode("utf-8")

    def read(self):
        return self._conteudo

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class TestGeocodificacao(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        GeocodificacaoService._cache_coordenadas.clear()
        GeocodificacaoService._cache_enderecos.clear()
        GeocodificacaoService._ultima_requisicao = 0.0

    def test_busca_coordenadas_por_cidade_e_estado(self):
        resposta_api = [
            {
                "lat": "-23.5506507",
                "lon": "-46.6333824",
                "display_name": "São Paulo, Região Sudeste, Brasil",
            }
        ]

        with patch(
            "Service.GeocodificacaoService.urlopen",
            return_value=RespostaFalsa(resposta_api),
        ):
            resposta = self.client.get(
                "/localidades/coordenadas",
                query_string={
                    "cidade": "São Paulo",
                    "estado": "SP",
                },
            )

        self.assertEqual(resposta.status_code, 200)
        dados = resposta.get_json()
        self.assertAlmostEqual(dados["Latitude"], -23.550651, places=6)
        self.assertAlmostEqual(dados["Longitude"], -46.633382, places=6)
        self.assertEqual(dados["Fonte"], "OpenStreetMap/Nominatim")

    def test_busca_coordenadas_envia_parametros_e_user_agent(self):
        resposta_api = [
            {
                "lat": "-23.5506507",
                "lon": "-46.6333824",
                "display_name": "São Paulo, Região Sudeste, Brasil",
            }
        ]

        with patch(
            "Service.GeocodificacaoService.urlopen",
            return_value=RespostaFalsa(resposta_api),
        ) as urlopen_mock:
            self.client.get(
                "/localidades/coordenadas",
                query_string={
                    "cidade": "São Paulo",
                    "estado": "SP",
                },
            )

        requisicao = urlopen_mock.call_args.args[0]

        self.assertIn("city=S%C3%A3o+Paulo", requisicao.full_url)
        self.assertIn("state=SP", requisicao.full_url)
        self.assertIn("country=Brazil", requisicao.full_url)
        self.assertEqual(
            requisicao.get_header("User-agent"),
            GEOCODIFICACAO_USER_AGENT,
        )

    def test_busca_coordenadas_sem_resultado(self):
        with patch(
            "Service.GeocodificacaoService.urlopen",
            return_value=RespostaFalsa([]),
        ):
            resposta = self.client.get(
                "/localidades/coordenadas",
                query_string={
                    "cidade": "Cidade Inexistente",
                    "estado": "SP",
                },
            )

        self.assertEqual(resposta.status_code, 404)
        self.assertIn(
            "Não foi possível encontrar coordenadas",
            resposta.get_json()["erro"],
        )

    def test_busca_coordenadas_valida_cidade_e_estado(self):
        resposta = self.client.get(
            "/localidades/coordenadas",
            query_string={"cidade": "", "estado": "SP"},
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            resposta.get_json()["erro"],
            "Informe a cidade para buscar as coordenadas.",
        )

        resposta = self.client.get(
            "/localidades/coordenadas",
            query_string={"cidade": "São Paulo", "estado": "ZZ"},
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            resposta.get_json()["erro"],
            "O estado informado é inválido.",
        )

    def test_busca_coordenadas_com_servico_indisponivel(self):
        with patch(
            "Service.GeocodificacaoService.urlopen",
            side_effect=URLError("falhou"),
        ):
            resposta = self.client.get(
                "/localidades/coordenadas",
                query_string={
                    "cidade": "São Paulo",
                    "estado": "SP",
                },
            )

        self.assertEqual(resposta.status_code, 503)
        self.assertIn(
            "Não foi possível consultar o serviço de coordenadas",
            resposta.get_json()["erro"],
        )

    def test_busca_coordenadas_usa_cache(self):
        resposta_api = [
            {
                "lat": "-23.5506507",
                "lon": "-46.6333824",
                "display_name": "São Paulo, Região Sudeste, Brasil",
            }
        ]

        with patch(
            "Service.GeocodificacaoService.urlopen",
            return_value=RespostaFalsa(resposta_api),
        ) as urlopen_mock:
            for _ in range(2):
                resposta = self.client.get(
                    "/localidades/coordenadas",
                    query_string={
                        "cidade": "São Paulo",
                        "estado": "SP",
                    },
                )
                self.assertEqual(resposta.status_code, 200)

        self.assertEqual(urlopen_mock.call_count, 1)

    def test_busca_endereco_por_coordenadas(self):
        resposta_api = {
            "display_name": "São Paulo, Região Sudeste, Brasil",
            "address": {
                "city": "São Paulo",
                "state": "São Paulo",
                "ISO3166-2-lvl4": "BR-SP",
            },
        }

        with patch(
            "Service.GeocodificacaoService.urlopen",
            return_value=RespostaFalsa(resposta_api),
        ):
            resposta = self.client.get(
                "/localidades/coordenadas/reversa",
                query_string={
                    "latitude": "-23.5506507",
                    "longitude": "-46.6333824",
                },
            )

        self.assertEqual(resposta.status_code, 200)
        dados = resposta.get_json()
        self.assertEqual(dados["Cidade"], "São Paulo")
        self.assertEqual(dados["Estado"], "SP")
        self.assertEqual(dados["Fonte"], "OpenStreetMap/Nominatim")

    def test_busca_endereco_usa_nome_do_estado_sem_iso(self):
        resposta_api = {
            "display_name": "Recife, Região Nordeste, Brasil",
            "address": {
                "city": "Recife",
                "state": "Pernambuco",
            },
        }

        with patch(
            "Service.GeocodificacaoService.urlopen",
            return_value=RespostaFalsa(resposta_api),
        ):
            resposta = self.client.get(
                "/localidades/coordenadas/reversa",
                query_string={
                    "latitude": "-8.047562",
                    "longitude": "-34.876965",
                },
            )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json()["Estado"], "PE")

    def test_busca_endereco_valida_coordenadas(self):
        resposta = self.client.get(
            "/localidades/coordenadas/reversa",
            query_string={"latitude": "-91", "longitude": "0"},
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            resposta.get_json()["erro"],
            "A latitude deve estar entre -90 e 90.",
        )

    def test_busca_endereco_sem_resultado(self):
        with patch(
            "Service.GeocodificacaoService.urlopen",
            return_value=RespostaFalsa({"error": "Unable to geocode"}),
        ):
            resposta = self.client.get(
                "/localidades/coordenadas/reversa",
                query_string={
                    "latitude": "0",
                    "longitude": "0",
                },
            )

        self.assertEqual(resposta.status_code, 404)
        self.assertIn(
            "Não foi possível encontrar cidade e estado",
            resposta.get_json()["erro"],
        )


if __name__ == "__main__":
    unittest.main()
