from pydantic import BaseModel

from Enum.Estado import Estado


class EnderecoLocalidadeResponseDTO(BaseModel):

    Cidade: str

    Estado: Estado

    Endereco: str | None = None

    Fonte: str = "OpenStreetMap/Nominatim"
