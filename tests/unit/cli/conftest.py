import pytest
from typer.testing import CliRunner

from bebop.cli.main import app


@pytest.fixture()
def runner():
    yield CliRunner()


def cli():
    yield app
