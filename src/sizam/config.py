import dataclasses
from configparser import ConfigParser
from typing import Dict, Optional

from sqlalchemy import URL


@dataclasses.dataclass
class Wiki2035Config:
    base_url: str
    token: str
    platform_id: str


@dataclasses.dataclass
class DBConfig:
    dialect: str
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    dbname: Optional[str] = None
    extra: Optional[Dict[str, str]] = None

    @property
    def sqla_url(self) -> URL:
        return URL.create(
            drivername=self.dialect,
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            database=self.dbname,
            query=self.extra
        )


@dataclasses.dataclass
class Config:
    wiki2035: Wiki2035Config
    db: DBConfig


def load_config(path: str) -> Config:
    parser = ConfigParser()
    parser.read(path, encoding="utf-8")
    api_config = parser["wiki2035"]
    return Config(
        wiki2035=Wiki2035Config(
            base_url=api_config["base_url"],
            token=f"Token {api_config['token']}",
            platform_id=api_config["company_name"]
        ),
        db=DBConfig(**{
            key: value if value else None
            for key, value
            in parser["db"].items()
        })
    )
