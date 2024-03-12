import re
from collections import UserString
from typing import Optional, ClassVar, Pattern

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
reference_token_pattern = re.compile(r"^@[a-z0-9_]+$")
index_token_pattern = re.compile(r"^[A-Z]+[0-9]*$")
range_token_pattern = re.compile(r"^([A-Z]+[0-9]*)?:[A-Z]*[0-9]*$")


class Token(UserString):
    """Representa un identificador de un elemento"""

    pattern: ClassVar[Pattern] = re.compile(r"^(@[a-z0-9_]+|(([A-Z]+[0-9]*)?:[A-Z]*[0-9]*|[A-Z]+[0-9]*))$")

    def __init__(self, value: str):
        if self.pattern.match(value) is None:
            raise ValueError(f"'{value}' is not a valid {self.__class__.__name__}")
        super().__init__(value)

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return cls.pattern.match(value) is not None


class RefToken(Token):
    """Representa un identificador de nombre de un elemento"""

    pattern = reference_token_pattern

    def __init__(self, value: str):
        super().__init__(value.lower())

    @property
    def name(self) -> str:
        return self[1:]

    @classmethod
    def from_name(cls, name: str) -> "RefToken":
        return cls(f"@{name}")


class IndexToken(Token):
    """Representa un identificador de índice"""

    pattern = index_token_pattern

    def __init__(self, value: str):
        super().__init__(value.upper())

    @property
    def main_index(self) -> int:
        chars = self._get_chars()
        total = 0
        length = len(chars) - 1
        for char in chars:
            index = ALPHABET.index(char) + 1
            total += (26**length) * index
            length -= 1
        return total - 1

    @property
    def sub_index(self) -> Optional[int]:
        sub = re.sub(r"[A-Z]", "", str(self))
        return int(sub) - 1 if sub != "" else None

    def _get_chars(self) -> str:
        return re.sub(r"\d", "", str(self))

    @classmethod
    def from_index(cls, idx: int, sub_idx: Optional[int] = None) -> "IndexToken":
        idx = abs(idx) + 1
        chars = ""
        while idx > 0:
            res = (idx - 1) % 26
            chars = ALPHABET[res] + chars
            idx = (idx - 1) // 26
        sub = sub_idx + 1 if sub_idx is not None else ""
        char = chars or "A"
        return cls(f"{char}{sub}")


class TokenRange(Token):
    """Representa un identificador de rango de índices"""

    pattern = range_token_pattern

    def __init__(self, value: str):
        super().__init__(value.upper())
