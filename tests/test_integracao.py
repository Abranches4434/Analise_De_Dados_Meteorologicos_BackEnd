import csv
import io
import unittest
from datetime import date, time
from urllib.parse import urlencode

from support import preparar_ambiente, resetar_banco

preparar_ambiente()

from app import app
from Entity import db
from Entity.Localidades import Localidades
from seed import popular_dados_demo


class BancoPostgreSQLTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        resetar_banco(app, db)
        app.config["TESTING"] = True
        cls.client = app.test_client()

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.session.remove()


class TestAnalisesComDadosDemo(BancoPostgreSQLTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        with app.app_context():
            cls.resumo = popular_dados_demo()

    def test_seed_cria_dados_de_demonstracao(self):
        self.assertTrue(self.resumo["criado"])
        self.assertEqual(self.resumo["localidades"], 3)
        self.assertEqual(self.resumo["registros"], 1095)
        self.assertEqual(self.resumo["thresholds"], 18)

    def test_estatisticas_por_localidade_e_periodo(self):
        resposta = self.client.get(
            "/analises/estatisticas",
            query_string={
                "localidade_id": 1,
                "data_inicio": "2025-01-01",
                "data_fim": "2025-12-31",
            },
        )

        self.assertEqual(resposta.status_code, 200)
        dados = resposta.get_json()

        self.assertEqual(dados["IDLocalidade"], 1)
        self.assertEqual(dados["QuantidadeRegistros"], 365)
        self.assertEqual(len(dados["Estatisticas"]), 7)
        self.assertTrue(
            all(
                estatistica["Quantidade"] == 365
                for estatistica in dados["Estatisticas"]
            )
        )

    def test_comparacao_entre_localidades(self):
        resposta = self.client.get(
            "/analises/comparacao",
            query_string={
                "localidade_ids": "1,2",
                "data_inicio": "2025-01-01",
                "data_fim": "2025-12-31",
            },
        )

        self.assertEqual(resposta.status_code, 200)
        dados = resposta.get_json()

        self.assertEqual(len(dados["Localidades"]), 2)
        self.assertTrue(
            all(
                localidade["QuantidadeRegistros"] == 365
                for localidade in dados["Localidades"]
            )
        )

    def test_eventos_extremos_incluem_seca_e_limiares(self):
        resposta = self.client.get(
            "/analises/eventos-extremos",
            query_string={
                "localidade_id": 1,
                "data_inicio": "2025-01-01",
                "data_fim": "2025-12-31",
            },
        )

        self.assertEqual(resposta.status_code, 200)
        dados = resposta.get_json()

        self.assertGreater(dados["QuantidadeEventos"], 0)
        self.assertEqual(
            dados["QuantidadeEventos"],
            len(dados["Eventos"]),
        )

        tipos = {evento["TipoLimiar"] for evento in dados["Eventos"]}
        self.assertIn("DIASSEMCHUVA", tipos)
        self.assertIn("MAXIMO", tipos)
        self.assertIn("MINIMO", tipos)

        secas = [
            evento
            for evento in dados["Eventos"]
            if evento["TipoLimiar"] == "DIASSEMCHUVA"
        ]
        self.assertTrue(
            any(
                evento["DataInicio"] <= "2025-08-01"
                and evento["DataFim"] >= "2025-08-20"
                and evento["Dias"] >= 20
                for evento in secas
            )
        )

    def test_sazonalidade_por_mes_e_estacao(self):
        por_mes = self.client.get(
            "/analises/sazonalidade",
            query_string={
                "localidade_id": 1,
                "data_inicio": "2025-01-01",
                "data_fim": "2025-12-31",
                "agrupamento": "mes",
            },
        ).get_json()

        self.assertEqual(por_mes["Agrupamento"], "mes")
        self.assertEqual(len(por_mes["Grupos"]), 12)
        self.assertEqual(
            sum(grupo["Quantidade"] for grupo in por_mes["Grupos"]),
            365,
        )

        por_estacao = self.client.get(
            "/analises/sazonalidade",
            query_string={
                "localidade_id": 1,
                "data_inicio": "2025-01-01",
                "data_fim": "2025-12-31",
                "agrupamento": "estacao",
            },
        ).get_json()

        self.assertEqual(por_estacao["Agrupamento"], "estacao")
        self.assertEqual(len(por_estacao["Grupos"]), 4)
        self.assertEqual(
            sum(grupo["Quantidade"] for grupo in por_estacao["Grupos"]),
            365,
        )

    def test_exportacoes_csv(self):
        casos = (
            (
                "registros",
                {"localidade_id": 1, "data_inicio": "2025-01-01", "data_fim": "2025-01-02"},
                2,
                "IDRegistrosClimaticos",
            ),
            (
                "estatisticas",
                {"localidade_id": 1, "data_inicio": "2025-01-01", "data_fim": "2025-12-31"},
                7,
                "IDLocalidade",
            ),
            (
                "comparacao",
                {"localidade_ids": "1,2", "data_inicio": "2025-01-01", "data_fim": "2025-12-31"},
                14,
                "IDLocalidade",
            ),
            (
                "eventos",
                {"localidade_id": 1, "data_inicio": "2025-01-01", "data_fim": "2025-12-31"},
                None,
                "IDThreshold",
            ),
            (
                "sazonalidade",
                {"localidade_id": 1, "data_inicio": "2025-01-01", "data_fim": "2025-12-31"},
                12,
                "IDLocalidade",
            ),
        )

        for tipo, parametros, quantidade, primeiro_campo in casos:
            with self.subTest(tipo=tipo):
                resposta = self.client.get(
                    f"/exportacoes/{tipo}?{urlencode(parametros)}"
                )

                self.assertEqual(resposta.status_code, 200)
                self.assertIn(
                    "text/csv",
                    resposta.headers["Content-Type"],
                )
                self.assertTrue(
                    resposta.data.startswith(b"\xef\xbb\xbf")
                )

                leitor = csv.DictReader(
                    io.StringIO(
                        resposta.data.decode("utf-8-sig")
                    ),
                    delimiter=";",
                )
                linhas = list(leitor)

                self.assertEqual(leitor.fieldnames[0], primeiro_campo)

                if tipo == "estatisticas":
                    self.assertIn("Variavel", leitor.fieldnames)
                if tipo == "sazonalidade":
                    self.assertIn("Grupo", leitor.fieldnames)
                if tipo == "eventos":
                    self.assertIn("Descricao", leitor.fieldnames)

                if quantidade is None:
                    self.assertGreater(len(linhas), 0)
                else:
                    self.assertEqual(len(linhas), quantidade)

    def test_parametros_invalidos_e_recurso_ausente(self):
        casos = (
            (
                "/analises/comparacao?localidade_ids=1"
                "&data_inicio=2025-01-01&data_fim=2025-12-31",
                400,
            ),
            ("/analises/eventos-extremos", 400),
            ("/analises/sazonalidade?agrupamento=dia", 400),
            ("/exportacoes/invalido", 400),
            (
                "/registros?data_inicio=2025-02-01&data_fim=2025-01-01",
                400,
            ),
            ("/registros?data_inicio=2025-13-01", 400),
            ("/localidades/999999", 404),
            ("/analises/estatisticas?localidade_id=999999", 404),
        )

        for url, status in casos:
            with self.subTest(url=url):
                self.assertEqual(
                    self.client.get(url).status_code,
                    status,
                )


class TestSemanticaEventosECRUD(BancoPostgreSQLTestCase):

    def setUp(self):
        resetar_banco(app, db)

        resposta = self.client.post(
            "/localidades",
            json={
                "Nome": "Estação Teste",
                "Cidade": "Teste",
                "Estado": "SP",
                "Latitude": -23.0,
                "Longitude": -46.0,
                "Ativo": True,
            },
        )

        self.assertEqual(resposta.status_code, 201)
        self.localidade_id = resposta.get_json()["IDLocalidade"]

    def criar_threshold(self, tipo: str, valor: float):
        resposta = self.client.post(
            "/thresholds",
            json={
                "FKLocalidade": self.localidade_id,
                "Variavel": "TEMPERATURA",
                "TipoLimiar": tipo,
                "EstacaoDoAno": "ANUAL",
                "Valor": valor,
                "Ativo": True,
            },
        )

        self.assertEqual(resposta.status_code, 201)
        return resposta.get_json()

    def criar_registro(
        self,
        dia: date,
        temp_min: float = 20.0,
        temp_max: float = 30.0,
        precipitacao: float = 0.0,
    ):
        resposta = self.client.post(
            "/registros",
            json={
                "TempMax": temp_max,
                "TempMin": temp_min,
                "TempMedia": (temp_max + temp_min) / 2,
                "UmidadeRelativa": 60.0,
                "Precipitacao": precipitacao,
                "VelocidadeVento": 10.0,
                "PressaoAtmosferica": 1013.0,
                "Data": dia.isoformat(),
                "Hora": time(12, 0, 0).isoformat(),
                "Ativo": True,
                "FKLocalidade": self.localidade_id,
            },
        )

        self.assertEqual(resposta.status_code, 201)
        return resposta.get_json()

    def eventos(self):
        return self.client.get(
            "/analises/eventos-extremos",
            query_string={"localidade_id": self.localidade_id},
        ).get_json()["Eventos"]

    def test_maximo_inclui_igualdade_e_inativacao_remove_das_analises(self):
        self.criar_threshold("MAXIMO", 30.0)
        registro = self.criar_registro(date(2025, 1, 1), temp_max=30.0)

        eventos = self.eventos()
        self.assertEqual(len(eventos), 1)
        self.assertEqual(eventos[0]["Valor"], 30.0)
        self.assertEqual(eventos[0]["Limiar"], 30.0)

        resposta = self.client.delete(
            f"/registros/{registro['IDRegistrosClimaticos']}"
        )
        self.assertEqual(resposta.status_code, 204)

        estatisticas = self.client.get(
            "/analises/estatisticas",
            query_string={"localidade_id": self.localidade_id},
        ).get_json()

        self.assertEqual(estatisticas["QuantidadeRegistros"], 0)
        self.assertEqual(estatisticas["Estatisticas"], [])
        self.assertEqual(self.eventos(), [])

        inativos = self.client.get(
            "/registros",
            query_string={"incluir_inativos": "true"},
        ).get_json()

        self.assertEqual(len(inativos), 1)
        self.assertFalse(inativos[0]["Ativo"])

    def test_minimo_inclui_igualdade(self):
        self.criar_threshold("MINIMO", 20.0)
        self.criar_registro(date(2025, 1, 1), temp_min=20.0)

        eventos = self.eventos()
        self.assertEqual(len(eventos), 1)
        self.assertEqual(eventos[0]["Valor"], 20.0)
        self.assertEqual(eventos[0]["Limiar"], 20.0)

    def test_diassemchuva_conta_dias_consecutivos(self):
        resposta = self.client.post(
            "/thresholds",
            json={
                "FKLocalidade": self.localidade_id,
                "Variavel": "PRECIPITACAO",
                "TipoLimiar": "DIASSEMCHUVA",
                "EstacaoDoAno": "ANUAL",
                "Valor": 3,
                "Ativo": True,
            },
        )
        self.assertEqual(resposta.status_code, 201)

        for dia in range(1, 4):
            self.criar_registro(
                date(2025, 1, dia),
                precipitacao=0.0,
            )

        self.criar_registro(
            date(2025, 1, 4),
            precipitacao=5.0,
        )

        eventos = self.eventos()
        self.assertEqual(len(eventos), 1)
        self.assertEqual(eventos[0]["TipoLimiar"], "DIASSEMCHUVA")
        self.assertEqual(eventos[0]["Dias"], 3)
        self.assertEqual(eventos[0]["DataInicio"], "2025-01-01")
        self.assertEqual(eventos[0]["DataFim"], "2025-01-03")

    def test_relacionamentos_orm_entre_entidades(self):
        registro = self.criar_registro(date(2025, 1, 1))
        threshold = self.criar_threshold("MAXIMO", 30.0)

        with app.app_context():
            localidade = db.session.get(
                Localidades,
                self.localidade_id,
            )

            self.assertEqual(len(localidade.registros), 1)
            self.assertEqual(len(localidade.thresholds), 1)
            self.assertEqual(
                localidade.registros[0].IDRegistrosClimaticos,
                registro["IDRegistrosClimaticos"],
            )
            self.assertEqual(
                localidade.registros[0].localidade.Nome,
                "Estação Teste",
            )
            self.assertEqual(
                localidade.thresholds[0].IDThreshold,
                threshold["IDThreshold"],
            )
            self.assertEqual(
                localidade.thresholds[0].localidade.IDLocalidade,
                self.localidade_id,
            )

    def test_crud_de_localidade_e_threshold(self):
        resposta = self.client.put(
            f"/localidades/{self.localidade_id}",
            json={
                "IDLocalidade": self.localidade_id,
                "Nome": "Estação Alterada",
                "Cidade": "Teste",
                "Estado": "SP",
                "Latitude": -23.0,
                "Longitude": -46.0,
                "Ativo": True,
            },
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            resposta.get_json()["Nome"],
            "Estação Alterada",
        )

        threshold = self.criar_threshold("MAXIMO", 30.0)

        resposta = self.client.put(
            f"/thresholds/{threshold['IDThreshold']}",
            json={
                "IDThreshold": threshold["IDThreshold"],
                "FKLocalidade": self.localidade_id,
                "Variavel": "TEMPERATURA",
                "TipoLimiar": "MAXIMO",
                "EstacaoDoAno": "ANUAL",
                "Valor": 35.0,
                "Ativo": True,
            },
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json()["Valor"], 35.0)

        resposta = self.client.delete(
            f"/thresholds/{threshold['IDThreshold']}"
        )
        self.assertEqual(resposta.status_code, 204)

        inativos = self.client.get(
            "/thresholds",
            query_string={"incluir_inativos": "true"},
        ).get_json()
        self.assertEqual(len(inativos), 1)
        self.assertFalse(inativos[0]["Ativo"])


class TestAnalisesIgnoramLocalidadesInativas(BancoPostgreSQLTestCase):

    def setUp(self):
        resetar_banco(app, db)

        self.ativa_id = self._criar_localidade(
            "Localidade Ativa",
            -23.0,
            -46.0,
        )
        self.inativa_id = self._criar_localidade(
            "Localidade Inativa",
            -22.0,
            -45.0,
        )

        self._criar_registro(self.ativa_id, temp_max=30.0)
        self._criar_registro(self.inativa_id, temp_max=45.0)

        resposta = self.client.delete(
            f"/localidades/{self.inativa_id}"
        )
        self.assertEqual(resposta.status_code, 204)

    def _criar_localidade(self, nome, latitude, longitude):
        resposta = self.client.post(
            "/localidades",
            json={
                "Nome": nome,
                "Cidade": "Teste",
                "Estado": "SP",
                "Latitude": latitude,
                "Longitude": longitude,
                "Ativo": True,
            },
        )

        self.assertEqual(resposta.status_code, 201)
        return resposta.get_json()["IDLocalidade"]

    def _criar_registro(self, localidade_id, temp_max):
        resposta = self.client.post(
            "/registros",
            json={
                "TempMax": temp_max,
                "TempMin": 20.0,
                "TempMedia": (temp_max + 20.0) / 2,
                "UmidadeRelativa": 60.0,
                "Precipitacao": 0.0,
                "VelocidadeVento": 10.0,
                "PressaoAtmosferica": 1013.0,
                "Data": "2025-01-01",
                "Hora": "12:00:00",
                "Ativo": True,
                "FKLocalidade": localidade_id,
            },
        )

        self.assertEqual(resposta.status_code, 201)

    def test_estatisticas_de_todas_as_localidades_ignoram_inativas(self):
        dados = self.client.get("/analises/estatisticas").get_json()

        self.assertEqual(dados["Nome"], "Todas as localidades")
        self.assertEqual(dados["QuantidadeRegistros"], 1)
        self.assertTrue(
            all(
                estatistica["Quantidade"] == 1
                for estatistica in dados["Estatisticas"]
            )
        )

    def test_sazonalidade_de_todas_as_localidades_ignora_inativas(self):
        dados = self.client.get(
            "/analises/sazonalidade",
            query_string={"agrupamento": "mes"},
        ).get_json()

        self.assertEqual(
            sum(grupo["Quantidade"] for grupo in dados["Grupos"]),
            1,
        )

    def test_exportacao_de_estatisticas_ignora_inativas(self):
        resposta = self.client.get("/exportacoes/estatisticas")

        self.assertEqual(resposta.status_code, 200)

        leitor = csv.DictReader(
            io.StringIO(resposta.data.decode("utf-8-sig")),
            delimiter=";",
        )
        linhas = list(leitor)

        self.assertEqual(len(linhas), 7)

        temp_max = next(
            linha
            for linha in linhas
            if linha["Variavel"] == "TempMax"
        )

        self.assertEqual(temp_max["Nome"], "Todas as localidades")
        self.assertEqual(float(temp_max["Maximo"]), 30.0)

    def test_analise_de_localidade_inativa_retorna_vazio(self):
        resposta = self.client.get(
            "/analises/estatisticas",
            query_string={"localidade_id": self.inativa_id},
        )

        self.assertEqual(resposta.status_code, 200)

        dados = resposta.get_json()

        self.assertEqual(dados["QuantidadeRegistros"], 0)
        self.assertEqual(dados["Estatisticas"], [])

    def test_listagem_de_registros_ignora_localidades_inativas(self):
        registros = self.client.get("/registros").get_json()

        self.assertEqual(len(registros), 1)
        self.assertEqual(registros[0]["FKLocalidade"], self.ativa_id)


if __name__ == "__main__":
    unittest.main()
