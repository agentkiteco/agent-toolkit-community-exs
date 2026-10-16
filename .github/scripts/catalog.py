"""Validate and collect the canonical content; imported by build and CI."""
from pathlib import Path
import re
import yaml

ROOT = Path(__file__).resolve().parents[2]
REPO = 'agentkiteco/agent-toolkit-community-exs'

def read_entry(path, kind, root=ROOT):
    text = path.read_text(encoding='utf-8')
    parts = text.split('---', 2)
    if len(parts) != 3 or parts[0].strip():
        raise ValueError(f'{path}: missing YAML frontmatter')
    meta = yaml.safe_load(parts[1])
    if not isinstance(meta, dict):
        raise ValueError(f'{path}: metadata must be a mapping')
    name, description = meta.get('name'), meta.get('description')
    if not isinstance(name, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) or len(name)>64:
        raise ValueError(f'{path}: invalid name')
    if not isinstance(description, str) or not description.strip() or len(description)>1024:
        raise ValueError(f'{path}: description must contain 1–1024 characters')
    expected = path.parent.name if kind=='skill' else path.stem
    if name != expected:
        raise ValueError(f'{path}: name must match {expected}')
    body = parts[2].strip()
    if not body:
        raise ValueError(f'{path}: empty body')
    if kind=='skill':
        for target in re.findall(r'\]\(([^)]+)\)', body):
            if '://' in target or target.startswith('#'):
                continue
            target = target.split('#')[0]
            resolved = (path.parent/target).resolve()
            if not resolved.is_relative_to(path.parent.resolve()) or not resolved.is_file():
                raise ValueError(f'{path}: missing or non-local resource {target}')
    rel = path.relative_to(root).as_posix()
    return dict(id=f'{kind}/{name}',name=name,description=description.strip(),kind=kind,path=rel,
                source=f'https://github.com/{REPO}/blob/main/{rel}',body=body)

def collect(root=ROOT):
    entries=[]
    for folder, pattern, kind in [('skills','*/SKILL.md','skill'),('prompts','*.md','prompt'),('instructions','*.md','instruction')]:
        entries.extend(read_entry(p,kind,root) for p in sorted((root/folder).glob(pattern)))
    if not entries:
        raise ValueError('Catalog must not be empty')
    return entries
