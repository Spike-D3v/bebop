# Bebop Kanban CLI

A simple command line interface tool for Kanban boards management.

## Install

### Requirements
You must have **python3.11+** installed.

### Build with Poetry

Clone the repository
```shell
$ git clone git@github.com:Spike-D3v/bebop.git
```

Install dependencies with [Poetry](https://python-poetry.org/)
```shell
$ poetry install
```

Build the project
```shell
$ poetry build
```

Install for current user, replacing `<bebop_sources_dir>` with the path where you cloned the repository, and the `<x>` with the version
```shell
$ pip install -u /<bebop_sources_dir>/dist/bebop-<x>.tar.gz
```

> Note: The preferred way to install is with [Pipx](https://github.com/pypa/pipx)

## Usage

Use `bebop` command to display the entire board

```shell
bebop
# displays the default board
```

You can manage multiple boards by passing the `--board` option

```shell
bebop --board my_stuff
# displays 'my_stuff' board
```

You can achieve the same by setting the board name as `BEBOP_BOARD` environment variable.
```shell
export BEBOP_BOARD=my_stuff
bebop
# displays 'my_stuff' board
```

Find more useful commands by passing the `--help` option
```shell
bebop --help
```

## Acknowledgements

- [Typer](https://github.com/tiangolo/typer/)
- [Rich](https://github.com/Textualize/rich)
- [Pydantic](https://github.com/pydantic/pydantic)
