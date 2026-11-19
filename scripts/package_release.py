"""Packages source, omitting local secrets and databases.
Does NOT claim full Flask/browser test verification.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
root=Path(__file__).resolve().parent.parent
out=root.parent/'CampusVote_UI_Source.zip'
skip={'__pycache__','.pytest_cache','.venv','.git','node_modules'}
with ZipFile(out,'w',ZIP_DEFLATED,compresslevel=8) as archive:
    for path in sorted(root.rglob('*')):
        if not path.is_file() or any(part in skip for part in path.relative_to(root).parts):continue
        if path.name in ('.secret_key','.env') or path.suffix in ('.sqlite3','.db','.pyc'):continue
        archive.write(path,'CampusVote/'+str(path.relative_to(root)).replace('\\','/'))
with ZipFile(out) as archive:
    if archive.testzip():raise RuntimeError('ZIP failed integrity validation')
    assert all(k in archive.namelist() for k in ('CampusVote/run.py','CampusVote/requirements.txt','CampusVote/campusvote/static/css/main.css','CampusVote/database/schema.sql'))
print(out)
