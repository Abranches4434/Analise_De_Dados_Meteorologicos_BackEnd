import unittest

from support import preparar_ambiente

preparar_ambiente()

from app import app


class TestErrosValidacao(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def _registro_valido(self) -> dict:
        return {
            "TempMax": 30,
            "TempMin": 10,
            "TempMedia": 20,
            "UmidadeRelativa": 50,
            "Precipitacao": 0,
            "VelocidadeVento": 5,
            "PressaoAtmosferica": 1000,
            "Data": "2025-01-01",
            "Hora": "12:00:00",
            "FKLocalidade": 1,
        }

    def _assert_mensagem_amigavel(self, resposta, trecho):
        self.assertEqual(resposta.status_code, 400)

        mensagem = resposta.get_json()["erro"]

        self.assertIn(trecho, mensagem)

        for proibido in (
            "validation error",
            "pydantic",
            "input_value",
            "For further information",
        ):
            self.assertNotIn(proibido, mensagem)

        return mensagem

    def test_registros_temperaturas_fora_de_ordem(self):
        dados = self._registro_valido()
        dados.update(TempMax=10, TempMin=30, TempMedia=20)

        resposta = self.client.post("/registros", json=dados)

        self._assert_mensagem_amigavel(
            resposta,
            "A temperatura mínima não pode ser maior que a temperatura máxima!",
        )

    def test_registros_temperatura_fora_da_faixa(self):
        dados = self._registro_valido()
        dados["TempMax"] = 60

        resposta = self.client.post("/registros", json=dados)

        self._assert_mensagem_amigavel(
            resposta,
            "O campo 'temperatura máxima' deve ser menor ou igual a 50.",
        )

    def test_registros_data_futura(self):
        dados = self._registro_valido()
        dados["Data"] = "2999-01-01"

        resposta = self.client.post("/registros", json=dados)

        self._assert_mensagem_amigavel(
            resposta,
            "A data do registro não pode ser futura!",
        )

    def test_thresholds_variavel_incompativel(self):
        resposta = self.client.post(
            "/thresholds",
            json={
                "FKLocalidade": 1,
                "Variavel": "UMIDADE",
                "TipoLimiar": "DIASSEMCHUVA",
                "EstacaoDoAno": "ANUAL",
                "Valor": 5,
            },
        )

        self._assert_mensagem_amigavel(
            resposta,
            "Umidade aceita apenas os tipos de limiar MAXIMO ou MINIMO!",
        )

    def test_localidades_com_multiplos_erros(self):
        resposta = self.client.post(
            "/localidades",
            json={
                "Nome": "Estação Teste",
                "Cidade": "Teste",
                "Estado": "ZZ",
                "Latitude": 200,
                "Longitude": 0,
            },
        )

        mensagem = self._assert_mensagem_amigavel(
            resposta,
            "O valor informado para 'estado' é inválido.",
        )

        self.assertIn("• O valor informado para 'estado' é inválido.", mensagem)
        self.assertIn(
            "• O campo 'latitude' deve ser menor ou igual a 90.",
            mensagem,
        )


if __name__ == "__main__":
    unittest.main()
