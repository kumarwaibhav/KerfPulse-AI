import pytest
import hashlib
import io
from types import SimpleNamespace
from pdm import research_data
from pdm.research_data import safe_member, download_verified


@pytest.mark.parametrize('path',['../escape','/absolute','C:/escape','folder/../../x','folder\\..\\x'])
def test_archive_traversal_rejected(path):
    with pytest.raises(ValueError): safe_member(path)


def test_safe_member_and_download_requirements(tmp_path):
    assert str(safe_member('machine/cut.h5')) == 'machine/cut.h5'
    with pytest.raises(ValueError): download_verified('http://example.org',tmp_path/'x','0'*64,1)
    with pytest.raises(ValueError): download_verified('https://example.org',tmp_path/'x','bad',1)


def test_bad_download_preserves_original_and_removes_temporary(tmp_path,monkeypatch):
    from pdm.dataset import source_path
    measured_bytes=source_path().read_bytes()[:100]
    class Response(io.BytesIO): url='https://example.org/pinned'
    monkeypatch.setattr(research_data,'urlopen',lambda *a,**k: Response(measured_bytes))
    monkeypatch.setattr(research_data.shutil,'disk_usage',lambda _:SimpleNamespace(free=30*2**30))
    path=tmp_path/'capture'
    path.write_bytes(measured_bytes)
    with pytest.raises(ValueError,match='integrity'):
        download_verified('https://example.org/pinned',path,'0'*64,len(measured_bytes))
    assert path.read_bytes()==measured_bytes
    assert list(tmp_path.iterdir())==[path]
    download_verified('https://example.org/pinned',path,hashlib.sha256(measured_bytes).hexdigest(),len(measured_bytes))
    assert path.read_bytes()==measured_bytes
