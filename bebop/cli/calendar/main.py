import typer

from . import render
from ..context import BebopContext

app = typer.Typer()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
):
    """calendar"""
    manager: BebopContext = ctx.obj
    calendar = render.Calendar([], manager.config)
    manager.console.print(calendar)


@app.command("month")
def show_month():
    """Muestra las actividades del mes"""
    pass


@app.command("week")
def show_week():
    """Muestra las actividades de la semana"""
    pass


@app.command("today")
def show_today():
    """Muestra las actividades del día"""
    pass
