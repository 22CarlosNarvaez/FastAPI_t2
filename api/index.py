import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
web_root = project_root / "techgear_web"

for p in (str(web_root), str(web_root / "techgear_web")):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from wsgi import application

