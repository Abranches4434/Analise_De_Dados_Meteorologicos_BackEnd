from datetime import date

from flask import Response, request
from flask_restful import Resource
from pydantic import ValidationError

from Exception.exception import (
    ElementoCadastrado,
    ElementoComDependenciasException,
    ElementoNaoEncontradoException,
    ServicoExternoIndisponivelException,
)
from Exception.validation import formatar_erro_validacao


class BaseResource(Resource):
    """Recurso REST base com serialização e tratamento de erros padronizados."""

    def _incluir_inativos(self) -> bool:
        valor = str(request.args.get("incluir_inativos", "")).lower()
        return valor in {"1", "true", "sim", "yes"}

    def _data(self, nome: str) -> date | None:
        valor = request.args.get(nome)

        if not valor:
            return None

        try:
            return date.fromisoformat(valor)
        except ValueError as erro:
            raise ValueError(
                f"A data '{nome}' é inválida. Use o formato AAAA-MM-DD."
            ) from erro

    def _inteiro(self, nome: str) -> int | None:
        valor = request.args.get(nome)

        if valor in (None, ""):
            return None

        try:
            return int(valor)
        except ValueError as erro:
            raise ValueError(
                f"O parâmetro '{nome}' deve ser um número inteiro."
            ) from erro

    def _lista_inteiros(self, nome: str) -> list[int]:
        valor = request.args.get(nome)

        if not valor:
            return []

        try:
            return [int(item.strip()) for item in valor.split(",") if item.strip()]
        except ValueError as erro:
            raise ValueError(
                f"O parâmetro '{nome}' deve conter números separados por vírgula."
            ) from erro

    def _executar(self, acao, status: int = 200):
        try:
            resultado = acao()

            if resultado is None:
                return "", 204

            if isinstance(resultado, list):
                return [
                    item.model_dump(mode="json") for item in resultado
                ], status

            if hasattr(resultado, "model_dump"):
                return resultado.model_dump(mode="json"), status

            return resultado, status
        except ValidationError as erro:
            return {"erro": formatar_erro_validacao(erro)}, 400
        except ValueError as erro:
            return {"erro": str(erro)}, 400
        except ElementoNaoEncontradoException as erro:
            return {"erro": str(erro)}, 404
        except ElementoCadastrado as erro:
            return {"erro": str(erro)}, 409
        except ElementoComDependenciasException as erro:
            return {"erro": str(erro)}, 409
        except ServicoExternoIndisponivelException as erro:
            return {"erro": str(erro)}, 503
        except Exception as erro:
            return {"erro": str(erro)}, 500

    def _executar_arquivo(self, acao):
        try:
            nome_arquivo, conteudo = acao()
            return Response(
                conteudo,
                mimetype="text/csv; charset=utf-8",
                headers={
                    "Content-Disposition": (
                        f"attachment; filename={nome_arquivo}"
                    )
                },
            )
        except ValidationError as erro:
            return {"erro": formatar_erro_validacao(erro)}, 400
        except ValueError as erro:
            return {"erro": str(erro)}, 400
        except ElementoNaoEncontradoException as erro:
            return {"erro": str(erro)}, 404
        except ServicoExternoIndisponivelException as erro:
            return {"erro": str(erro)}, 503
        except Exception as erro:
            return {"erro": str(erro)}, 500
