#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def main():
    """Run administrative tasks."""
    web_root = Path(__file__).resolve().parent  # .../techgear_web
    project_root = web_root.parent  # .../FastAPI_T2

    # project_root -> resolves "techgear_web.settings"
    # web_root     -> resolves the "store" app
    for import_root in (project_root, web_root):
        if str(import_root) not in sys.path:
            sys.path.insert(0, str(import_root))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "techgear_web.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()