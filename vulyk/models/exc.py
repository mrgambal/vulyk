# -*- coding: utf-8 -*-

__all__ = ['TaskImportError', 'TaskNotFoundError', 'TaskSaveError',
           'TaskPermissionError', 'TaskSkipError', 'TaskValidationError',
           'WorkSessionLookUpError']


class TaskImportError(Exception):
    pass


class TaskSkipError(Exception):
    pass


class TaskSaveError(Exception):
    pass


class TaskValidationError(Exception):
    pass


class TaskPermissionError(Exception):
    pass


class WorkSessionLookUpError(Exception):
    pass


class TaskNotFoundError(Exception):
    pass
