# -*- coding=utf-8 -*-
import re
from typing import Generator, List

import click

from vulyk.models.user import Group, User


def get_groups_ids() -> List[str]:
    """
    Returns list of groups codes

    :rtype : list[str]
    """
    return Group.objects().scalar('id')


def validate_id(ctx,
                param: str,
                value: str) -> str:
    """
    Allows group code to consist only of letters/numbers/underscore

    :param ctx: Click context
    :param param: Name of parameter (`id`)
    :type param: str
    :param value: Value of `id` parameter
    :type value: str

    :return: true if value passes
    :rtype: str

    :raise click.BadParameter:
    """
    if re.match("^[A-z0-9]+[A-z0-9_]+$", value):
        return value
    else:
        raise click.BadParameter('Only letters, numbers, underscores '
                                 'are allowed. Underscore can\'t go first')


def list_groups() -> Generator[str, None, None]:
    """
    Generates list of group representation strings

    :rtype : _generator[str]
    """
    return (repr(g) for g in Group.objects.all())


def new_group(gid: str, description: str) -> None:
    """
    Creates new group

    :param gid: Group's symbolic code
    :type gid: str
    :param description: Short description (optional)
    :type description: str

    :raise click.BadParameter: if wrong `id` has been passed
    """
    try:
        Group.objects.create(id=gid, description=description)
    except Group.DoesNotExist:
        raise click.BadParameter('No group was found with id ' + gid)


def remove_group(gid: str) -> None:
    """
    Delete existing group

    :param gid: Group's symbolic code
    :type gid: str

    :raise click.BadParameter: if wrong `id` has been passed
    """
    try:
        Group.objects.get(id=gid).delete()
    except Group.DoesNotExist:
        raise click.BadParameter('No group was found with id ' + gid)


def add_task_type(gid: str, task_type: str) -> None:
    """
    Appends task type to the list of allowed ones of certain group

    :param gid: Group's symbolic code
    :type gid: str
    :param task_type: Task type symbolic code
    :type task_type: str

    :raise click.BadParameter: if wrong `gid` has been passed
    """
    try:
        Group.objects.get(id=gid).update(add_to_set__allowed_types=task_type)
    except Group.DoesNotExist:
        raise click.BadParameter('No group was found with id ' + gid)


def remove_task_type(gid: str, task_type: str) -> None:
    """
    Removes task type from the list of allowed types of specified group

    :param gid: Group's symbolic code
    :type gid: str
    :param task_type: Task type symbolic code
    :type task_type: str

    :raise click.BadParameter: if wrong `gid` has been passed
    """
    try:
        Group.objects.get(id=gid).update(pull__allowed_types=task_type)
    except Group.DoesNotExist:
        raise click.BadParameter('No group was found with id ' + gid)


def assign_to(username: str, gid: str) -> None:
    """
    Assigns a group to user

    :param gid: Group's symbolic code
    :type gid: str
    :param username: Username of member
    :type username: str

    :raise click.BadParameter: if wrong `gid` or ` username` has been passed
    """
    try:
        User.objects.get(username=username) \
            .update(add_to_set__groups=Group.objects.get(id=gid))
    except User.DoesNotExist:
        raise click.BadParameter('No user was found with username ' + username)
    except Group.DoesNotExist:
        raise click.BadParameter('No group was found with id ' + gid)


def resign(username: str, gid: str) -> None:
    """
    Excludes user from specified group

    :param gid: Group's symbolic code
    :type gid: str
    :param username: Username of member
    :type username: str

    :raise click.BadParameter: if wrong `gid` or ` username` has been passed
    """
    try:
        User.objects.get(username=username) \
            .update(pull__groups=Group.objects.get(id=gid))
    except User.DoesNotExist:
        raise click.BadParameter('No user was found with username ' + username)
    except Group.DoesNotExist:
        raise click.BadParameter('No group was found with id ' + gid)
