# -*- coding=utf-8 -*-
from __future__ import unicode_literals
import click
import re

from vulyk.app import db
from vulyk.models.user import Group, User


def get_groups_ids():
    """
    Returns list of groups codes

    :rtype : list[str]
    """
    return Group.objects().scalar('id')


def validate_id(ctx, param, value):
    """
    Allows group code to consist only of letters/numbers/underscore

    :param ctx: Click context
    :param param: Name of parameter (`id`)
    :param value: Value of `id` parameter

    :return: true if value passes

    :raise click.BadParameter:
    """
    if re.match("^[A-z0-9]+[A-z0-9_]+$", value):
        return value
    else:
        raise click.BadParameter('Only letters, numbers, underscores '
                                 'are allowed. Underscore can\'t go first')


def list_groups():
    """
    Generates list of group representation strings

    :rtype : _generator[str]
    """
    return (repr(g) for g in Group.objects.all())


def new_group(gid, description):
    """
    Creates new group

    :param gid: Group's symbolic code
    :type gid: str | unicode
    :param description: Short description (optional)
    :type description: str | unicode

    :raise click.BadParameter: if wrong `id` has been passed
    """
    try:
        Group.objects.create(id=gid, description=description)
    except Group.DoesNotExist:
        raise click.BadParameter('No group was found with id ' + gid)


def remove_group(gid):
    """
    Delete existing group

    :param gid: Group's symbolic code
    :type gid: str | unicode

    :raise click.BadParameter: if wrong `id` has been passed
    """
    try:
        Group.objects.get(id=gid).delete()
    except Group.DoesNotExist:
        raise click.BadParameter('No group was found with id ' + gid)


def add_task_type(gid, task_type):
    """
    Appends task type to the list of allowed ones of certain group

    :param gid: Group's symbolic code
    :type gid: str | unicode
    :param task_type: Task type symbolic code
    :type task_type: str | unicode

    :raise click.BadParameter: if wrong `gid` has been passed
    """
    try:
        Group.objects.get(id=gid).update(add_to_set__allowed_types=task_type)
    except Group.DoesNotExist:
        raise click.BadParameter('No group was found with id ' + gid)


def remove_task_type(gid, task_type):
    """
    Removes task type from the list of allowed types of specified group

    :param gid: Group's symbolic code
    :type gid: str | unicode
    :param task_type: Task type symbolic code
    :type task_type: str | unicode

    :raise click.BadParameter: if wrong `gid` has been passed
    """
    try:
        Group.objects.get(id=gid).update(pull__allowed_types=task_type)
    except Group.DoesNotExist:
        raise click.BadParameter('No group was found with id ' + gid)


def assign_to(username, gid):
    """
    Assigns a group to user

    :param gid: Group's symbolic code
    :type gid: str | unicode
    :param username: Username of member
    :type username: str | unicode

    :raise click.BadParameter: if wrong `gid` or ` username` has been passed
    """
    try:
        User.objects.get(username=username) \
            .update(add_to_set__groups=Group.objects.get(id=gid))
    except User.DoesNotExist:
        raise click.BadParameter('No user was found with username ' + username)
    except Group.DoesNotExist:
        raise click.BadParameter('No group was found with id ' + gid)


def resign(username, gid):
    """
    Excludes user from specified group

    :param gid: Group's symbolic code
    :type gid: str | unicode
    :param username: Username of member
    :type username: str | unicode

    :raise click.BadParameter: if wrong `gid` or ` username` has been passed
    """
    try:
        User.objects.get(username=username) \
            .update(pull__groups=Group.objects.get(id=gid))
    except User.DoesNotExist:
        raise click.BadParameter('No user was found with username ' + username)
    except Group.DoesNotExist:
        raise click.BadParameter('No group was found with id ' + gid)
