from pydantic_settings import BaseSettings


class Config(BaseSettings):
    class Config:
        env_file = ".env"

    URI: str
    DB_NAME: str


config = Config()
