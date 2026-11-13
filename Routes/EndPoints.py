from flask_restful import Api

from Routes.Resources import (
    ComparacaoResource,
    CoordenadasLocalidadeResource,
    EnderecoLocalidadeResource,
    EstatisticasResource,
    EventosExtremosResource,
    ExportacaoResource,
    HealthResource,
    LocalidadeResource,
    LocalidadesResource,
    RegistroResource,
    RegistrosResource,
    SazonalidadeResource,
    ThresholdResource,
    ThresholdsResource,
)


def registrar_recursos(app):
    api = Api(app)

    api.add_resource(HealthResource, "/health")

    api.add_resource(LocalidadesResource, "/localidades")
    api.add_resource(
        CoordenadasLocalidadeResource,
        "/localidades/coordenadas",
    )
    api.add_resource(
        EnderecoLocalidadeResource,
        "/localidades/coordenadas/reversa",
    )
    api.add_resource(LocalidadeResource, "/localidades/<int:id>")

    api.add_resource(RegistrosResource, "/registros")
    api.add_resource(RegistroResource, "/registros/<int:id>")

    api.add_resource(ThresholdsResource, "/thresholds")
    api.add_resource(ThresholdResource, "/thresholds/<int:id>")

    api.add_resource(
        EstatisticasResource,
        "/analises/estatisticas",
    )
    api.add_resource(
        ComparacaoResource,
        "/analises/comparacao",
    )
    api.add_resource(
        EventosExtremosResource,
        "/analises/eventos-extremos",
    )
    api.add_resource(
        SazonalidadeResource,
        "/analises/sazonalidade",
    )
    api.add_resource(
        ExportacaoResource,
        "/exportacoes/<string:tipo>",
    )

    return api
