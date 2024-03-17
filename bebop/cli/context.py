from pathlib import Path
from typing import Optional, Tuple

import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.theme import Theme

from bebop.cli.config import BebopConfig, DEFAULT_BOARD
from bebop.models import Board, PostGroup, Post
from bebop.token import IndexToken, RefToken
from . import render

ElementTree = Tuple[PostGroup, Optional[Post]]


class BebopContext:

    def __init__(
        self,
        config: BebopConfig,
        board_name: Optional[str] = None,
        dry_run: bool = False,
        debug: bool = False,
        author: Optional[str] = None,
    ):
        """Obtener el contexto de ejecución del CLI"""
        self.config = config
        self.theme = Theme(config.theme.model_dump(mode="json", by_alias=True))
        self.console = Console(theme=self.theme)
        self.board_name = board_name or config.default_board
        self.board = self.load_board()
        self.dry_run = dry_run
        self.debug = debug
        self.author = author

    @property
    def board_path(self) -> Path:
        return (self.config.get_root_path() / self.board_name).with_suffix(".json")

    def load_board(self) -> Board:
        if not self.board_path.is_file():
            board = DEFAULT_BOARD.copy()
            board.title = self.board_name.title()
            dump = board.model_dump_json(indent=2, by_alias=True)
            self.board_path.write_text(dump)
            return board

        with self.board_path.open("r") as f:
            return Board.model_validate_json(f.read())

    def save_board(self) -> None:
        if self.dry_run:
            return

        dump = self.board.model_dump_json(indent=2, by_alias=True)
        temp = self.board_path.with_suffix(".json.tmp")
        with temp.open("w") as f:
            f.write(dump)
        temp.rename(self.board_path)

    def get_tree_by_index(self, token: IndexToken) -> ElementTree:
        """
        Obtener el árbol de elementos por índice

        :raises typer.Abort: Si el índice no corresponde a ningún elemento
        """
        try:
            group = self.board.posts[token.main_index]
            post = None
            if token.sub_index is not None:
                post = group.posts[token.sub_index]
            return group, post

        except IndexError:
            message = render.ErrorPanel(f"The Token '{token}' does not exists")
            self.console.print(message)
            raise typer.Abort()

    def get_tree_by_ref(self, token: RefToken) -> ElementTree:
        """
        Obtener el árbol de elementos por nombre

        :raises typer.Abort: Si no se encuentra ningún elemento con el nombre
        """
        for group in self.board.posts:
            if (group.name or "").lower() == token.name:
                return group, None

            for post in group.posts:
                if (post.name or "").lower() == token.name:
                    return group, post

        message = render.ErrorPanel(f"The Token '{token}' does not match any element")
        self.console.print(message)
        raise typer.Abort()

    def build_index_token(self, group: PostGroup, post: Optional[Post] = None) -> IndexToken:
        """Obtener el IndexToken para un árbol de elementos"""
        try:
            main_index = self.board.index(group)
            sub_index = group.posts.index(post)
            return IndexToken.from_index(main_index, sub_index)
        except ValueError:
            message = render.ErrorPanel("Failed to create the IndexToken")
            self.console.print(message)
            raise typer.Abort()

    def print_kanban(self) -> None:
        kanban = render.Kanban(self.board, self.config)
        self.console.print(kanban)

    def ask_token(self) -> IndexToken:
        token = Prompt.ask("Enter a [token]Index Token[/]", console=self.console)
        try:
            return IndexToken(token)
        except ValueError:
            error = render.ErrorPanel("Invalid token")
            raise typer.Abort()
