from dataclasses import MISSING, dataclass, fields
from sys import stderr
import json


@dataclass
class Config:
    base_url: str
    api_key: str
    model: str

    def __init__(self, config_file_path) -> None:
        try:
            with open(config_file_path, "r") as config_file:
                config_content = json.load(config_file)
        except FileNotFoundError:
            stderr.write(f"Expected config: {config_file_path}\n")
            raise
        for field in fields(self):
            val = config_content.get(field.name, field.default)
            if val is MISSING:
                raise ValueError(f"No value for {field.name}")
            setattr(self, field.name, val)


config = Config("config.json")