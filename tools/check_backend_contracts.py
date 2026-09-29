"""Check direct QML Backend calls against the Python API; not a Qt metaobject test."""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
tree = ast.parse((ROOT / 'python/Backend/backend.py').read_text(encoding='utf-8'))
backend = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Backend')
methods = {n.name for n in backend.body if isinstance(n, ast.FunctionDef)}
errors, total = [], 0
for file in sorted((ROOT / 'qml').rglob('*.qml')):
    for method in set(re.findall(r'\bBackend\.(\w+)\s*\(', file.read_text(encoding='utf-8'))):
        total += 1
        if method not in methods:
            errors.append(f'{file.relative_to(ROOT)}: undefined Backend.{method}')
if errors:
    raise SystemExit('\n'.join(errors))
print(f'{total} distinct file/API call pairs checked: all referenced Backend methods exist.')
print('Qt Slot overload resolution is covered only by the real Qt smoke/integration tests.')
