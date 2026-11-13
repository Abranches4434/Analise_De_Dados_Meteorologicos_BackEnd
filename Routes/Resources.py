from flask import request
from flask_restful import Resource

from Controller.AnaliseController import AnaliseController
from Controller.GeocodificacaoController import GeocodificacaoController
from Controller.LocalidadesController import LocalidadesController
from Controller.RegistrosClimaticosController import (
    RegistrosClimaticosController,
)
from Controller.ThresholdsController import ThresholdsController
from Routes.BaseResource import BaseResource


class LocalidadesResource(BaseResource):

    def __init__(self):
        self._controller = LocalidadesController()

    def get(self):
        return self._executar(
            lambda: self._controller.selecionar_todos(
                self._incluir_inativos()
            )
        )

    def post(self):
        return self._executar(
            lambda: self._controller.inserir(request.get_json(silent=True)),
            status=201,
        )


class LocalidadeResource(BaseResource):

    def __init__(self):
        self._controller = LocalidadesController()

    def get(self, id: int):
        return self._executar(
            lambda: self._controller.selecionar_por_id(id)
        )

    def put(self, id: int):
        return self._executar(
            lambda: self._controller.alterar(
                request.get_json(silent=True),
                id,
            )
        )

    def delete(self, id: int):
        return self._executar(
            lambda: self._controller.excluir(id),
            status=204,
        )


class CoordenadasLocalidadeResource(BaseResource):

    def __init__(self):
        self._controller = GeocodificacaoController()

    def get(self):
        return self._executar(
            lambda: self._controller.buscar_coordenadas(
                request.args.get("cidade"),
                request.args.get("estado"),
            )
        )


class EnderecoLocalidadeResource(BaseResource):

    def __init__(self):
        self._controller = GeocodificacaoController()

    def get(self):
        return self._executar(
            lambda: self._controller.buscar_endereco(
                request.args.get("latitude"),
                request.args.get("longitude"),
            )
        )


class RegistrosResource(BaseResource):

    def __init__(self):
        self._controller = RegistrosClimaticosController()

    def get(self):
        return self._executar(
            lambda: self._controller.selecionar_todos(
                incluir_inativos=self._incluir_inativos(),
                data_inicio=self._data("data_inicio"),
                data_fim=self._data("data_fim"),
                localidade_id=self._inteiro("localidade_id"),
            )
        )

    def post(self):
        return self._executar(
            lambda: self._controller.inserir(request.get_json(silent=True)),
            status=201,
        )


class RegistroResource(BaseResource):

    def __init__(self):
        self._controller = RegistrosClimaticosController()

    def get(self, id: int):
        return self._executar(
            lambda: self._controller.selecionar_por_id(id)
        )

    def put(self, id: int):
        return self._executar(
            lambda: self._controller.alterar(
                request.get_json(silent=True),
                id,
            )
        )

    def delete(self, id: int):
        return self._executar(
            lambda: self._controller.excluir(id),
            status=204,
        )


class ThresholdsResource(BaseResource):

    def __init__(self):
        self._controller = ThresholdsController()

    def get(self):
        return self._executar(
            lambda: self._controller.selecionar_todos(
                self._incluir_inativos()
            )
        )

    def post(self):
        return self._executar(
            lambda: self._controller.inserir(request.get_json(silent=True)),
            status=201,
        )


class ThresholdResource(BaseResource):

    def __init__(self):
        self._controller = ThresholdsController()

    def get(self, id: int):
        return self._executar(
            lambda: self._controller.selecionar_por_id(id)
        )

    def put(self, id: int):
        return self._executar(
            lambda: self._controller.alterar(
                request.get_json(silent=True),
                id,
            )
        )

    def delete(self, id: int):
        return self._executar(
            lambda: self._controller.excluir(id),
            status=204,
        )


class EstatisticasResource(BaseResource):

    def __init__(self):
        self._controller = AnaliseController()

    def get(self):
        return self._executar(
            lambda: self._controller.estatisticas(
                data_inicio=self._data("data_inicio"),
                data_fim=self._data("data_fim"),
                localidade_id=self._inteiro("localidade_id"),
            )
        )


class ComparacaoResource(BaseResource):

    def __init__(self):
        self._controller = AnaliseController()

    def get(self):
        return self._executar(
            lambda: self._controller.comparar(
                data_inicio=self._data("data_inicio"),
                data_fim=self._data("data_fim"),
                localidade_ids=self._lista_inteiros("localidade_ids"),
            )
        )


class EventosExtremosResource(BaseResource):

    def __init__(self):
        self._controller = AnaliseController()

    def get(self):
        return self._executar(
            lambda: self._controller.eventos_extremos(
                data_inicio=self._data("data_inicio"),
                data_fim=self._data("data_fim"),
                localidade_id=self._inteiro("localidade_id"),
            )
        )


class SazonalidadeResource(BaseResource):

    def __init__(self):
        self._controller = AnaliseController()

    def get(self):
        return self._executar(
            lambda: self._controller.sazonalidade(
                data_inicio=self._data("data_inicio"),
                data_fim=self._data("data_fim"),
                localidade_id=self._inteiro("localidade_id"),
                agrupamento=request.args.get("agrupamento", "mes"),
            )
        )


class ExportacaoResource(BaseResource):

    def __init__(self):
        self._controller = AnaliseController()

    def get(self, tipo: str):
        return self._executar_arquivo(
            lambda: self._controller.exportar(
                tipo=tipo,
                data_inicio=self._data("data_inicio"),
                data_fim=self._data("data_fim"),
                localidade_id=self._inteiro("localidade_id"),
                localidade_ids=self._lista_inteiros("localidade_ids"),
                agrupamento=request.args.get("agrupamento", "mes"),
            )
        )


class HealthResource(Resource):

    def get(self):
        return {"status": "ok"}, 200
