from dataclasses import dataclass
from typing import List, Union

from rich import box
from rich.console import RenderResult, ConsoleOptions, Console, ConsoleRenderable, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from bebop.models import Board, PostGroup, Post, Comment
from bebop.token import IndexToken
from .config import BebopConfig


def tags_line(tags: List[str]) -> str:
    return " ".join([f"[tag]{x}[/]" for x in tags])


def icons_line(element: PostGroup | Post) -> str:
    icons = []
    if element.description is not None:
        icons.append(":memo:")

    if element.description_file is not None:
        icons.append(":paperclip:")

    if getattr(element, "start_date", None) is not None:
        icons.append(":calendar:")

    if getattr(element, "end_date", None) is not None:
        icons.append(":alarm_clock:")

    if len(element.comments):
        icons.append(":speech_balloon:")

    if len(getattr(element, "todos", [])):
        icons.append(f"| [todos]{element.todo_progress}%[/]")
    return " ".join(icons)


@dataclass
class HelpPanel:
    """Renderiza un mensaje de ayuda"""

    data: ConsoleRenderable | str
    config: BebopConfig | None = None

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield Panel(self.data, title=":question: Help", border_style="help")


@dataclass
class ErrorPanel:
    """Renderiza un mensaje de error"""

    data: ConsoleRenderable | str
    config: BebopConfig | None = None

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield Panel(self.data, title=":exclamation: Error", border_style="error")


@dataclass
class PostPlate:
    """Renderiza un post como tarjeta"""

    post: Post
    token: IndexToken
    config: BebopConfig

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        group = Group(
            f"[token]{self.token}[/] [post]{self.post.title}[/]",
            f"[ref]@{self.post.name.lower()}[/]" if self.post.name is not None else "",
            tags_line(self.post.tags),
            icons_line(self.post),
        )
        yield Panel(
            group,
            border_style="post.box",
            subtitle=self.post.author,
        )


@dataclass
class DescriptionBox:
    """Renderizar panel de descripción"""

    description: str

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        group = Group("", Markdown(self.description), "")
        yield Panel(
            group,
            title=":memo: Description",
            title_align="left",
            box=box.HORIZONTALS,
            style="description",
            border_style="description",
        )


@dataclass
class TodosBox:
    """Renderizar panel de TODOS"""

    post: Post

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        rows = [""]
        for todo in self.post.todos:
            checkmark = ":white_check_mark:" if todo.checked else "  "
            rows.append(f"[todos]- \[{checkmark}] {todo.text}[/]")
        rows.append("")

        yield Panel(
            Group(*rows),
            title=f"To Do - {self.post.todo_progress}%",
            title_align="left",
            box=box.HORIZONTALS,
            style="todos",
            border_style="todos.box",
        )


@dataclass
class CommentsBox:
    """Renderiza la caja de comentarios"""

    comments: List[Comment]
    config: BebopConfig

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        rows = [""]

        for comment in self.comments:
            date_str = comment.created_at.strftime(self.config.datetime_format)
            rows.append(f"> \[{date_str}]:\n    {comment.text}")
        rows.append("")

        yield Panel(
            Group(*rows),
            title=":speech_balloon: Comments",
            title_align="left",
            box=box.HORIZONTALS,
            style="comments",
            border_style="comments.box",
        )


@dataclass
class ElementInfo:
    """Renderiza un elemento como panel detallado"""

    element: Union[Post, PostGroup]
    token: IndexToken
    config: BebopConfig

    @property
    def style(self) -> str:
        return "post" if isinstance(self.element, Post) else "group"

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        parts = [
            f"[token]{self.token}[/] [{self.style}]{self.element.title}[/]",
            f"[ref]@{self.element.name.lower()}[/]" if self.element.name is not None else "",
            "",
        ]

        if len(self.element.tags):
            parts.append("Tags:")
            parts.append("    " + tags_line(self.element.tags))
            parts.append("")

        if getattr(self.element, "start_date", None) is not None:
            date_str = self.element.start_date.strftime(self.config.datetime_format)
            parts.append("Start Date:")
            parts.append(f"    [date]{date_str}[/]")
            parts.append("")

        if getattr(self.element, "end_date", None) is not None:
            date_str = self.element.end_date.strftime(self.config.datetime_format)
            parts.append("End Date:")
            parts.append(f"    [date]{date_str}[/]")
            parts.append("")

        if self.element.description is not None:
            parts.append(DescriptionBox(self.element.description))
            parts.append("")

        if len(getattr(self.element, "todos", [])):
            parts.append(TodosBox(self.element))
            parts.append("")

        if getattr(self.element, "posts", None) is not None:
            if len(self.element.posts):
                for sub_idx, post in enumerate(self.element.posts):
                    token = IndexToken.from_index(self.token.main_index, sub_idx)
                    parts.append(PostPlate(post, token, self.config))
            else:
                help_panel = HelpPanel(
                    "Empty Group. Try to add a [post]Post[/] with:\n"
                    f"'[white][green]bebop[/] push -o [token]{self.token}[/] [dim]\[OPTIONS][/] TITLE[/]'"
                )
                parts.append(help_panel)
            parts.append("")

        if len(self.element.comments):
            parts.append(CommentsBox(self.element.comments, self.config))
            parts.append("")

        if len(self.element.comments):
            parts.append("")

        group = Group(*parts)
        yield Panel(group, border_style=f"{self.style}.box", subtitle=self.element.author)


@dataclass
class Kanban:
    """Renderiza el Kanban"""

    board: Board
    config: BebopConfig

    def _render_group(self, group: PostGroup, token: IndexToken) -> ConsoleRenderable:
        return Group(
            f"[token]{token}[/] [group]{group.title}[/]",
            f"[ref]@{group.name.lower()}[/]" if group.name is not None else "",
            tags_line(group.tags),
            icons_line(group),
        )

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        if not len(self.board.active_posts):
            yield HelpPanel("Hola", self.config)

        table = Table(
            title=self.board.title,
            title_style="board",
            caption=self.board.author,
            box=box.MINIMAL,
            border_style="board.box",
            expand=True,
        )

        max_idx = 0
        for idx, group in enumerate(self.board.active_posts):
            token = IndexToken.from_index(idx)
            header = self._render_group(group, token)
            table.add_column(header)
            max_idx = max(max_idx, len(group.active_posts))

        for sub_idx in range(max_idx):
            row = []
            for main_idx, group in enumerate(self.board.active_posts):
                cell = ""
                if sub_idx < len(group.active_posts):
                    post = group.posts[sub_idx]
                    token = IndexToken.from_index(main_idx, sub_idx)
                    cell = PostPlate(post, token, self.config)
                row.append(cell)
            table.add_row(*row)

        yield table
