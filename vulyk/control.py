#!/usr/bin/env python
# coding=utf-8

import click
from cli import admin as _admin, db as _db, groups as _groups
from app import TASKS_TYPES


def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


@click.group()
def cli():
    """Vulyk UA management CLI"""


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
@click.argument('task_type', type=click.Choice(TASKS_TYPES.keys()))
@click.argument("name",
                type=click.Path(exists=True,
                                dir_okay=False,
                                readable=True,
                                resolve_path=True),
                nargs=-1)
def load(task_type, name):
    """Refills tasks collection from json."""
    _db.load_tasks(TASKS_TYPES[task_type], name)


@cli.group("group")
def group():
    """Groups management section"""
    pass


@group.command("list")
def group_show():
    for g in _groups.list_groups():
        click.echo(g)


@group.command("add")
@click.option("--gid",
              prompt="Specify string code (letters, numbers, underscores)",
              callback=_groups.validate_id)
@click.option("--description",
              prompt="Provide a short description (up to 200 symbols)")
def group_add(gid, description):
    _groups.new_group(gid, description)


@group.command("del")
@click.option("--gid",
              prompt="Specify the group you want to remove",
              type=click.Choice(_groups.get_groups_ids()))
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to remove the group?')
def group_remove(gid):
    _groups.remove_group(gid)


@group.command("assign")
@click.option("--username",
              prompt="Provide the username")
@click.option("--gid",
              prompt="Specify the group you want to assign",
              type=click.Choice(_groups.get_groups_ids()))
def group_assign_to(username, gid):
    _groups.assign_to(username, gid)


@group.command("resign")
@click.option("--username",
              prompt="Provide the username")
@click.option("--gid",
              prompt="Specify the group you want to resign the user from",
              type=click.Choice(_groups.get_groups_ids()))
def group_assign_to(username, gid):
    _groups.resign(username, gid)


@click.option("--gid",
              prompt="Specify group's id",
              type=click.Choice(_groups.get_groups_ids()))
@group.command("addtype")
@click.option("--task_type",
              prompt="Provide the task type name")
def group_addtype(gid, task_type):
    _groups.add_task_type(gid, task_type=task_type)


@click.option("--gid",
              prompt="Specify group's id",
              type=click.Choice(_groups.get_groups_ids()))
@group.command("deltype")
@click.option("--task_type",
              prompt="Provide the task type name")
def group_deltype(gid, task_type):
    _groups.remove_task_type(gid, task_type=task_type)
