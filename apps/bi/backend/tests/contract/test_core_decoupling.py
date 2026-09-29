import ast
from pathlib import Path


CORE_ROOT = Path(__file__).parents[2] / "src" / "analytics_core"


def test_analytics_core_does_not_import_bi() -> None:
    violations: list[str] = []
    for path in CORE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imported = [node.module or ""]
            else:
                continue
            if any(name == "bi" or name.startswith("bi.") for name in imported):
                violations.append(f"{path}: {imported}")

    assert not violations, "analytics_core must not import bi:\n" + "\n".join(violations)


def test_pandas_is_confined_to_pandas_impl() -> None:
    source_root = Path(__file__).parents[2] / "src"
    violations = []
    for path in source_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        normalized = str(path).replace("\\", "/")
        if ("import pandas" in text or "from pandas" in text) and "/engine/pandas_impl/" not in normalized:
            violations.append(str(path))
    assert not violations, "pandas must stay in pandas_impl:\n" + "\n".join(violations)
