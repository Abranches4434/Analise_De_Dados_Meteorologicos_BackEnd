from datetime import date, time

from Entity import db
from Entity.Localidades import Localidades
from Entity.RegistrosClimaticos import RegistrosClimaticos
from Repository.BaseRepository import BaseRepository


class RegistrosClimaticosRepository(BaseRepository):

    def __init__(self):
        super().__init__(RegistrosClimaticos)

    def selecionar_por_filtros(
        self,
        data_inicio: date | None = None,
        data_fim: date | None = None,
        fk_localidade: int | None = None,
        incluir_inativos: bool = False,
    ) -> list[RegistrosClimaticos]:
        consulta = db.select(RegistrosClimaticos)

        if not incluir_inativos:
            consulta = consulta.where(
                RegistrosClimaticos.Ativo.is_(True),
                RegistrosClimaticos.localidade.has(
                    Localidades.Ativo.is_(True)
                ),
            )

        if data_inicio is not None:
            consulta = consulta.where(
                RegistrosClimaticos.Data >= data_inicio
            )

        if data_fim is not None:
            consulta = consulta.where(RegistrosClimaticos.Data <= data_fim)

        if fk_localidade is not None:
            consulta = consulta.where(
                RegistrosClimaticos.FKLocalidade == fk_localidade
            )

        consulta = consulta.order_by(
            RegistrosClimaticos.Data,
            RegistrosClimaticos.Hora,
        )

        return db.session.execute(consulta).scalars().all()

    def selecionar_por_data_hora_localidade(
        self,
        data: date,
        hora: time,
        fk_localidade: int,
    ) -> RegistrosClimaticos | None:
        return db.session.execute(
            db.select(RegistrosClimaticos).where(
                RegistrosClimaticos.Data == data,
                RegistrosClimaticos.Hora == hora,
                RegistrosClimaticos.FKLocalidade == fk_localidade,
            )
        ).scalars().first()

    def alterar(self, registro: RegistrosClimaticos) -> RegistrosClimaticos | None:
        registro_atual = self.buscar_por_id(
            registro.IDRegistrosClimaticos
        )

        if registro_atual is not None:
            registro_atual.Ativo = registro.Ativo
            registro_atual.Data = registro.Data
            registro_atual.FKLocalidade = registro.FKLocalidade
            registro_atual.Hora = registro.Hora
            registro_atual.Precipitacao = registro.Precipitacao
            registro_atual.PressaoAtmosferica = registro.PressaoAtmosferica
            registro_atual.TempMax = registro.TempMax
            registro_atual.TempMin = registro.TempMin
            registro_atual.TempMedia = registro.TempMedia
            registro_atual.UmidadeRelativa = registro.UmidadeRelativa
            registro_atual.VelocidadeVento = registro.VelocidadeVento
            db.session.commit()

        return registro_atual
