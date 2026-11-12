import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from support import preparar_ambiente

preparar_ambiente()

from app import app


class TestDataHoraFutura(unittest.TestCase):

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

    def test_horario_futuro_no_mesmo_dia_utc(self):
        dados = self._registro_valido()
        dados.update(Data="2026-11-12", Hora="12:30:00")

        agora = datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc)

        with patch(
            "DTOs.RegistrosClimaticosRequestDTO.datetime"
        ) as datetime_mock:
            datetime_mock.now.return_value = agora
            datetime_mock.combine.side_effect = datetime.combine

            resposta = self.client.post("/registros", json=dados)

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            resposta.get_json()["erro"],
            "O horário do registro não pode ser futuro!",
        )

    def test_data_futura_continua_rejeitada(self):
        dados = self._registro_valido()
        dados["Data"] = "2999-01-01"

        resposta = self.client.post("/registros", json=dados)

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(
            resposta.get_json()["erro"],
            "A data do registro não pode ser futura!",
        )


if __name__ == "__main__":
    unittest.main()
