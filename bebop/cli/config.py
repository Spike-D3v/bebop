import re
from pathlib import Path

import typer
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from bebop.models import Board, PostGroup

APP_NAME = "bebop"
DEFAULT_BOARD_NAME = APP_NAME
DATETIME_FORMAT = "%Y-%m-%d %H:%M"
DEFAULT_BOARD = Board(
    title=APP_NAME.title(),
    posts=[
        PostGroup(title="To Do", name="todo"),
        PostGroup(title="In Progress", name="in_progress"),
        PostGroup(title="Done", name="done"),
    ],
)


def to_dot(v: str) -> str:
    return re.sub(r"_", ".", v)


class BebopTheme(BaseModel):
    """Representa el tema de la aplicación"""

    model_config = ConfigDict(alias_generator=to_dot)

    token: str = Field(default="red")
    ref: str = Field(default="dim red")
    group: str = Field(default="bold green")
    group_box: str = Field(default="green")
    post: str = Field(default="blue")
    post_box: str = Field(default="blue")
    board: str = Field(default="italic magenta")
    board_box: str = Field(default="magenta")
    description: str = Field(default="dim")
    help: str = Field(default="bright_yellow")
    todos: str = Field(default="purple")
    todos_box: str = Field(default="purple")
    comments: str = Field(default="yellow")
    comments_box: str = Field(default="yellow")
    date: str = Field(default="dark_cyan")
    tag: str = Field(default="bright_yellow on navy_blue")
    element: str = Field(default="bright_cyan")
    element_box: str = Field(default="bright_cyan")
    error: str = Field(default="bright_red")


class BebopConfig(BaseModel):
    """Representa la configuración del CLI"""

    model_config = ConfigDict(alias_generator=to_camel)

    default_board: str = Field(default=DEFAULT_BOARD_NAME)
    datetime_format: str = Field(default=DATETIME_FORMAT)
    theme: BebopTheme = Field(default_factory=lambda: BebopTheme())

    @classmethod
    def load_config(cls) -> "BebopConfig":
        config_path = cls.get_config_path()

        if not config_path.is_file():
            config = cls()
            dump = config.model_dump_json(indent=2, by_alias=True)
            config_path.write_text(dump)
            return config

        with config_path.open("r") as cfg:
            return cls.model_validate_json(cfg.read())

    @classmethod
    def get_config_path(cls) -> Path:
        return cls.get_root_path() / "config.json"

    @staticmethod
    def get_root_path() -> Path:
        return Path(typer.get_app_dir(APP_NAME))
