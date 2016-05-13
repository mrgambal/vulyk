#!/usr/bin/env python
# -*- coding=utf-8 -*-
import click
from veryprettytable import VeryPrettyTable, ALL

from vulyk.app import TASKS_TYPES, app
from vulyk.cli import (
    admin as _admin,
    batches as _batches,
    db as _db,
    groups as _groups,
    project_init as _project_init,
    stats as _stats)


def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


@click.group()
def cli():
    """Vulyk UA management CLI"""
    pass


@cli.command('run')
def run():
    """Start vulyk"""
    app.config.from_object('local_settings')
    app.run()


# region Admin
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


# endregion Admin

# region DB (export/import)
@cli.group('db')
def db():
    """Commands to manage DB"""
    pass


@db.command('load')
@click.argument('task_type', type=click.Choice(TASKS_TYPES.keys()))
@click.argument('path',
                type=click.Path(exists=True,
                                dir_okay=False,
                                readable=True,
                                resolve_path=True),
                nargs=-1)
@click.option('--batch',
              default=app.config['DEFAULT_BATCH'],
              callback=_batches.validate_batch,
              help='Specify the batch id tasks should be loaded into')
def load(task_type, path, batch):
    """Refills tasks collection from json."""
    count = _db.load_tasks(TASKS_TYPES[task_type], path, batch)

    if batch is not None and count > 0:
        _batches.add_batch(batch, count, task_type)


@db.command('export')
@click.argument('task_type', type=click.Choice(TASKS_TYPES.keys()))
@click.argument('path',
                type=click.Path(file_okay=True,
                                writable=True,
                                resolve_path=True))
@click.option('--batch',
              default=app.config['DEFAULT_BATCH'],
              type=click.Choice(_batches.batches_list() + ["__all__"]),
              help='Specify the batch id from which tasks should be exported. ' +
                   'Passing __all__ will export all tasks of a given type')
@click.option('--export-all', 'export_all', default=False, is_flag=True)
def export(task_type, path, batch, export_all):
    """Exports answers on closed tasks to json."""
    _db.export_tasks(TASKS_TYPES[task_type], path, batch, not export_all)


# endregion DB (export/import)

# region Group
@cli.group('group')
def group():
    """Groups management section"""
    pass


@group.command('list')
def group_show():
    for g in _groups.list_groups():
        click.echo(g)


@group.command('add')
@click.option('--gid',
              prompt='Specify string code (letters, numbers, underscores)',
              callback=_groups.validate_id)
@click.option('--description',
              prompt='Provide a short description (up to 200 characters)')
def group_add(gid, description):
    _groups.new_group(gid, description)


@group.command('del')
@click.option('--gid',
              prompt='Specify the group you want to remove',
              type=click.Choice(_groups.get_groups_ids()))
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to remove the group?')
def group_remove(gid):
    _groups.remove_group(gid)


@group.command('assign')
@click.option('--username',
              prompt='Provide the username')
@click.option('--gid',
              prompt='Specify the group you want to assign',
              type=click.Choice(_groups.get_groups_ids()))
def group_assign_to(username, gid):
    _groups.assign_to(username, gid)


@group.command('resign')
@click.option('--username',
              prompt='Provide the username')
@click.option('--gid',
              prompt='Specify the group you want to resign the user from',
              type=click.Choice(_groups.get_groups_ids()))
def group_resign_to(username, gid):
    _groups.resign(username, gid)


@group.command('addtype')
@click.option('--gid',
              prompt='Specify group\'s id',
              type=click.Choice(_groups.get_groups_ids()))
@click.option('--task_type',
              type=click.Choice(TASKS_TYPES.keys()),
              prompt='Provide the task type name')
def group_addtype(gid, task_type):
    _groups.add_task_type(gid, task_type=task_type)


@group.command('deltype')
@click.option('--gid',
              prompt='Specify group\'s id',
              type=click.Choice(_groups.get_groups_ids()))
@click.option('--task_type',
              type=click.Choice(TASKS_TYPES.keys()),
              prompt='Provide the task type name')
def group_deltype(gid, task_type):
    _groups.remove_task_type(gid, task_type=task_type)


# endregion Group

# region Bootstrapping
@cli.command('init')
@click.argument('allowed_types',
                type=click.Choice(TASKS_TYPES.keys()),
                nargs=-1)
def project_init(allowed_types):
    """
    Bootstrapping

    :type allowed_types: list[basestring]
    """
    if len(allowed_types) == 0:
        raise click.BadParameter('Please specify at least '
                                 'one default task type')

    _project_init(allowed_types)


# endregion Bootstrapping

# region Stats
@cli.group('stats')
def stats():
    """Commands to show some stats"""
    pass


@stats.command('batch')
@click.option('-n', '--batch_name', 'batch_name',
              type=click.Choice(_batches.batches_list()))
@click.option('-t', '--task_type', 'task_type',
              type=click.Choice(TASKS_TYPES.keys()))
def batch(batch_name, task_type):
    """
    Prints out some numbers which describe the state of tasks in certain batch
    """
    headers = ['Batch',
               'Total',
               'Completed (flag)',
               'Percent (flag)',
               'Answers',
               'Percent (answers)',
               'Breakdown (answers: tasks)']
    pt = VeryPrettyTable(headers)
    pt.align = 'l'
    pt.left_padding_width = 1
    pt.hrules = ALL

    for k, v in _stats.batch_completeness(batch_name, task_type).items():
        values = [k,
                  v['total'],
                  v['flag'],
                  '{:5.1f} %'.format(v['flag_percent']),
                  v['answers'],
                  '{:5.1f} %'.format(v['answers_percent']),
                  v['breakdown']]
        pt.add_row(values)

    print(pt)

# endregion Stats
