from pathlib import Path

from dotenv import load_dotenv

from .loader import load_settings
from .settings import Settings

_project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
load_dotenv(_project_root / ".env")
_config = load_settings(_project_root / "settings")
settings = Settings(**_config)
