from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    app_name: str = "Votecatcher Backend"
    version: str = ""
