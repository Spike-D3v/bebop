from datetime import datetime
from typing import Annotated, Optional, List

import typer
from rich.prompt import Confirm

from bebop.cli import render
from bebop.cli.config import BebopConfig
from bebop.cli.context import BebopContext
from bebop.models import Post, Todo, Comment, PostGroup
from bebop.token import IndexToken

app = typer.Typer(rich_markup_mode="rich")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    board_name: Annotated[Optional[str], typer.Option("--board", "-b", envvar="BEBOP_BOARD")] = None,
    dry_run: bool = False,
    debug: bool = False,
) -> None:
    """Simple Kanban CLI"""
    config = BebopConfig.load_config()
    manager = BebopContext(config, board_name, dry_run, debug)
    ctx.obj = manager
    if ctx.invoked_subcommand is None:
        manager.print_kanban()


@app.command("post")
def add_post(
    ctx: typer.Context,
    title: str,
    on_group: Annotated[IndexToken, typer.Argument(parser=IndexToken)],
    description: Annotated[Optional[str], typer.Option("--description", "-d")] = None,
    tags: Annotated[Optional[List[str]], typer.Option("--tag", "-t")] = None,
    todos: Annotated[Optional[List[str]], typer.Option("--todo", "-x")] = None,
    start_date: Annotated[Optional[datetime], typer.Option("--start-date", "-s")] = None,
    end_date: Annotated[Optional[datetime], typer.Option("--end-date", "-e")] = None,
    comments: Annotated[Optional[List[str]], typer.Option("--comment", "-c")] = None,
    name: Annotated[Optional[str], typer.Option("--name", "-n")] = None,
) -> None:
    """Add a new [blue]Post[/]"""
    manager: BebopContext = ctx.obj
    group, _ = manager.get_tree_by_index(on_group)
    post = Post(
        title=title,
        name=name,
        description=description,
        tags=tags,
        todos=[Todo(text=x) for x in todos],
        comments=[Comment(text=x) for x in comments],
        startDate=start_date,
        endDate=end_date,
    )
    group.posts.append(post)

    manager.save_board()
    manager.print_kanban()


@app.command("group")
def add_group(
    ctx: typer.Context,
    title: str,
    description: Annotated[Optional[str], typer.Option("--description", "-d")] = None,
    tags: Annotated[Optional[List[str]], typer.Option("--tag", "-t")] = None,
    comments: Annotated[Optional[List[str]], typer.Option("--comment", "-c")] = None,
    name: Annotated[Optional[str], typer.Option("--name", "-n")] = None,
    posts: Annotated[Optional[List[str]], typer.Option("--post", "-p")] = None,
) -> None:
    manager: BebopContext = ctx.obj
    group = PostGroup(
        title=title,
        name=name,
        description=description,
        tags=tags,
        comments=[Comment(text=x) for x in comments],
        posts=[Post(title=x) for x in posts],
    )
    manager.board.posts.append(group)
    manager.save_board()
    manager.print_kanban()


@app.command("add")
def add_element(
    ctx: typer.Context,
    title: str,
    on_group: Annotated[IndexToken, typer.Option("--on-group", "-o", parser=IndexToken)] = None,
    description: Annotated[Optional[str], typer.Option("--description", "-d")] = None,
    tags: Annotated[Optional[List[str]], typer.Option("--tag", "-t")] = None,
    todos: Annotated[Optional[List[str]], typer.Option("--todo", "-x")] = None,
    start_date: Annotated[Optional[datetime], typer.Option("--start-date", "-s")] = None,
    end_date: Annotated[Optional[datetime], typer.Option("--end-date", "-e")] = None,
    comments: Annotated[Optional[List[str]], typer.Option("--comment", "-c")] = None,
    name: Annotated[Optional[str], typer.Option("--name", "-n")] = None,
    posts: Annotated[Optional[List[str]], typer.Option("--post", "-p")] = None,
) -> None:
    """
    Add a new [bold green]PostGroup[/] or [blue]Post[/]
    """
    if on_group is not None:
        return add_post(ctx, title, on_group, description, tags, todos, start_date, end_date, comments, name)
    add_group(ctx, title, description, tags, comments, name, posts)


@app.command("push")
def push_elements() -> None:
    pass


@app.command("rm")
def remove_elements(
    ctx: typer.Context,
    tokens: Annotated[List[IndexToken], typer.Argument(parser=IndexToken)],
    omit_confirmation: Annotated[bool, typer.Option("--omit-confirmation", "-y")] = False,
) -> None:
    """
    Remove the elements at the given [red]INDEXES[red]
    """
    manager: BebopContext = ctx.obj

    elements = []
    for token in tokens:
        group, post = manager.get_tree_by_index(token)
        element = group if post is None else post
        source_list = manager.board.posts if post is None else group.posts
        if not omit_confirmation:
            panel = render.ElementInfo(element, token, manager.config)
            manager.console.print(panel)
            style = "group" if post is None else "post"
            result = Confirm.ask(
                f"Are you sure you want to delete [token]{token}[/] [{style}]{element.title}[/]?",
                console=manager.console,
                default=True,
            )
            if not result:
                continue
        elements.append((source_list, element))

    for source_list, element in elements:
        source_list.remove(element)

    manager.save_board()
    manager.print_kanban()


@app.command("show")
def show_elements(
    ctx: typer.Context,
    tokens: Annotated[Optional[List[IndexToken]], typer.Argument(parser=IndexToken)] = None,
) -> None:
    """"""
    manager: BebopContext = ctx.obj

    if not len(tokens):
        tokens = [IndexToken.from_index(idx) for idx in range(len(manager.board.posts))]

    for token in tokens:
        group, post = manager.get_tree_by_index(token)
        element = group if post is None else post
        panel = render.ElementInfo(element, token, manager.config)
        manager.console.print(panel)


@app.command("mv")
def move_element(
    ctx: typer.Context,
    from_token: Annotated[IndexToken, typer.Argument(parser=IndexToken)],
    to_token: Annotated[IndexToken, typer.Argument(parser=IndexToken)]
) -> None:
    """
    Move an Element
    """
    manager: BebopContext = ctx.obj
    source_group, source_post = manager.get_tree_by_index(from_token)
    source_element = source_group if source_post is None else source_post

    target_group, target_post = manager.get_tree_by_index(to_token)
    target_element = target_group if target_post is None else target_post

    if isinstance(source_element, PostGroup) and isinstance(target_element, Post):
        error = render.ErrorPanel("It is not possible to move a [group]PostGroup[/] to a [post]Post[/] position")
        manager.console.print(error)
        raise typer.Abort()

    source_list = manager.board.posts if source_post is None else source_group.posts
    source_list.remove(source_element)
    target_list = manager.board.posts if target_post is None else target_group.posts

    if isinstance(source_element, Post) and isinstance(target_element, PostGroup):
        target_list = target_group.posts
        target_list.append(source_element)
    else:
        target_index = target_list.index(target_element)
        target_list.insert(target_index, source_element)

    manager.save_board()
    manager.print_kanban()


@app.command("edit")
def edit_element() -> None:
    """Edit element data"""
    pass


@app.command("describe")
def edit_description() -> None:
    pass


@app.command("insert")
def insert_element() -> None:
    """Insertar un elemento"""
    pass


@app.command("archive")
def archive_elements() -> None:
    pass


@app.command("todo")
def append_todo() -> None:
    pass


@app.command("comment")
def append_comment() -> None:
    pass


@app.command("checkmarks")
def edit_post_checkmarks() -> None:
    pass


@app.command("open")
def open_board_file() -> None:
    pass
