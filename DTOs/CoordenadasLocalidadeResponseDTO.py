from pydantic import BaseModel


class CoordenadasLocalidadeResponseDTO(BaseModel):

    Latitude: float

    Longitude: float

    Endereco: str | None = None

    Fonte: str = "OpenStreetMap/Nominatim"
