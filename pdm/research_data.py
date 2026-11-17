"""Small official source manifests and bounded, verified HTTPS acquisition."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tempfile
from urllib.request import Request, urlopen
from urllib.parse import urlparse

from pdm.dataset import source_path, verify_source, SOURCE_SHA256
from pdm.research_runtime import atomic_json


def safe_member(name):
    path = PurePosixPath(name.replace('\\','/'))
    if path.is_absolute() or '..' in path.parts or any(':' in part for part in path.parts):
        raise ValueError('Unsafe archive member')
    return path


def download_verified(url, destination, sha256, size):
    if urlparse(url).scheme != 'https': raise ValueError('HTTPS required')
    if size <= 0 or len(sha256)!=64: raise ValueError('Expected size and SHA-256 required')
    path = Path(destination)
    path.parent.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(path.parent).free < size+15*2**30: raise ValueError('Insufficient disk reserve')
    temporary = None
    try:
        with urlopen(Request(url,headers={'User-Agent':'KerfPulseResearch/1'}),timeout=45) as response:
            if urlparse(response.url).scheme != 'https': raise ValueError('Insecure redirect')
            with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as file:
                temporary = Path(file.name); digest = hashlib.sha256(); received = 0
                while chunk := response.read(2**20):
                    received += len(chunk)
                    if received > size: raise ValueError('Source exceeds expected size')
                    digest.update(chunk); file.write(chunk)
        if received != size or digest.hexdigest()!=sha256: raise ValueError('Source integrity mismatch')
        temporary.replace(path)
        return path
    finally:
        if temporary is not None: temporary.unlink(missing_ok=True)


def main():
    directory = Path('artifacts/research-data')
    verify_source(source_path().read_bytes())
    registry = {'haas':{'version':'10.6084/m9.figshare.28589216.v1','sha256':SOURCE_SHA256,'license':'CC BY 4.0','verified':'local CSV bytes'},
                'stiehl':{'url':'https://data.mendeley.com/datasets/zpxs87bjt8/3','license':'CC BY 4.0','task':'flank wear, cast iron, three machines',
                          'status':'Landing metadata reviewed; archive bytes/labels not yet acquired or verified'},
                'bosch':{'repository':'https://github.com/boschresearch/CNC_Machining','license':'CC BY 4.0 data; BSD-3 code','task':'process anomaly; not cutter-damage horizon'}}
    url = 'https://api.github.com/repos/boschresearch/CNC_Machining/git/trees/main?recursive=1'
    with urlopen(Request(url,headers={'User-Agent':'KerfPulseResearch/1'}),timeout=30) as response:
        content = response.read(4*2**20+1)
    if len(content)>4*2**20: raise ValueError('Manifest exceeds size limit')
    tree = json.loads(content)
    if tree.get('truncated'): raise ValueError('Incomplete Bosch source tree')
    files = [entry for entry in tree['tree'] if entry['path'].startswith('data/') and entry['path'].endswith('.h5')]
    for file in files: safe_member(file['path'])
    directory.mkdir(parents=True,exist_ok=True)
    (directory/'bosch-tree.json').write_bytes(content)
    registry['bosch'].update(tree_sha=tree['sha'],manifest_sha256=hashlib.sha256(content).hexdigest(),files=len(files),
                             indexed_bytes=sum(f.get('size',0) for f in files),verified='Official manifest only; no sensor HDF5 bytes verified')
    atomic_json(directory/'registry.json',registry)
    print(json.dumps(registry,indent=2))


if __name__=='__main__': main()
