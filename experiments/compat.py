"""ai-economist(2020, numpy 1.21 기준)를 numpy 1.26에서 저장소 수정 없이 import하기 위한 shim.

numpy 1.24에서 제거된 별칭 3곳(layout_from_file.py:212,213 / tutorials/utils/plotting.py:185)만
되살린다. foundation을 import하기 *전에* 이 모듈을 먼저 import해야 한다.
"""

import sys
import types
from pathlib import Path

import numpy as np

# numpy>=1.24에서 제거된 별칭 복원. 저장소가 실제로 쓰는 것은 np.int 뿐이다
# (layout_from_file.py:212,213 / tutorials/utils/plotting.py:185).
np.int = int
np.float = float

# GPUtil은 covid19 시나리오에서만 쓰이는데, 내부적으로 Python 3.12에서 제거된
# distutils를 import한다. 우리는 covid19를 쓰지 않으므로 stub으로 대체해
# components/__init__.py의 일괄 import만 통과시킨다.
if "GPUtil" not in sys.modules:
    try:
        import GPUtil  # noqa: F401
    except Exception:
        _stub = types.ModuleType("GPUtil")
        _stub.getGPUs = lambda: []
        _stub.getAvailable = lambda *a, **k: []
        sys.modules["GPUtil"] = _stub

REPO_ROOT = Path(__file__).resolve().parent.parent / "ai-economist"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FIG_DIR = Path(__file__).resolve().parent / "figures"
RESULT_DIR = Path(__file__).resolve().parent / "results"
FIG_DIR.mkdir(exist_ok=True)
RESULT_DIR.mkdir(exist_ok=True)


def setup_matplotlib():
    """한국어+영어 병기 라벨을 렌더링할 수 있도록 CJK 폰트를 설정한다."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    installed = {f.name for f in font_manager.fontManager.ttflist}
    for candidate in ("Noto Sans CJK KR", "Noto Serif CJK KR", "NanumGothic"):
        if candidate in installed:
            plt.rcParams["font.family"] = candidate
            break
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 120
    plt.rcParams["savefig.dpi"] = 300
    plt.rcParams["savefig.bbox"] = "tight"
    return plt


def save(fig, name):
    """figures/<name>.png 로 저장하고 경로를 출력한다."""
    path = FIG_DIR / f"{name}.png"
    fig.savefig(path)
    print(f"[saved] {path}")
    return path


def write_table(name, text):
    """results/<name>.md 로 마크다운 표를 저장한다."""
    path = RESULT_DIR / f"{name}.md"
    path.write_text(text, encoding="utf-8")
    print(f"[saved] {path}")
    return path
