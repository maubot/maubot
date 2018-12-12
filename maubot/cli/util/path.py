import click
import os


def type_path(val: str) -> str:
    val = os.path.abspath(val)
    if os.path.exists(val):
        return val
    directory = os.path.dirname(val)
    if not os.path.isdir(directory):
        if os.path.exists(directory):
            raise click.BadParameter(f"{directory} is not a directory")
        raise click.BadParameter(f"{directory} does not exist")
    return val
