# coding=utf-8
from blinker import signal

__all__ = ["on_batch_done", "on_task_done"]

on_task_done = signal("on_task_done")
on_batch_done = signal("on_batch_done")
