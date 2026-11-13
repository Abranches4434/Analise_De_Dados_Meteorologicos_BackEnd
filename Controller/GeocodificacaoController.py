from Service.GeocodificacaoService import GeocodificacaoService


class GeocodificacaoController:

    def __init__(self, servico: GeocodificacaoService | None = None):
        self._servico = servico or GeocodificacaoService()

    def buscar_coordenadas(self, cidade, estado):
        return self._servico.buscar_coordenadas(cidade, estado)

    def buscar_endereco(self, latitude, longitude):
        return self._servico.buscar_endereco(latitude, longitude)
