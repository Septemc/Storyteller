from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    全局配置。后续可以扩展更多字段，例如各类 API key。
    """
    # 注意：路径是相对项目根目录的 ./data/db.sqlite
    database_url: str = "sqlite:///./data/db.sqlite"

    # Pydantic v2 的配置方式
    model_config = SettingsConfigDict(env_prefix="NOVEL_")


settings = Settings()
