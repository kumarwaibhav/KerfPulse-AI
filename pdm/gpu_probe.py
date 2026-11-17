"""Verify real CUDA work on authentic benchmark observations."""
import json
from pathlib import Path
import platform
import subprocess
import time

from pdm.dataset import load, SOURCE_SHA256
from pdm.research_runtime import ResourceGuard, atomic_json, snapshot


def main():
    import numpy as np
    import torch
    import xgboost as xgb
    directory = Path('artifacts/gpu-probe')
    guard = ResourceGuard(directory)
    guard.check(force=True)
    if not torch.cuda.is_available(): raise RuntimeError('CUDA unavailable; no silent CPU fallback permitted')
    torch.manual_seed(17)
    cuts = [c for t in load().values() for c in t.cuts if c.status == 'ok'][:128]
    x = np.array([list(c.current.values()) for c in cuts], dtype=np.float32)
    x = (x-x.mean(0))/(x.std(0)+1e-8)
    y = np.array([min(load()[c.tool_id].failure_cycle-c.cycle,9)-1 for c in cuts])
    tensor = torch.as_tensor(x, device='cuda')
    labels = torch.as_tensor(y, device='cuda', dtype=torch.long)
    net = torch.nn.Linear(x.shape[1], 9).cuda()
    optimizer = torch.optim.Adam(net.parameters(), lr=.001)
    scaler = torch.amp.GradScaler('cuda')
    started = time.perf_counter()
    for _ in range(20):
        optimizer.zero_grad(set_to_none=True)
        with torch.autocast('cuda', dtype=torch.float16):
            loss = torch.nn.functional.cross_entropy(net(tensor), labels)
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
    torch.cuda.synchronize()
    with torch.no_grad():
        fp32 = net(tensor)
        with torch.autocast('cuda', dtype=torch.float16): amp = net(tensor)
    max_difference = (fp32-amp.float()).abs().max().item()
    assert max_difference < .02 and torch.isfinite(loss)
    booster = xgb.train({'device':'cuda','tree_method':'hist','objective':'multi:softprob','num_class':9,'max_depth':2,'seed':17}, xgb.DMatrix(x,label=y), num_boost_round=5)
    config = json.loads(booster.save_config())
    device = config['learner']['generic_param']['device']
    if not device.startswith('cuda'): raise RuntimeError('XGBoost did not use CUDA')
    versions = subprocess.check_output([str(Path(__import__('sys').executable)), '-m','pip','freeze'],text=True)
    directory.mkdir(parents=True,exist_ok=True)
    (directory/'environment.lock.txt').write_text(versions,encoding='utf-8')
    report = {'source_sha256':SOURCE_SHA256,'rows':len(cuts),'purpose':'Runtime verification only; training observations, not efficacy evaluation',
              'python':platform.python_version(),'torch':torch.__version__,'cuda_runtime':torch.version.cuda,'xgboost':xgb.__version__,
              'torch_device':str(tensor.device),'xgboost_device':device,'training_steps':20,'amp_max_logit_difference':max_difference,
              'torch_peak_allocated_bytes':torch.cuda.max_memory_allocated(),'seconds':time.perf_counter()-started,'hardware':snapshot()}
    atomic_json(directory/'report.json',report)
    print(json.dumps(report,indent=2))


if __name__ == '__main__': main()
