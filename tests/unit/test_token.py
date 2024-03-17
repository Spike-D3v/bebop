from typing import Tuple

import pytest

from bebop.token import IndexToken


class TestIndexToken:

    @pytest.mark.parametrize("invalid_token", ["1", "1A", "", "_", " "])
    def test_invalid_token(self, invalid_token: str):
        """Comprobar tokens inválidos"""
        with pytest.raises(ValueError) as exc_info:
            IndexToken(invalid_token)
        assert str(exc_info.value) == f"'{invalid_token}' is not a valid IndexToken"

    @pytest.mark.parametrize("valid_token", ["A", "A1", "AA1", "zz1"])
    def test_valid_token(self, valid_token: str):
        """Comprobar tokens válidos"""
        token = IndexToken(valid_token)
        assert token == valid_token.upper()

    @pytest.mark.parametrize("input_token", ["A", "b1", "AA1", "zz1", "c2"])
    def test_main_index_is_positive_int(self, input_token: str):
        """Comprobar que el main index es un número entero positivo"""
        token = IndexToken(input_token)
        assert isinstance(token.main_index, int)
        assert token.main_index >= 0

    def test_first_main_index_is_zero(self):
        """Comprobar que el primer índice es cero"""
        token = IndexToken("A")
        assert token.main_index == 0

    @pytest.mark.parametrize("token_value", [("A", 0), ("Z", 25), ("AA", 26), ("ZZ", 701)])
    def test_main_index_range(self, token_value: Tuple[str, int]):
        """Comprobar la correspondencia de las letras a los índices"""
        token = IndexToken(token_value[0])
        assert token.main_index == token_value[1]

    @pytest.mark.parametrize("input_token", ["a1", "a100", "b20", "z333"])
    def test_sub_index_is_positive_int(self, input_token: str):
        """Comprobar que el subíndice del token siempre es entero positivo"""
        token = IndexToken(input_token)
        assert token.sub_index >= 0

    def test_first_sub_index_is_zero(self):
        """Comprobar que el primer subíndice es cero"""
        token = IndexToken("a1")
        assert token.sub_index == 0

    @pytest.mark.parametrize("index_token", [(0, "A"), (25, "Z"), (26, "AA"), (702, "AAA")])
    def test_from_main_index(self, index_token: Tuple[int, str]):
        """Comprobar generación de token a partir de un índice primario"""
        token = IndexToken.from_index(index_token[0])
        assert token == index_token[1]

    @pytest.mark.parametrize("index", [0, 10, 723, 9, 26])
    def test_from_sub_index(self, index: int):
        """Comprobar generación de subíndices"""
        token = IndexToken.from_index(0, index)
        assert token == f"A{index+1}"
