import importlib.util, os
from pathlib import Path

# enhanced.py lives in the hyphenated 'radar-engine' dir; load it by path.
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "enhanced_under_test", ROOT / "radar-engine" / "fetchers" / "enhanced.py")


def _fetcher_class():
    # base.py is a sibling relative import; load it first under the expected package name.
    import sys, types
    pkg = types.ModuleType("ruut"); pkg.__path__ = []
    sys.modules.setdefault("ruut", pkg)
    base_spec = importlib.util.spec_from_file_location(
        "ruut.base", ROOT / "radar-engine" / "core" / "base.py")
    base_mod = importlib.util.module_from_spec(base_spec); base_spec.loader.exec_module(base_mod)
    sys.modules["ruut.base"] = base_mod
    src = (ROOT / "radar-engine" / "fetchers" / "enhanced.py").read_text()
    src = src.replace("from ..core.base import", "from ruut.base import")
    ns = {}
    exec(compile(src, "enhanced.py", "exec"), ns)
    return ns["EnhancedYAMLFetcher"]


def test_max_items_reads_config_with_default():
    Fetcher = _fetcher_class()
    f = Fetcher({"id": "x", "type": "json_api", "max_items": 5}, http_client=None)
    assert f._max_items(20) == 5
    g = Fetcher({"id": "y", "type": "json_api"}, http_client=None)
    assert g._max_items(20) == 20
