"""
WSGI config for techgear_web project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
import sys
from pathlib import Path

web_root = Path(__file__).resolve().parent
project_root = web_root.parent

for import_root in (project_root, web_root):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from django.core.wsgi import get_wsgi_application  # noqa: E402

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

application = get_wsgi_application()