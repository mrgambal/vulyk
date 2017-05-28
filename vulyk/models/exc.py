# -*- coding: utf-8 -*-
"""
Module contains all exception classes could be raised during work with
the DB.
"""

__all__ = [
    'TaskImportError',
    'TaskNotFoundError',
    'TaskSaveError',
    'TaskPermissionError',
    'TaskUpdateError',
    'TaskSkipError',
    'TaskValidationError',
    'WorkSessionLookUpError'
]


class TaskImportError(Exception):
    pass


class TaskUpdateError(Exception):
    pass


class TaskSkipError(Exception):
    pass


class TaskSaveError(Exception):
    pass


class TaskValidationError(Exception):
    pass


class TaskPermissionError(Exception):
    pass


class TaskNotFoundError(Exception):
    pass


class WorkSessionLookUpError(Exception):
    pass
