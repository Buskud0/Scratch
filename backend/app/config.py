from dotenv import find_dotenv, load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(find_dotenv())


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    secret_key: str = Field(default="", validation_alias="SECRET_KEY")
    admin_code: str = Field(default="", validation_alias="ADMIN_CODE")
    db_user: str = Field(default="", validation_alias="SCRATCH_DB_USER")
    db_password: str = Field(default="", validation_alias="SCRATCH_DB_PASSWORD")
    db_name: str = Field(default="", validation_alias="SCRATCH_DB_NAME")
    db_host: str = Field(default="127.0.0.1", validation_alias="SCRATCH_DB_HOST")
    db_port: int = Field(default=3306, validation_alias="SCRATCH_DB_PORT")
    access_token_expire_minutes: int = Field(default=30, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    def validate_secrets(self) -> None:
        if not self.secret_key or not self.admin_code:
            raise RuntimeError("SECRET_KEY and ADMIN_CODE must be set in environment variables")


settings = Settings()