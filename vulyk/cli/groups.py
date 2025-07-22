# -*- coding=utf-8 -*-
import re
from collections.abc import Generator

import click

from vulyk.models.user import Group, User


def get_groups_ids() -> list[str]:
    """
    Returns list of groups codes.
    """
    return Group.objects().scalar("id")


def validate_id(ctx: click.Context, param: str, value: str) -> str:
    """
    Allows group code to consist only of letters/numbers/underscore.

    :param ctx: Click context.
    :param param: Name of parameter (`id`).
    :param value: Value of `id` parameter.

    :return: true if value passes.

    :raise click.BadParameter: if wrong `id` has been passed.
    """
    if re.match("^[A-z0-9]+[A-z0-9_]+$", value):
        return value

    raise click.BadParameter("Only letters, numbers, underscores are allowed. Underscore can't go first")


def list_groups() -> Generator[str]:
    """
    Generates list of group representation strings.
    """
    return (repr(g) for g in Group.objects.all())


def new_group(gid: str, description: str) -> None:
    """
    Creates a new group.

    :param gid: Group's symbolic code.
    :param description: Short description (optional).

    :raise click.BadParameter: if wrong `id` has been passed.
    """
    try:
        Group.objects.create(id=gid, description=description)
    except Group.DoesNotExist as e:
        raise click.BadParameter("No group was found with id " + gid) from e


def remove_group(gid: str) -> None:
    """
    Delete existing group.

    :param gid: Group's symbolic code.

    :raise click.BadParameter: if wrong `id` has been passed.
    """
    try:
        Group.objects.get(id=gid).delete()
    except Group.DoesNotExist as e:
        raise click.BadParameter("No group was found with id " + gid) from e


def add_task_type(gid: str, task_type: str) -> None:
    """
    Appends task type to the list of allowed ones of certain group.

    :param gid: Group's symbolic code.
    :param task_type: Task type symbolic code.

    :raise click.BadParameter: if wrong `gid` has been passed.
    """
    try:
        Group.objects.get(id=gid).update(add_to_set__allowed_types=task_type)
    except Group.DoesNotExist as e:
        raise click.BadParameter("No group was found with id " + gid) from e


def remove_task_type(gid: str, task_type: str) -> None:
    """
    Removes task type from the list of allowed types of specified group.

    :param gid: Group's symbolic code.
    :param task_type: Task type symbolic code.

    :raise click.BadParameter: if wrong `gid` has been passed.
    """
    try:
        Group.objects.get(id=gid).update(pull__allowed_types=task_type)
    except Group.DoesNotExist as e:
        raise click.BadParameter("No group was found with id " + gid) from e


def assign_to(username: str, gid: str) -> None:
    """
    Assigns a group to user.

    :param gid: Group's symbolic code.
    :param username: Username of member.

    :raise click.BadParameter: if wrong `gid` or ` username` has been passed.
    """
    try:
        User.objects.get(username=username).update(add_to_set__groups=Group.objects.get(id=gid))
    except User.DoesNotExist as e:
        raise click.BadParameter("No user was found with username " + username) from e
    except Group.DoesNotExist as e:
        raise click.BadParameter("No group was found with id " + gid) from e


def resign(username: str, gid: str) -> None:
    """
    Excludes user from specified group.

    :param gid: Group's symbolic code.
    :param username: Username of member.

    :raise click.BadParameter: if wrong `gid` or ` username` has been passed.
    """
    try:
        User.objects.get(username=username).update(pull__groups=Group.objects.get(id=gid))
    except User.DoesNotExist as e:
        raise click.BadParameter("No user was found with username " + username) from e
    except Group.DoesNotExist as e:
        raise click.BadParameter("No group was found with id " + gid) from e
