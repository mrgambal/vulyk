# -*- coding: utf-8 -*-
"""
The package consists of modules hat provide support for different aspects of
project's CLI.
"""

from collections.abc import Iterable

from vulyk.models.user import Group, User

__all__ = ["is_initialized", "project_init"]


def project_init(allowed_types: Iterable[str]) -> None:
    """
    The method reassures that a default group is already available,
    otherwise it will be created and passed task types are to be made
    accessible to the group.

    :param allowed_types: Task type names to be allowed to default group.
    """
    gr_key = "default"
    group: Group

    try:
        group = Group.objects.get(id=gr_key)

        if set(allowed_types) == set(group.allowed_types):
            return

        group.allowed_types = allowed_types
        group.save()
    except Group.DoesNotExist:
        group = Group(id=gr_key, description="default group", allowed_types=allowed_types)
        group.save()

    User.objects.update(add_to_set__groups=group)


def is_initialized(default_key: str = "default") -> bool:
    """
    The method checks whether the default group has been created already or
    has not.
    :param default_key: Default group ID
    :returns: A boolean flag
    """
    return Group.objects(id=default_key).count() == 1
