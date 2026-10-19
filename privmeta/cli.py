import os
import sys

import click

from . import __version__
from .banner import show
from .commands import clean, fake, info, shred
from .errors import PrivMetaError
from .interactive import launch


def _clear():
    if not sys.stdout.isatty():
        return
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def _safe(func, args):
    try:
        return func(args)
    except PrivMetaError as exc:
        click.echo(f"[-] {exc}", err=True)
        sys.exit(2)
    except KeyboardInterrupt:
        click.echo("[!] interrupted", err=True)
        sys.exit(130)


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    _clear()
    show()
    if ctx.invoked_subcommand is None:
        launch()


@cli.command()
@click.argument("paths", nargs=-1, required=True)
@click.option("--all", "all_fields", is_flag=True, help="Remove every metadata segment.")
@click.option("--drop", help="Comma separated fields to remove.")
@click.option("--keep", help="Comma separated fields to keep.")
@click.option("--recursive", "-r", is_flag=True, help="Descend into subdirectories.")
@click.option("--output-dir", "-o", type=click.Path(file_okay=False), help="Write results here.")
@click.option("--inplace", is_flag=True, help="Replace the original file.")
@click.option("--keep-backup", is_flag=True, help="Keep a .bak copy before --inplace.")
@click.option("--rename", is_flag=True, help="Rename outputs to a neutral pattern.")
@click.option("--reset-time", is_flag=True, help="Reset filesystem timestamps.")
@click.option("--dry-run", is_flag=True, help="Report the plan without writing.")
@click.option("--fail-fast", is_flag=True, help="Stop at the first error.")
def clean_cmd(paths, **kwargs):
    namespace = type("Args", (), {})()
    namespace.paths = list(paths)
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    _safe(clean.run, namespace)


@cli.command()
@click.argument("paths", nargs=-1, required=True)
@click.option("--camera", help="Camera profile key.")
@click.option("--city", help="City key for GPS injection.")
@click.option("--radius", type=float, help="GPS radius in kilometres.")
@click.option("--date-range", help="START:END in ISO format.")
@click.option("--timeline", is_flag=True, help="Spread dates sequentially.")
@click.option("--preserve", is_flag=True, help="Merge over existing EXIF instead of replacing.")
@click.option("--thumbnail", is_flag=True, help="Regenerate the embedded thumbnail.")
@click.option("--seed", type=int, help="Seed for reproducible randomness.")
@click.option("--recursive", "-r", is_flag=True, help="Descend into subdirectories.")
@click.option("--output-dir", "-o", type=click.Path(file_okay=False), help="Write results here.")
@click.option("--inplace", is_flag=True, help="Replace the original file.")
@click.option("--fail-fast", is_flag=True, help="Stop at the first error.")
def fake_cmd(paths, **kwargs):
    namespace = type("Args", (), {})()
    namespace.paths = list(paths)
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    _safe(fake.run, namespace)


@cli.command()
@click.argument("paths", nargs=-1, required=True)
@click.option("--passes", type=int, default=1, show_default=True, help="Number of overwrite passes.")
@click.option("--quality", type=int, help="Re-encode JPEG at this quality.")
@click.option("--check", is_flag=True, help="Validate metadata after shredding.")
@click.option("--recursive", "-r", is_flag=True, help="Descend into subdirectories.")
@click.option("--output-dir", "-o", type=click.Path(file_okay=False), help="Write results here.")
@click.option("--inplace", is_flag=True, help="Replace the original file.")
@click.option("--fail-fast", is_flag=True, help="Stop at the first error.")
def shred_cmd(paths, **kwargs):
    namespace = type("Args", (), {})()
    namespace.paths = list(paths)
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    _safe(shred.run, namespace)


@cli.command()
@click.argument("paths", nargs=-1, required=True)
@click.option("--recursive", "-r", is_flag=True, help="Descend into subdirectories.")
def info_cmd(paths, **kwargs):
    namespace = type("Args", (), {})()
    namespace.paths = list(paths)
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    _safe(info.run, namespace)


cli.add_command(clean_cmd, "clean")
cli.add_command(fake_cmd, "fake")
cli.add_command(shred_cmd, "shred")
cli.add_command(info_cmd, "info")


@click.command()
def version():
    click.echo(f"PrivMeta {__version__}")


cli.add_command(version, "version")


def main():
    cli()