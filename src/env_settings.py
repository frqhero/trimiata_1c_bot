from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    TELEGRAM_TOKEN: str
    STOCK_DATA_EQUIVALENCE: str = Field(description='Path to the folder with stock data equivalence')
    LOGIN_1C: str
    PASSWORD_1C: str
    MEDIA_SOURCES_PATH: str
    PHOTO_RENAMING_URL: str = Field(description='Send barcodes, validates they exist and get articles')
    CANCEL_ORDER_URL: str = Field(description='Cancel order by order_id')

settings = Settings()
