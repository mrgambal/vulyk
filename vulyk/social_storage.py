"""MongoEngine storage integration for social-auth.

The upstream ``social-storage-mongoengine`` package still implements nonce
creation with ``QuerySet.get_or_create()``. MongoEngine removed that deprecated
method, so current OAuth flows fail when ``social-core`` calls
``storage.nonce.use()`` while creating a provider redirect state.

This module keeps the upstream storage models but replaces nonce creation with
an atomic MongoEngine ``modify(upsert=True)`` operation. The nonce model also
defines a unique compound index for ``server_url``, ``timestamp``, and ``salt``
so concurrent requests cannot create duplicate state records. Keep this
workaround in Vulyk-owned code rather than editing installed packages.
"""

from typing import ClassVar

from mongoengine import ReferenceField
from social_core.utils import module_member, setting_name
from social_flask_mongoengine.models import FlaskStorage as BaseFlaskStorage
from social_mongoengine.storage import (
    MongoengineAssociationMixin,
    MongoengineCodeMixin,
    MongoengineNonceMixin,
    MongoenginePartialMixin,
    MongoengineUserMixin,
)


class MongoengineNonceMixinWithAtomicUse(MongoengineNonceMixin):
    """Create nonces atomically and report whether this call inserted one."""

    @classmethod
    def use(cls, server_url, timestamp, salt):
        return (
            cls.objects(server_url=server_url, timestamp=timestamp, salt=salt).modify(
                set__salt=salt, upsert=True, new=False
            )
            is None
        )


class FlaskStorage(BaseFlaskStorage):
    """Flask social-auth storage with MongoEngine-compatible nonce handling."""


def init_social(app, db):
    """Initialize social-auth MongoEngine models on the application."""
    user_model_class = module_member(app.config[setting_name("USER_MODEL")])

    class UserSocialAuth(db.Document, MongoengineUserMixin):
        user = ReferenceField(user_model_class)

        @classmethod
        def user_model(cls):
            return user_model_class

    class Nonce(db.Document, MongoengineNonceMixinWithAtomicUse):
        meta: ClassVar[dict[str, object]] = {
            "indexes": [{"fields": ["server_url", "timestamp", "salt"], "unique": True}]
        }

    class Association(db.Document, MongoengineAssociationMixin):
        pass

    class Code(db.Document, MongoengineCodeMixin):
        pass

    class Partial(db.Document, MongoenginePartialMixin):
        pass

    FlaskStorage.user = UserSocialAuth
    FlaskStorage.nonce = Nonce
    FlaskStorage.association = Association
    FlaskStorage.code = Code
    FlaskStorage.partial = Partial
