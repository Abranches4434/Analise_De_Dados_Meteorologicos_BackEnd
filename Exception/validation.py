from pydantic import ValidationError


ROTULOS_CAMPOS = {
    "IDRegistrosClimaticos": "id do registro",
    "IDThreshold": "id do threshold",
    "IDLocalidade": "id da localidade",
    "FKLocalidade": "localidade",
    "TempMax": "temperatura máxima",
    "TempMin": "temperatura mínima",
    "TempMedia": "temperatura média",
    "UmidadeRelativa": "umidade relativa",
    "Precipitacao": "precipitação",
    "VelocidadeVento": "velocidade do vento",
    "PressaoAtmosferica": "pressão atmosférica",
    "Data": "data",
    "Hora": "hora",
    "Ativo": "ativo",
    "Nome": "nome",
    "Cidade": "cidade",
    "Estado": "estado",
    "Latitude": "latitude",
    "Longitude": "longitude",
    "Variavel": "variável",
    "TipoLimiar": "tipo de limiar",
    "EstacaoDoAno": "estação do ano",
    "Valor": "valor",
}


def _rotulo(campo: str | None) -> str:
    if not campo:
        return "dados"

    return ROTULOS_CAMPOS.get(campo, campo)


def _valor_limite(valor):
    if isinstance(valor, float) and valor.is_integer():
        return int(valor)

    return valor


def _formatar_erro(erro: dict) -> str:
    tipo = erro.get("type")
    contexto = erro.get("ctx") or {}
    mensagem = erro.get("msg", "")
    local = erro.get("loc") or ()
    campo = local[-1] if local else None
    rotulo = _rotulo(campo)

    if tipo == "value_error":
        return mensagem.removeprefix("Value error, ").strip()

    if tipo == "assertion_error":
        return mensagem.removeprefix("Assertion failed, ").strip()

    if tipo == "missing":
        return f"O campo '{rotulo}' é obrigatório."

    if tipo == "greater_than_equal":
        return (
            f"O campo '{rotulo}' deve ser maior ou igual a "
            f"{_valor_limite(contexto.get('ge'))}."
        )

    if tipo == "less_than_equal":
        return (
            f"O campo '{rotulo}' deve ser menor ou igual a "
            f"{_valor_limite(contexto.get('le'))}."
        )

    if tipo == "greater_than":
        limite = _valor_limite(contexto.get("gt"))
        return f"O campo '{rotulo}' deve ser maior que {limite}."

    if tipo == "less_than":
        limite = _valor_limite(contexto.get("lt"))
        return f"O campo '{rotulo}' deve ser menor que {limite}."

    if tipo == "string_too_short":
        return (
            f"O campo '{rotulo}' deve ter pelo menos "
            f"{contexto.get('min_length')} caractere(s)."
        )

    if tipo == "string_too_long":
        return (
            f"O campo '{rotulo}' deve ter no máximo "
            f"{contexto.get('max_length')} caractere(s)."
        )

    if tipo in {"enum", "literal_error"}:
        return f"O valor informado para '{rotulo}' é inválido."

    if not campo:
        return "Os dados informados são inválidos."

    return f"O valor informado para '{rotulo}' é inválido."


def formatar_erro_validacao(erro: ValidationError) -> str:
    mensagens = []
    vistos = set()

    for detalhe in erro.errors():
        mensagem = _formatar_erro(detalhe)

        if not mensagem or mensagem in vistos:
            continue

        vistos.add(mensagem)
        mensagens.append(mensagem)

    if not mensagens:
        return "Os dados informados são inválidos."

    if len(mensagens) == 1:
        return mensagens[0]

    return "\n".join(f"• {mensagem}" for mensagem in mensagens)
