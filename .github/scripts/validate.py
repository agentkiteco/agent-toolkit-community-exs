from catalog import ROOT, collect, read_entry
entries=collect()
for path in (ROOT/'.github/templates').glob('*/SKILL.md'):
    read_entry(path,'skill')
print(f'Validated {len(entries)} catalog entries and skill templates.')
