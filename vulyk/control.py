#!/usr/bin/env python
# -*- coding=utf-8 -*-

from typing import Any

import click
from prettytable import ALL, PrettyTable

from vulyk.app import TASKS_TYPES, app
from vulyk.cli import admin as _admin
from vulyk.cli import batches as _batches
from vulyk.cli import db as _db
from vulyk.cli import groups as _groups
from vulyk.cli import project_init as _project_init
from vulyk.cli import stats as _stats


def abort_if_false(ctx: click.Context, param: click.Parameter, value: Any) -> None:
    if not value:
        ctx.abort()


@click.group()
def cli() -> None:
    """Vulyk UA management CLI."""


@cli.command("run")
def run() -> None:
    """Start vulyk."""
    app.run()


# region Admin
@cli.group("admin")
def admin() -> None:
    """Manages admin users."""


@admin.command("list")
def admin_list() -> None:
    """List admin users."""
    _admin.list_admin()


@admin.command("add")
@click.argument("email")
def admin_add(email: str) -> None:
    """Mark user as admin."""
    _admin.toggle_admin(email, state=True)


@admin.command("remove")
@click.argument("email")
def admin_remove(email: str) -> None:
    """Unmark user as admin."""
    _admin.toggle_admin(email, state=False)


# endregion Admin


# region DB (export/import)
@cli.group("db")
def db() -> None:
    """Commands to manage DB."""


@db.command("load")
@click.argument("task_type", type=click.Choice(list(TASKS_TYPES.keys())))
@click.argument("path", type=click.Path(exists=True, dir_okay=False, readable=True, resolve_path=True), nargs=-1)
@click.option("--meta", multiple=True, type=(str, str), help="Override meta information for the batch")
@click.option(
    "--batch",
    default=app.config["DEFAULT_BATCH"],
    callback=lambda ctx, param, value: _batches.validate_batch(ctx, param, value, app.config["DEFAULT_BATCH"]),
    help="Specify the batch id tasks should be loaded into",
)
def load(task_type: str, path: str, meta: tuple[str, str], batch: str) -> None:
    """Refills tasks collection from json.."""
    task_type_obj = TASKS_TYPES[task_type]
    count = _db.load_tasks(task_type_obj, path, batch)

    if batch is not None and count > 0:
        _batches.add_batch(
            batch_id=batch,
            count=count,
            task_type=task_type_obj,
            default_batch=app.config["DEFAULT_BATCH"],
            batch_meta=dict(meta),
        )


@db.command("export")
@click.argument("task_type", type=click.Choice(list(TASKS_TYPES.keys())))
@click.argument("path", type=click.Path(file_okay=True, writable=True, resolve_path=True))
@click.option(
    "--batch",
    default=app.config["DEFAULT_BATCH"],
    type=click.Choice([*_batches.batches_list(), "__all__"]),
    help="Specify the batch id from which tasks should be exported. "
    "Passing __all__ will export all tasks of a given type",
)
@click.option("--export-all", "export_all", default=False, is_flag=True)
def export(task_type: str, path: str, batch: str, *, export_all: bool) -> None:
    """Exports answers to chosen tasks to json."""
    _db.export_reports(TASKS_TYPES[task_type], path, batch, closed=not export_all)


# endregion DB (export/import)


# region Group
@cli.group("group")
def group() -> None:
    """Groups management section."""


@group.command("list")
def group_show() -> None:
    for g in _groups.list_groups():
        click.echo(g)


@group.command("add")
@click.option("--gid", prompt="Specify string code (letters, numbers, underscores)", callback=_groups.validate_id)
@click.option("--description", prompt="Provide a short description (up to 200 characters)")
def group_add(gid: str, description: str) -> None:
    _groups.new_group(gid, description)


@group.command("del")
@click.option("--gid", prompt="Specify the group you want to remove", type=click.Choice(_groups.get_groups_ids()))
@click.option(
    "--yes",
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt="Are you sure you want to remove the group?",
)
def group_remove(gid: str) -> None:
    _groups.remove_group(gid)


@group.command("assign")
@click.option("--username", prompt="Provide the username")
@click.option("--gid", prompt="Specify the group you want to assign", type=click.Choice(_groups.get_groups_ids()))
def group_assign_to(username: str, gid: str) -> None:
    _groups.assign_to(username, gid)


@group.command("resign")
@click.option("--username", prompt="Provide the username")
@click.option(
    "--gid", prompt="Specify the group you want to resign the user from", type=click.Choice(_groups.get_groups_ids())
)
def group_resign_to(username: str, gid: str) -> None:
    _groups.resign(username, gid)


@group.command("addtype")
@click.option("--gid", prompt="Specify group's id", type=click.Choice(_groups.get_groups_ids()))
@click.option("--task_type", type=click.Choice(list(TASKS_TYPES.keys())), prompt="Provide the task type name")
def group_addtype(gid: str, task_type: str) -> None:
    _groups.add_task_type(gid, task_type=task_type)


@group.command("deltype")
@click.option("--gid", prompt="Specify group's id", type=click.Choice(_groups.get_groups_ids()))
@click.option("--task_type", type=click.Choice(list(TASKS_TYPES.keys())), prompt="Provide the task type name")
def group_deltype(gid: str, task_type: str) -> None:
    _groups.remove_task_type(gid, task_type=task_type)


# endregion Group


# region Bootstrapping
@cli.command("init")
@click.argument("allowed_types", type=click.Choice(list(TASKS_TYPES.keys())), nargs=-1)
def project_init(allowed_types: list[str]) -> None:
    """
    Bootstrapping

    :param allowed_types: list of allowed task types.
    """
    if len(allowed_types) == 0:
        raise click.BadParameter("Please specify at least one default task type")

    _project_init(allowed_types)


# endregion Bootstrapping


# region Stats
@cli.group("stats")
def stats() -> None:
    """Commands to show some stats."""


@stats.command("batch")
@click.option("-n", "--batch_name", "batch_name", type=click.Choice(_batches.batches_list()))
@click.option("-t", "--task_type", "task_type", type=click.Choice(list(TASKS_TYPES.keys())))
def batch(batch_name: str, task_type: str) -> None:
    """
    Prints out some numbers which describe the state of tasks in certain batch.
    """
    headers = [
        "Batch",
        "Total",
        "Completed (flag)",
        "Percent (flag)",
        "Answers",
        "Percent (answers)",
        "Breakdown (answers: tasks)",
    ]
    pt = PrettyTable(headers)
    pt.align = "l"
    pt.left_padding_width = 1
    pt.hrules = ALL

    for k, v in _stats.batch_completeness(batch_name, task_type).items():
        values = [
            k,
            v["total"],
            v["flag"],
            "{:5.1f} %".format(v["flag_percent"]),
            v["answers"],
            "{:5.1f} %".format(v["answers_percent"]),
            v["breakdown"],
        ]
        pt.add_row(values)
    click.echo(pt.get_string())


# endregion Stats
