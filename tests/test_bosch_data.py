from dataclasses import replace
from pathlib import Path
import pytest
from pdm.bosch_data import catalog,local_path,partition_recordings,inspect_recording

MANIFEST = Path('artifacts/research-data/bosch-tree.json')


def records():
    if not MANIFEST.exists():pytest.skip('Pinned external manifest not acquired')
    return catalog(MANIFEST)


def test_manifest_and_holdouts():
    values=records()
    assert len(values)==1702 and sum(r.label=='bad' for r in values)==70
    for machine in ('M01','M02','M03'):
        train,test=partition_recordings(values,machine=machine)
        assert {r.machine for r in test}=={machine}
        assert machine not in {r.machine for r in train}
        assert not {r.path for r in train}&{r.path for r in test}
    train,test=partition_recordings(values,period=(2021,8))
    assert all((r.year,r.month)<(2021,8) for r in train)
    assert all((r.year,r.month)==(2021,8) for r in test)
    with pytest.raises(ValueError):partition_recordings(values,machine='M99')
    with pytest.raises(ValueError):partition_recordings(values+values[:1],machine='M01')


def test_wrong_manifest_and_path_escape(tmp_path):
    wrong=tmp_path/'manifest.json';wrong.write_text('{"tree":[]}')
    with pytest.raises(ValueError,match='pinned'):catalog(wrong)
    from pdm.bosch_data import Recording
    malicious=Recording('../outside.h5','0'*40,1,'M01','OP00','good',2019,8)
    with pytest.raises(ValueError,match='Unsafe'):local_path(tmp_path,malicious)


def test_real_sample_integrity_and_chunking(tmp_path):
    pytest.importorskip('h5py')
    values=records()
    item=next(r for r in values if r.path=='data/M01/OP00/good/M01_Aug_2019_OP00_000.h5')
    root=Path('data/research/bosch')
    if not local_path(root,item).exists():pytest.skip('Authentic Bosch sample not acquired')
    summary=inspect_recording(root,item,chunk_rows=8192)
    assert summary['samples']==268288 and summary['channels']==3
    assert summary['sha256']=='2f08bdf2b57c9a61d2f2026458c2f6e4396c14bcfc4bd713dee6002f67517df0'
    assert summary['units']=='Raw acceleration units unqualified'
    with pytest.raises(ValueError,match='publisher'):
        inspect_recording(root,replace(item,git_blob_sha1='0'*40))
    # Integrity failure fixture, never presented as measured sensor data.
    copy=local_path(tmp_path,item);copy.parent.mkdir(parents=True);copy.write_bytes(b'invalid HDF5')
    with pytest.raises(ValueError,match='publisher'):inspect_recording(tmp_path,item)
