import calendar as c
from dataclasses import field, dataclass
from datetime import datetime
from typing import List

from rich import box
from rich.console import ConsoleOptions, Console, RenderResult
from rich.table import Table
from rich.text import Text

from bebop.cli.calendar.models import Scheduled
from bebop.cli.config import BebopConfig

WEEK_DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


@dataclass
class Calendar:
    """Renderiza un calendario"""

    events: List[Scheduled]
    config: BebopConfig
    date: datetime = field(default_factory=datetime.now)

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:

        month = MONTHS[self.date.month - 1]
        calendar = c.Calendar(6)
        table = Table(
            title=month,
            box=box.ROUNDED,
            border_style="board.box",
            expand=True,
            title_style="board",
            show_lines=True
        )

        for day in WEEK_DAYS:
            title = Text(day[0], justify="center")
            table.add_column(title, style="group")

        for week in calendar.monthdatescalendar(self.date.year, self.date.month):
            row = []
            for date in week:
                num_style = "green"
                if date.month != self.date.month:
                    num_style = "grey30"
                elif date.day == self.date.day:
                    num_style = "red"
                row.append(f"[{num_style}]{date.day}[/]\n\n")
            table.add_row(*row)

        yield table
