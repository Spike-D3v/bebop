from dataclasses import dataclass
from datetime import datetime

from bebop.models import BebopElement


@dataclass
class Scheduled:
    """Representa un elemento programado"""

    element: BebopElement
    date: datetime
