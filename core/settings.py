from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=".env",
        extra="ignore",
    )

    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    name: str = "industrial"
    echo: bool = False

    @property
    def dsn(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class ModbusSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MODBUS_",
        env_file=".env",
        extra="ignore",
    )

    host: str = "127.0.0.1"
    port: int = 502
    unit: int = 1
    timeout: float = 3.0
    temp_register: int = 1
    hum_register: int = 2
    scale: float = 10.0
    unit_id: int = 1


class OpcUaSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="OPCUA_",
        env_file=".env",
        extra="ignore",
    )

    url: str = "opc.tcp://localhost:4840/freeopcua/server/"
    username: str = ""
    password: str = ""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    modbus: ModbusSettings = Field(default_factory=ModbusSettings)
    opcua: OpcUaSettings = Field(default_factory=OpcUaSettings)
    debug: bool = False


settings = Settings()
