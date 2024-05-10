from pydantic import BaseModel, Field


class PhotoRenamingRow(BaseModel):
    barcode: str = Field(alias='ШК')
    name: str = Field(alias='Наименование')
    aim: str = Field(alias='Трим_Аим')
    metal: str = Field(alias='Металл')
    diagnostics: str = Field(alias='Диагностика')
    article: str = Field(alias='Артикул')


class PhotoRenamingResponse(BaseModel):
    response: list[PhotoRenamingRow]