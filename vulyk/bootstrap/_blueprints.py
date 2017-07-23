from werkzeug.utils import import_string
from vulyk.blueprints import VulykModule

__all__ = [
    'init_blueprints'
]


def init_blueprints(app):
    enabled_blueprints = app.config.get('ENABLED_BLUEPRINTS', [])
    for blueprint in enabled_blueprints:
        try:
            blueprint_obj = import_string(blueprint['path'])
            if not isinstance(blueprint_obj, VulykModule):
                raise ImportError

            blueprint_obj.configure(blueprint.get('config', {}))

            app.register_blueprint(
                blueprint_obj, url_prefix='/{}'.format(blueprint['url_prefix'])
            )

            app.logger.info('Blueprint {} loaded successfully.'.format(
                blueprint['path'])
            )
        except (ImportError, KeyError) as e:
            app.logger.warning('Cannot load blueprint {}: {}.'.format(
                blueprint.get('path'), e)
            )
