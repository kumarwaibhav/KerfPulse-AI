"""Stable experiment identity, including preprocessing, partitions and environment."""
import hashlib
from importlib import metadata
import platform
import os
import subprocess
from pathlib import Path


def digest(value):
    import json
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def fingerprint(rows, groups, folds, methods):
    root=Path(__file__).parent
    files=('dataset.py','train.py','validation.py','inference.py','research_runtime.py','gpu_benchmark.py','experiment_provenance.py')
    versions={}
    for name in ('numpy','scipy','scikit-learn','torch','xgboost','joblib','threadpoolctl'):
        try: versions[name]=metadata.version(name)
        except metadata.PackageNotFoundError: versions[name]=None
    from pdm.gpu_benchmark import names_for
    observations=[{'tool':c.tool_id,'cycle':c.cycle,'group':groups[c.tool_id],'remaining':remaining,
                   'context':c.context,'current':c.current,'vibration':c.vibration} for c,remaining in rows]
    try:
        gpu_identity=subprocess.check_output(['nvidia-smi','--query-gpu=name,driver_version','--format=csv,noheader'],text=True,timeout=5).strip()
    except (OSError,subprocess.SubprocessError):gpu_identity=None
    return {'schema_version':2,'python':platform.python_version(),'platform':platform.platform(),'gpu_driver_identity':gpu_identity,
            'runtime_environment':{key:os.getenv(key) for key in ('CUDA_VISIBLE_DEVICES','CUBLAS_WORKSPACE_CONFIG','OMP_NUM_THREADS','MKL_NUM_THREADS')},
            'packages':versions,'code':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files},
            'observations_sha256':digest(observations),'partitions_sha256':digest(folds),
            'features':{method:names_for(rows[0][0],method) for method in methods}}
