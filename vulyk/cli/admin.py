# -*- coding: utf-8 -*-
from click import echo

from vulyk.models.user import User


def list_admin():
    admin_users = list(User.objects(admin=True).scalar('email'))
    if admin_users:
        echo('Allowed admins are')
        for email in admin_users:
            echo('- %s' % email)
    else:
        echo('No admins found')

    users = list(User.objects(admin=False).scalar('email'))
    if users:
        echo('Rest of users are:')
        for email in users:
            echo('- %s' % email)


def toggle_admin(email, state):
    users = User.objects.filter(email=email)

    if users.count() == 0:
        echo('User %s does not exists' % email)

    for user in users:
        user.admin = state
        user.save()

    echo('Done')
