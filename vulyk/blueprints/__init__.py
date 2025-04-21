# -*- coding: utf-8 -*-
from collections.abc import Callable
from typing import Any, ClassVar

import flask


class VulykModule(flask.Blueprint):
    """
    Slightly altered Blueprint to fit our kinky needs.
    """

    config: ClassVar[dict[str, Any]] = {}

    def __init__(
        self,
        name: str,
        import_name: str,
        static_folder: str | None = None,
        static_url_path: str | None = None,
        template_folder: str | None = None,
        url_prefix: str | None = None,
        subdomain: str | None = None,
        url_defaults: dict | None = None,
        root_path: str | None = None,
    ) -> None:
        super().__init__(
            name,
            import_name,
            static_folder,
            static_url_path,
            template_folder,
            url_prefix,
            subdomain,
            url_defaults,
            root_path,
        )

        self._context_fillers: list[Callable[[], dict[str, Any]]] = []
        self.app_context_processor(self._get_module_view_context)

    def configure(self, config: dict) -> None:
        """
        Update blueprint's configuration.

        :param config: Configuration to extend with.
        """
        self.config.update(config)

    def add_context_filler(self, filler: Callable[[], dict[str, Any]]) -> None:
        """
        Adds any function that provides some partial context to be passed
        within module's templates.

        :param filler: A callable.
        """
        self._context_fillers.append(filler)

    def _get_module_view_context(self) -> dict[str, Any]:
        """
        Refills the context with values produced in `self._context_fillers`.

        :return: Dictionary with all context filled.
        """
        result: dict[str, Any] = {}

        for fun in self._context_fillers:
            upd = {f"{self.name}_{k}": v for (k, v) in fun().items()}
            result.update(upd)

        return result
