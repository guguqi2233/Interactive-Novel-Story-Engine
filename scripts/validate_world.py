from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.tools.validate_world import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
