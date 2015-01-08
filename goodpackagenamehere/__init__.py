__version__ = '1.0.0'

try:
    from .app import app
except ImportError:
    # To make setup.py work
    pass
