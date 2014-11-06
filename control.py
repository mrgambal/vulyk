#!/usr/bin/env python

import click
from cli import admin as _admin
from cli import db as _db


@click.group()
def cli():
    """Pullenti UA management CLI"""


@cli.group('admin')
def admin():
    """Manages admin users"""
    pass


@admin.command('list')
def admin_list():
    """List admin users"""
    _admin.list_admin()


@admin.command('add')
@click.argument('email')
def admin_add(email):
    """Mark user as admin"""
    _admin.toggle_admin(email, True)


@admin.command('remove')
@click.argument('email')
def admin_remove(email):
    """Unmark user as admin"""
    _admin.toggle_admin(email, False)


@cli.group("db")
def db():
    """Commands to manage DB"""
    pass


@db.command("load")
@click.argument("name",
                type=click.Path(exists=True,
                                dir_okay=False,
                                readable=True,
                                resolve_path=True),
                nargs=-1)
def load(name):
    """Refills tasks collection from json."""
    _db.load_tasks(name)


if __name__ == '__main__':
    cli()