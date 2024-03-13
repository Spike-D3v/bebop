import curses
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Optional, List

import click
import typer
from rich.prompt import Confirm

from bebop.cli import render
from bebop.cli.config import BebopConfig
from bebop.cli.context import BebopContext
from bebop.cli.helpers import render_checkmarks_menu
from bebop.models import Post, Todo, Comment, PostGroup
from bebop.token import IndexToken

app = typer.Typer(rich_markup_mode="rich")


class HelpPanel(StrEnum):
    """Representa los grupos de comandos"""

    DATA = "Data :memo:"
    VIEW = "View :fire:"
    UTILS = "Utilities :toolbox:"


@app.callback(invoke_without_command=True, epilog="See you space cowboy :rocket:")
def main(
    ctx: typer.Context,
    board_name: Annotated[Optional[str], typer.Option("--board", "-b", envvar="BEBOP_BOARD")] = None,
    dry_run: bool = False,
    debug: bool = False,
) -> None:
    """
    Simple Kanban CLI tool

    Bebop is a tool for organizing your notes :memo:, tracking progress :chart_increasing:,
    or listing your pending tasks :white_check_mark:
    """
    config = BebopConfig.load_config()
    manager = BebopContext(config, board_name, dry_run, debug)
    ctx.obj = manager
    if ctx.invoked_subcommand is None:
        manager.print_kanban()


@app.command("post", rich_help_panel=HelpPanel.DATA)
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


@app.command("group", rich_help_panel=HelpPanel.DATA)
def add_group(
    ctx: typer.Context,
    title: str,
    description: Annotated[Optional[str], typer.Option("--description", "-d")] = None,
    tags: Annotated[Optional[List[str]], typer.Option("--tag", "-t")] = None,
    comments: Annotated[Optional[List[str]], typer.Option("--comment", "-c")] = None,
    name: Annotated[Optional[str], typer.Option("--name", "-n")] = None,
    posts: Annotated[Optional[List[str]], typer.Option("--post", "-p")] = None,
) -> None:
    """
    Add a new [green]PostGroup[/]
    """
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


@app.command("add", rich_help_panel=HelpPanel.DATA)
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


@app.command("push", rich_help_panel=HelpPanel.DATA)
def push_elements(
    ctx: typer.Context,
    titles: List[str],
    token: Annotated[Optional[IndexToken], typer.Option("--on-group", "-o", parser=IndexToken)] = None,
) -> None:
    """
    Add multiple items at once
    """
    manager: BebopContext = ctx.obj
    target_list = manager.board.posts
    model = PostGroup

    if token is not None:
        group, _ = manager.get_tree_by_index(token)
        target_list = group.posts
        model = Post

    for title in titles:
        element = model(title=title)
        target_list.append(element)

    manager.save_board()
    manager.print_kanban()


@app.command("rm", rich_help_panel=HelpPanel.DATA)
def remove_elements(
    ctx: typer.Context,
    tokens: Annotated[List[IndexToken], typer.Argument(parser=IndexToken)],
    omit_confirmation: Annotated[bool, typer.Option("--omit-confirmation", "-y")] = False,
) -> None:
    """
    Remove all the given elements
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


@app.command("show", rich_help_panel=HelpPanel.VIEW)
def show_elements(
    ctx: typer.Context,
    tokens: Annotated[Optional[List[IndexToken]], typer.Argument(parser=IndexToken)] = None,
) -> None:
    """
    Show detailed view of the given elements
    """
    manager: BebopContext = ctx.obj

    if not len(tokens):
        tokens = [IndexToken.from_index(idx) for idx in range(len(manager.board.posts))]

    for token in tokens:
        group, post = manager.get_tree_by_index(token)
        element = group if post is None else post
        panel = render.ElementInfo(element, token, manager.config)
        manager.console.print(panel)


@app.command("mv", rich_help_panel=HelpPanel.VIEW)
def move_element(
    ctx: typer.Context,
    from_token: Annotated[IndexToken, typer.Argument(parser=IndexToken)],
    to_token: Annotated[IndexToken, typer.Argument(parser=IndexToken)],
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


@app.command("edit", rich_help_panel=HelpPanel.DATA)
def edit_element(
    ctx: typer.Context,
    token: Annotated[Optional[IndexToken], typer.Argument(parser=IndexToken)] = None,
    title: Annotated[Optional[str], typer.Option("--title", "-T", help="Set a new title")] = None,
    description: Annotated[Optional[str], typer.Option("--description", "-d", help="Set a new description")] = None,
    start_date: Annotated[Optional[datetime], typer.Option("--start-date", "-s", help="Set a new start date")] = None,
    end_date: Annotated[Optional[datetime], typer.Option("--end-date", "-e", help="Set a new end date")] = None,
    tags: Annotated[Optional[List[str]], typer.Option("--tag", "-t", help="Set new tags for the element")] = None,
    todos: Annotated[Optional[List[str]], typer.Option("--todo", "-x", help="Set new todos for the element")] = None,
    name: Annotated[Optional[str], typer.Option("--name", "-n", help="Set a new name")] = None,
) -> None:
    """
    Edit data of the given Element.
    """
    manager: BebopContext = ctx.obj
    if token is None:
        manager.print_kanban()
        token = manager.ask_token()

    group, post = manager.get_tree_by_index(token)
    element = group if post is None else post

    if title is not None:
        element.title = title
    if name is not None:
        element.name = name
    if description is not None:
        element.description = description
    if len(tags):
        element.tags = tags

    if len(todos):
        if isinstance(element, Post):
            element.todos = [Todo(text=x) for x in todos]
        else:
            help_panel = render.HelpPanel("The [green]--todo[/] option only applies to [post]Post[/] elements")
            manager.console.print(help_panel)

    if start_date is not None:
        if isinstance(element, Post):
            element.start_date = start_date
        else:
            help_panel = render.HelpPanel("The [green]--start-date[/] option only applies to [post]Post[/] elements")
            manager.console.print(help_panel)

    if end_date is not None:
        if isinstance(element, Post):
            element.end_date = end_date
        else:
            help_panel = render.HelpPanel("The [green]--end-date[/] option only applies to [post]Post[/] elements")
            manager.console.print(help_panel)

    manager.save_board()
    info = render.ElementInfo(element, token, manager.config)
    manager.console.print(info)


@app.command("describe", rich_help_panel=HelpPanel.DATA)
def edit_description(
    ctx: typer.Context,
    token: Annotated[Optional[IndexToken], typer.Argument(parser=IndexToken)] = None,
    description: Annotated[Optional[str], typer.Argument(parser=IndexToken)] = None,
) -> None:
    """
    Add or edit the description of the given Element
    """
    manager: BebopContext = ctx.obj

    if token is None:
        manager.print_kanban()
        token = manager.ask_token()

    group, post = manager.get_tree_by_index(token)
    element = group if post is None else post

    if description is None:
        description = click.edit(element.description)

    element.description = description
    manager.save_board()

    panel = render.ElementInfo(element, token, manager.config)
    manager.console.print(panel)


@app.command("insert", rich_help_panel=HelpPanel.DATA)
def insert_element(
    ctx: typer.Context,
    title: str,
    token: Annotated[Optional[IndexToken], typer.Argument(parser=IndexToken)] = None,
    description: Annotated[Optional[str], typer.Option("--description", "-d")] = None,
    tags: Annotated[Optional[List[str]], typer.Option("--tag", "-t")] = None,
    todos: Annotated[Optional[List[str]], typer.Option("--todo", "-x")] = None,
    start_date: Annotated[Optional[datetime], typer.Option("--start-date", "-s")] = None,
    end_date: Annotated[Optional[datetime], typer.Option("--end-date", "-e")] = None,
    comments: Annotated[Optional[List[str]], typer.Option("--comment", "-c")] = None,
    name: Annotated[Optional[str], typer.Option("--name", "-n")] = None,
    posts: Annotated[Optional[List[str]], typer.Option("--post", "-p")] = None,
) -> None:
    """Insertar un elemento"""
    manager: BebopContext = ctx.obj

    if token is None:
        manager.print_kanban()
        token = manager.ask_token()

    group, post = manager.get_tree_by_index(token)

    if post is None:
        element = PostGroup(
            title=title,
            name=name,
            description=description,
            tags=tags,
            comments=[Comment(text=x) for x in comments],
            posts=[Post(title=x) for x in posts],
        )
        idx = manager.board.posts.index(group)
        manager.board.posts.insert(idx, element)
    else:
        element = Post(
            title=title,
            name=name,
            description=description,
            tags=tags,
            todos=[Todo(text=x) for x in todos],
            comments=[Comment(text=x) for x in comments],
            startDate=start_date,
            endDate=end_date,
        )
        idx = group.posts.index(post)
        group.posts.insert(idx, element)

    manager.save_board()
    manager.print_kanban()


@app.command("archive", rich_help_panel=HelpPanel.VIEW)
def archive_elements() -> None:
    """[dim]Coming soon... :smile:[/]"""
    pass


@app.command("todo", rich_help_panel=HelpPanel.DATA)
def append_todo(
    ctx: typer.Context,
    text: str,
    token: Annotated[Optional[IndexToken], typer.Argument(parser=IndexToken)] = None,
    checked: Annotated[bool, typer.Option("--checked", "-X")] = False,
) -> None:
    """
    Append a new To-Do to the given [blue]Post[/]
    """
    manager: BebopContext = ctx.obj
    if token is None:
        manager.print_kanban()
        token = manager.ask_token()

    group, post = manager.get_tree_by_index(token)
    if post is None:
        error = render.ErrorPanel("A [group]PostGroup[/] element does not support todos")
        manager.console.print(error)
        raise typer.Abort()

    todo = Todo(text=text, checked=checked)
    post.todos.append(todo)

    manager.save_board()

    info = render.ElementInfo(post, token, manager.config)
    manager.console.print(info)


@app.command("comment", rich_help_panel=HelpPanel.DATA)
def append_comment(
    ctx: typer.Context,
    text: str,
    token: Annotated[Optional[IndexToken], typer.Argument(parser=IndexToken)] = None,
) -> None:
    """
    Append a new comment to the given Element
    """
    manager: BebopContext = ctx.obj
    if token is None:
        manager.print_kanban()
        token = manager.ask_token()

    group, post = manager.get_tree_by_index(token)
    element = group if post is None else post

    comment = Comment(text=text)
    element.comments.append(comment)
    manager.save_board()

    info = render.ElementInfo(element, token, manager.config)
    manager.console.print(info)


@app.command("checkmarks", rich_help_panel=HelpPanel.DATA)
def edit_post_checkmarks(
    ctx: typer.Context,
    token: Annotated[Optional[IndexToken], typer.Argument(parser=IndexToken)] = None,
) -> None:
    """
    Edit the checkmarks of the given [blue]Post[/] To-Do's
    """
    manager: BebopContext = ctx.obj
    if token is None:
        manager.print_kanban()
        token = manager.ask_token()

    _, post = manager.get_tree_by_index(token)
    if post is None:
        error = render.ErrorPanel("A [group]PostGroup[/] element does not support todos")
        manager.console.print(error)
        raise typer.Abort()

    if not len(post.todos):
        error = render.ErrorPanel(
            f"The [blue]Post[/] '[token]{token}[/] [post]{post.title}[/]' does not have any [todos]TODO[/]"
        )
        manager.console.print(error)
        raise typer.Exit()

    curses.wrapper(render_checkmarks_menu(post))
    manager.save_board()

    info = render.ElementInfo(post, token, manager.config)
    manager.console.print(info)


@app.command("open", rich_help_panel=HelpPanel.UTILS)
def open_board_file(ctx: typer.Context) -> None:
    """
    Open the current board file in your preferred editor
    """
    manager: BebopContext = ctx.obj
    typer.launch(str(manager.board_path))
