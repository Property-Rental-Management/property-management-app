import socket
from pydantic import BaseSettings, Field


class CloudFlareSettings(BaseSettings):
    EMAIL: str = Field(..., env="CLOUDFLARE_EMAIL")
    TOKEN: str = Field(..., env="CLOUDFLARE_TOKEN")
    X_CLIENT_SECRET_TOKEN: str = Field(..., env="CLIENT_SECRET")

    class Config:
        case_sensitive = True
        env_file = '.env.development'
        env_file_encoding = 'utf-8'


class MySQLSettings(BaseSettings):
    PRODUCTION_DB: str = Field(..., env="production_sql_db")
    DEVELOPMENT_DB: str = Field(..., env="dev_sql_db")

    class Config:
        env_file = '.env.development'
        env_file_encoding = 'utf-8'


class Logging(BaseSettings):
    filename: str = Field(default="rental.logs")

    class Config:
        env_file = '.env.development'
        env_file_encoding = 'utf-8'

class ResendSettings(BaseSettings):
    API_KEY: str = Field(..., env="RESEND_API_KEY")
    from_: str = Field(default="norespond@rental-manager.site")
    class Config:
        env_file = '.env.development'
        env_file_encoding = 'utf-8'


class EmailSettings(BaseSettings):
    RESEND: ResendSettings = ResendSettings()

    class Config:
        env_file = '.env.development'
        env_file_encoding = 'utf-8'


class Settings(BaseSettings):
    APP_NAME: str = Field(default='rental and property manager')
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    CLIENT_SECRET: str = Field(..., env="CLIENT_SECRET")
    MYSQL_SETTINGS: MySQLSettings = MySQLSettings()
    CLOUDFLARE_SETTINGS: CloudFlareSettings = CloudFlareSettings()
    EMAIL_SETTINGS: EmailSettings = EmailSettings()
    DEVELOPMENT_SERVER_NAME: str = Field(default="DESKTOP-T9V7F59")
    LOGGING: Logging = Logging()
    HOST_ADDRESSES: str = Field(..., env='HOST_ADDRESSES')

    class Config:
        env_file = '.env.development'
        env_file_encoding = 'utf-8'


def config_instance() -> Settings:
    """

    :return:
    """
    return Settings()


def is_development():
    return socket.gethostname() == config_instance().DEVELOPMENT_SERVER_NAME
