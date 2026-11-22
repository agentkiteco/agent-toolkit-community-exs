"""Install the bundled native runtime into an app without replacing existing files."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import tempfile


def install(app_dir):
    skill = Path(__file__).resolve().parents[1]
    assets = skill / 'assets'
    sources = {p.name: p.read_text() for p in (assets / 'runtime').iterdir() if p.is_file()}
    for name in ('exness_adapter.py', 'exness_signing.py'):
        text = (assets / name).read_text()
        if name == 'exness_adapter.py':
            before = 'from exness_signing import headers,load_key'
            if text.count(before) != 1:
                raise ValueError('Unexpected SDK signing import; review package integration')
            text = text.replace(before, 'from .exness_signing import headers,load_key')
        sources[name] = text
    for name, text in sources.items():
        if name.endswith('.py'):
            ast.parse(text, filename=name)
    app_dir = Path(app_dir).resolve()
    app_dir.mkdir(parents=True, exist_ok=True)
    target = app_dir / 'signal2copy_runtime'
    if target.exists() or target.is_symlink():
        raise FileExistsError('Runtime already exists; preserve it and merge an update explicitly: ' + str(target))
    hashes = {name: hashlib.sha256(text.encode()).hexdigest() for name, text in sorted(sources.items())}
    with tempfile.TemporaryDirectory(prefix='.signal2copy-runtime-', dir=app_dir) as temporary:
        prepared = Path(temporary) / 'signal2copy_runtime'
        prepared.mkdir()
        for name, text in sources.items():
            (prepared / name).write_text(text, encoding='utf-8')
        (prepared / 'RUNTIME_MANIFEST.json').write_text(json.dumps({
            'skill': 'signal2copy', 'files': hashes,
            'scope': 'Native core; host authentication, storage, admission, controls and UI integration required',
            'live_acceptance': False,
        }, indent=2) + '\n', encoding='utf-8')
        prepared.rename(target)
    return {'installed': str(target), 'files': len(sources) + 1, 'existing_files_replaced': 0,
            'connections_started': 0, 'execution_enabled_by_installer': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app-dir', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(install(args.app_dir)))
