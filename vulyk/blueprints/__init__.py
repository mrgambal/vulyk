# -*- coding: utf-8 -*-
from types import LambdaType

import flask


class VulykModule(flask.Blueprint):
    """
    Slightly altered Blueprint to fit our kinky needs.
    """
    config = {}

    def __init__(self, name, import_name, static_folder=None,
                 static_url_path=None, template_folder=None, url_prefix=None,
                 subdomain=None, url_defaults=None, root_path=None):
        super().__init__(name, import_name, static_folder, static_url_path,
                         template_folder, url_prefix, subdomain, url_defaults,
                         root_path)

        self._context_fillers = []  # type: list[LambdaType[None -> dict]]
        self.app_context_processor(self._get_module_view_context)

    def configure(self, config: dict) -> None:
        """
        Update blueprint's configuration.

        :param config: Configuration to extend with.
        :type config: dict
        """
        self.config.update(config)

    def add_context_filler(self, filler: LambdaType) -> None:
        """
        Adds any function that provides some partial context to be passed
        within module's templates.

        :param filler: A callable
        :type filler: LambdaType[None -> dict]
        """
        self._context_fillers.append(filler)

    def _get_module_view_context(self) -> dict:
        """
        Refills the context with values produced in `self._context_fillers`.

        :return: Dictionary with all context filled.
        :rtype: dict
        """
        result = {}

        for fun in self._context_fillers:
            upd = {'{}_{}'.format(self.name, k): v for (k, v) in fun().items()}
            result.update(upd)

        return result
