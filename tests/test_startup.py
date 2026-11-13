import unittest

from support import preparar_ambiente

preparar_ambiente()

from app import app


class TestInicializacaoAPI(unittest.TestCase):

    def test_app_importa(self):
        self.assertIsNotNone(app)

    def test_rotas_registradas(self):
        rotas = {}

        for regra in app.url_map.iter_rules():
            if regra.rule == "/static/<path:filename>":
                continue

            rotas.setdefault(regra.rule, set()).update(
                regra.methods - {"HEAD", "OPTIONS"}
            )

        self.assertEqual(
            set(rotas.keys()),
            {
                "/health",
                "/localidades",
                "/localidades/coordenadas",
                "/localidades/coordenadas/reversa",
                "/localidades/<int:id>",
                "/registros",
                "/registros/<int:id>",
                "/thresholds",
                "/thresholds/<int:id>",
                "/analises/estatisticas",
                "/analises/comparacao",
                "/analises/eventos-extremos",
                "/analises/sazonalidade",
                "/exportacoes/<string:tipo>",
            },
        )

        self.assertEqual(rotas["/health"], {"GET"})
        self.assertEqual(rotas["/localidades"], {"GET", "POST"})
        self.assertEqual(rotas["/localidades/coordenadas"], {"GET"})
        self.assertEqual(
            rotas["/localidades/coordenadas/reversa"],
            {"GET"},
        )
        self.assertEqual(rotas["/localidades/<int:id>"], {"GET", "PUT", "DELETE"})
        self.assertEqual(rotas["/registros"], {"GET", "POST"})
        self.assertEqual(rotas["/registros/<int:id>"], {"GET", "PUT", "DELETE"})
        self.assertEqual(rotas["/thresholds"], {"GET", "POST"})
        self.assertEqual(rotas["/thresholds/<int:id>"], {"GET", "PUT", "DELETE"})
        self.assertEqual(rotas["/analises/estatisticas"], {"GET"})
        self.assertEqual(rotas["/analises/comparacao"], {"GET"})
        self.assertEqual(rotas["/analises/eventos-extremos"], {"GET"})
        self.assertEqual(rotas["/analises/sazonalidade"], {"GET"})
        self.assertEqual(rotas["/exportacoes/<string:tipo>"], {"GET"})

    def test_comandos_de_banco_registrados(self):
        self.assertIn("init-db", app.cli.commands)
        self.assertIn("seed-demo", app.cli.commands)

    def test_health(self):
        resposta = app.test_client().get("/health")

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json(), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
