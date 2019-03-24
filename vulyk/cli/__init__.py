# -*- coding: utf-8 -*-
"""
The package consists of modules hat provide support for different aspects of
project's CLI.
"""

from vulyk.models.user import Group, User


def project_init(allowed_types) -> None:
    """
    The method reassures that a default group is already available,
    otherwise it will be created and passed task types are to be made
    accessible to the group.

    :param allowed_types: Task type names to be allowed to default group.
    :type allowed_types: list[str]
    """
    gr_key = 'default'
    if is_initialized(gr_key) and \
            list(allowed_types) == Group.objects.get(id=gr_key).allowed_types:
        return

    group = Group(
        id=gr_key,
        description='default group',
        allowed_types=allowed_types)

    group.save()

    User.objects.update(add_to_set__groups=group)


def is_initialized(default_key='default') -> bool:
    """
    The method checks whether the default group has been created already or
    has not.

    :param default_key: Default group ID
    :type default_key: str

    :returns: A boolean flag
    :rtype: bool
    """
    return Group.objects(id=default_key).count() == 1
