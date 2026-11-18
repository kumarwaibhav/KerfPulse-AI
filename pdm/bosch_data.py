"""Pinned Bosch recording integrity and partitioning; no trained model or RUL."""
import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

COMMIT = 'd60581d6a3ab6015dcc5488c3d76112bb8e1bcb1'
MANIFEST_SHA256 = '3dd398ff7187a8b50ca0aba46987c27f2a9d73b8fbbdb663b0163dedfd55f576'
SAMPLING_HZ = 2000
MONTHS = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
PATTERN = re.compile(r'data/(M\d{2})/(OP\d{2})/(good|bad)/(M\d{2})_([A-Za-z]{3})_(20\d{2})_(OP\d{2})_(\d+)\.h5')


@dataclass(frozen=True)
class Recording:
    path: str
    git_blob_sha1: str
    size: int
    machine: str
    operation: str
    label: str
    year: int
    month: int


def catalog(manifest=Path('artifacts/research-data/bosch-tree.json')):
    content = Path(manifest).read_bytes()
    if len(content) > 4*2**20 or hashlib.sha256(content).hexdigest() != MANIFEST_SHA256:
        raise ValueError('Bosch manifest differs from pinned reviewed bytes')
    tree = json.loads(content)
    if tree.get('truncated') or tree.get('sha') != COMMIT:
        raise ValueError('Incomplete or unpinned Bosch manifest')
    result = []
    for entry in tree['tree']:
        path = entry['path']
        if not path.endswith('.h5'):
            continue
        match = PATTERN.fullmatch(path)
        if not match or entry['type'] != 'blob':
            raise ValueError('Unexpected recording path/type')
        machine, operation, label, file_machine, month, year, file_op, _ = match.groups()
        if machine != file_machine or operation != file_op or month not in MONTHS:
            raise ValueError('Contradictory recording lineage')
        if not re.fullmatch('[0-9a-f]{40}', entry['sha']) or type(entry['size']) is not int or entry['size'] <= 0:
            raise ValueError('Invalid source blob contract')
        result.append(Recording(path,entry['sha'],entry['size'],machine,operation,label,int(year),MONTHS[month]))
    if len({r.path for r in result}) != len(result) or len(result) != 1702:
        raise ValueError('Incomplete or repeated recording catalog')
    return tuple(sorted(result,key=lambda r:r.path))


def local_path(root, recording):
    root = Path(root).resolve()
    member = PurePosixPath(recording.path)
    if member.is_absolute() or '..' in member.parts or '\\' in recording.path or ':' in recording.path:
        raise ValueError('Unsafe recording path')
    path = root.joinpath(*member.parts).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Recording escapes dataset root')
    return path


def _verify_open(file, recording):
    git = hashlib.sha1(('blob '+str(recording.size)+'\0').encode())
    digest = hashlib.sha256()
    size = 0
    while chunk := file.read(2**20):
        size += len(chunk)
        if size > recording.size:
            raise ValueError('Recording exceeds publisher size')
        git.update(chunk);digest.update(chunk)
    if size != recording.size or git.hexdigest() != recording.git_blob_sha1:
        raise ValueError('Recording differs from publisher Git blob')
    file.seek(0)
    return digest.hexdigest()


def inspect_recording(root, recording, chunk_rows=65536):
    if type(chunk_rows) is not int or not 1 <= chunk_rows <= 262144:
        raise ValueError('Use bounded chunk size 1..262144')
    import h5py
    import numpy as np
    path = local_path(root,recording)
    with path.open('rb') as raw:
        digest = _verify_open(raw,recording)
        # Read the same verified open file, without loading the corpus eagerly.
        with h5py.File(raw,'r') as handle:
            if not isinstance(handle.get('vibration_data',getlink=True),h5py.HardLink):
                raise ValueError('Local vibration dataset required')
            data = handle['vibration_data']
            if not isinstance(data,h5py.Dataset) or data.ndim != 2 or data.shape[1] != 3 or not 1 <= data.shape[0] <= 20_000_000:
                raise ValueError('Expected bounded N by three acceleration dataset')
            if data.dtype.kind != 'f' or data.is_virtual or data.external:
                raise ValueError('Local floating-point samples required')
            squares = np.zeros(3,dtype=np.float64)
            peaks = np.zeros(3,dtype=np.float64)
            for start in range(0,data.shape[0],chunk_rows):
                values = np.asarray(data[start:start+chunk_rows],dtype=np.float64)
                if not np.isfinite(values).all():
                    raise ValueError('Nonfinite recorded acceleration')
                squares += np.square(values).sum(axis=0)
                peaks = np.maximum(peaks,np.abs(values).max(axis=0))
            rows = data.shape[0]
            rms = np.sqrt(squares/rows)
            if not np.isfinite(rms).all():
                raise ValueError('Overflow in recorded-signal summary')
    return {**asdict(recording),'sha256':digest,'samples':rows,'channels':3,'sampling_hz':SAMPLING_HZ,
            'sampling_basis':'Publisher declaration; not independently calibrated',
            'duration_seconds':rows/SAMPLING_HZ,'units':'Raw acceleration units unqualified',
            'rms_channels':rms.tolist(),'absolute_peak_channels':peaks.tolist(),
            'task':'Recording-level process anomaly; no cutter RUL or failure horizon'}


def partition_recordings(records, *, machine=None, period=None):
    if (machine is None) == (period is None):
        raise ValueError('Choose exactly one machine or period holdout')
    if len({r.path for r in records}) != len(records):
        raise ValueError('Duplicate recording identities')
    if machine is not None:
        train = [r for r in records if r.machine != machine]
        test = [r for r in records if r.machine == machine]
    else:
        if not isinstance(period,tuple) or len(period)!=2 or any(type(v) is not int for v in period) or not 1<=period[1]<=12:
            raise ValueError('Period must be (year, month)')
        train = [r for r in records if (r.year,r.month) < period]
        test = [r for r in records if (r.year,r.month) == period]
    if not train or not test:
        raise ValueError('Requested holdout has no training or test recordings')
    assert not {r.path for r in train} & {r.path for r in test}
    return tuple(train),tuple(test)


def audit(manifest,root,output):
    records = catalog(manifest)
    summaries = [inspect_recording(root,r) for r in records if local_path(root,r).exists()]
    result = {'repository_commit':COMMIT,'manifest_sha256':MANIFEST_SHA256,'catalog_recordings':len(records),
              'catalog_bytes':sum(r.size for r in records),'verified_local_recordings':summaries,
              'missing_local_recordings':len(records)-len(summaries),'task':'Process anomaly only',
              'model_training':'Not run','qualification':'Raw integrity foundation; no plant/model approval'}
    output = Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as file:json.dump(result,file,indent=2,allow_nan=False)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,default=Path('artifacts/research-data/bosch-tree.json'))
    parser.add_argument('--root',type=Path,default=Path('data/research/bosch'))
    parser.add_argument('--output',type=Path,default=Path('artifacts/bosch-integrity-v1/report.json'))
    args = parser.parse_args()
    result = audit(args.manifest,args.root,args.output)
    print(json.dumps({'recordings':result['catalog_recordings'],'verified_local':len(result['verified_local_recordings']),
                      'missing_local':result['missing_local_recordings'],'training':'Not run'}))
