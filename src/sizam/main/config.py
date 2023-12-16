import dataclasses
from configparser import ConfigParser


@dataclasses.dataclass
class Config:
    base_url: str
    token: str
    platform_id: str


def load_config(path: str) -> Config:
    parser = ConfigParser()
    parser.read(path, encoding="utf-8")
    api_config = parser["wiki2035"]
    return Config(
        base_url=api_config["base_url"],
        token=f"Token {api_config['token']}",
        platform_id=api_config["company_name"],
    )
