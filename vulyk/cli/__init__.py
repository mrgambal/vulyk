# -*- coding: utf-8 -*-
from vulyk.models.user import Group, User


def project_init(allowed_types):
    """
    :type allowed_types: list[basestring]
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


def is_initialized(default_key='default'):
    """
    :rtype: bool
    """
    return Group.objects(id=default_key).count() == 1
