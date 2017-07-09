from blinker import signal

on_task_done = signal('on_task_done')

__all__ = ["on_task_done"]
