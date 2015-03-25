# -*- coding: utf-8 -*-
from vulyk.models.user import Group, User


def project_init(allowed_types):
    """
    :type allowed_types: list[basestring]
    """
    group = Group(
        id="default",
        description="default group",
        allowed_types=allowed_types)

    group.save()

    User.objects.update(add_to_set__groups=group)
