# -*- coding=utf-8 -*-


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
