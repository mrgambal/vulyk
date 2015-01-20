# -*- coding=utf-8 -*-
import click
import re

from ..app import db
from ..models import Group, User


def get_groups_ids():
    return Group.objects().scalar("id")


def validate_id(ctx, param, value):
    if re.match("^[A-z0-9]+[A-z0-9_]+$", value):
        return value
    else:
        raise click.BadParameter("Only letters, numbers, underscores "
                                 "are allowed. Underscore can't go first")


def new_group(gid, description):
    Group.objects.create(id=gid, description=description)


def remove_group(gid):
    Group.objects(id=gid).delete()


def assign_to(username, gid):
    try:
        User.objects(username=username)\
            .update(set__group=Group.objects(id=gid))
    except User.DoesNotExist:
        raise click.BadParameter("No user was found with username " + username)
    except Group.DoesNotExist:
        raise click.BadParameter("No group was found with id " + gid)
