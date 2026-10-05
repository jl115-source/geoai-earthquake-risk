"""Frozen-checkpoint inference preflight only; never fits a readout or PCA.

Executes checksum-pinned official SatMAE source (CC BY-NC 4.0), retained locally
with its licence. Compatibility changes are explicit and do not alter weights.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
import types
from urllib.request import urlopen

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / 'configs/geoai_experiment_1f.json'
RAW = ROOT / 'data/raw/geoai_1f'
OUTPUT = ROOT / 'data/processed/geoai_1f/satmae_preflight'


def file_hash(path, algorithm='sha256'):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, algorithm).hexdigest()


def normalize(reflectance, config):
    if reflectance.shape != (10, 96, 96) or not np.isfinite(reflectance).all():
        raise ValueError('Complete finite 10x96x96 reflectance required')
    mean = np.asarray(config['mean'])[:, None, None]
    std = np.asarray(config['std'])[:, None, None]
    dn = reflectance.astype(np.float64) * 10000
    quantized = np.clip(255 * (dn - (mean - 2 * std)) / (4 * std), 0, 255).astype(np.uint8)
    return quantized.astype(np.float32) / 255


def verify_sources(config, fetch=False):
    source = RAW / 'satmae/source'
    for name, expected in config['source_sha256'].items():
        path = source / name
        if not path.exists() and fetch:
            path.parent.mkdir(parents=True, exist_ok=True)
            url = f"https://raw.githubusercontent.com/sustainlab-group/SatMAE/{config['source_revision']}/{name}"
            with urlopen(url, timeout=90) as response:
                path.write_bytes(response.read())
        if not path.exists() or file_hash(path) != expected:
            raise ValueError(f'Missing or changed official source: {path}')
    return source


def load_frozen(config, source, checkpoint):
    import torch
    import timm
    if not torch.__version__.startswith('2.6.0') or timm.__version__ != '0.9.16':
        raise ValueError('Use the pinned requirements-eo.txt runtime')
    if checkpoint.stat().st_size != config['bytes'] or file_hash(checkpoint, 'md5') != config['md5']:
        raise ValueError('Official checkpoint length/MD5 mismatch')
    # Original checkpoint includes argparse.Namespace training metadata. This is
    # the only additional safe global; never opt out of weights-only loading.
    with torch.serialization.safe_globals([argparse.Namespace]):
        archive = torch.load(checkpoint, map_location='cpu', mmap=True, weights_only=True)
    state = archive['model']
    sys.path.insert(0, str(source))
    code = (source / 'models_mae_group_channels.py').read_text()
    if code.count(', qk_scale=None') != 2:
        raise ValueError('Unexpected upstream compatibility surface')
    # timm 0.9 uses the same default head_dim**-0.5 scale without qk_scale=None.
    code = code.replace(', qk_scale=None', '')
    module = types.ModuleType('satmae_pinned')
    exec(compile(code, str(source / 'models_mae_group_channels.py'), 'exec'), module.__dict__)
    # Meta construction avoids allocating random weights/decoder optimizer state.
    # STRICT full-state loading below restores every parameter, including fixed
    # positional/channel encodings; no initial/random tensor can enter inference.
    module.MaskedAutoencoderGroupChannelViT.initialize_weights = lambda self: None
    with torch.device('meta'):
        model = module.mae_vit_large_patch16(img_size=96, patch_size=8, in_chans=10,
                                           channel_groups=((0, 1, 2, 6), (3, 4, 5, 7), (8, 9)))
    model.load_state_dict(state, strict=True, assign=True)
    if any(p.is_meta for p in model.parameters()):
        raise ValueError('Unrestored meta parameter')
    model.eval().requires_grad_(False)
    for block in model.blocks:
        block.attn.fused_attn = False

    def identity_mask(self, x, mask_ratio):
        if mask_ratio != 0:
            raise ValueError('Frozen preflight permits only identity/no mask')
        n, length, _ = x.shape
        return x, torch.zeros(n, length, device=x.device), torch.arange(length, device=x.device).expand(n, -1)

    model.random_masking = types.MethodType(identity_mask, model)
    encoder_keys = [k for k in state if not k.startswith('decoder_') and k != 'mask_token']
    return model, {'full_state_tensors_strictly_loaded': len(state), 'encoder_tensors': len(encoder_keys),
                   'encoder_parameters': sum(state[k].numel() for k in encoder_keys),
                   'checkpoint_sha256': file_hash(checkpoint),
                   'compatibility': ['remove obsolete qk_scale=None', 'skip random initialization; strict assign every tensor',
                                     'identity no-mask branch', 'disable fused attention on CPU'],
                   'decoder_executed': False, 'optimizer_used': False}


def embedding(model, values):
    import torch
    with torch.inference_mode():
        tokens, _, _ = model.forward_encoder(torch.from_numpy(values[None]), mask_ratio=0)
        if tokens.shape != (1, 433, 1024):
            raise ValueError(f'Unexpected tokens: {tokens.shape}')
        result = tokens[:, 1:].mean(dim=1).numpy()[0].copy()
    if not np.isfinite(result).all():
        raise ValueError('Nonfinite embedding')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-name', default='run_a')
    parser.add_argument('--fetch-source', action='store_true')
    parser.add_argument('--compare', type=Path, help='Prior embeddings.npy from a separate process')
    args = parser.parse_args()
    if not args.run_name.replace('_', '').isalnum():
        raise ValueError('Simple alphanumeric run name required')
    import torch
    import timm
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    config = json.loads(CONFIG.read_text())['encoder']
    source = verify_sources(config, args.fetch_source)
    model, evidence = load_frozen(config, source, RAW / 'satmae/pretrain-vit-large-e199.pth')
    frame = pd.read_parquet(ROOT / 'data/processed/geoai_1f/feature_manifest.parquet',
                            columns=['building_id', 'city', 'location_key', 'eligible'])
    rows = frame.loc[frame.eligible].sort_values('building_id').groupby('city', sort=True).head(1).sort_values('city')
    vectors, elapsed, chip_hashes = [], [], {}
    for row in rows.itertuples():
        path = RAW / 'locations' / row.location_key / 'reflectance.npz'
        report = json.loads((path.parent / 'audit.json').read_text())
        if report['status'] != 'complete_clear_composite' or file_hash(path) != report['chip_sha256']:
            raise ValueError('Input chip checksum mismatch')
        chip_hashes[row.location_key] = file_hash(path)
        with np.load(path) as chip:
            if not (chip['clear_observation_count'] > 0).all():
                raise ValueError('Unobserved pixels cannot enter the encoder')
            values = normalize(chip['reflectance'], config)
        start = time.perf_counter()
        torch.manual_seed(1)
        first = embedding(model, values)
        torch.manual_seed(777)
        second = embedding(model, values)
        if not np.array_equal(first, second):
            raise ValueError('Repeat inference changed with RNG seed')
        vectors.append(first)
        elapsed.append((time.perf_counter() - start) / 2)
        print(f'{row.city}: finite 1024-D, repeated inference byte-identical', flush=True)
    matrix = np.stack(vectors)
    if np.unique(matrix, axis=0).shape[0] != len(rows):
        raise ValueError('Distinct city chips unexpectedly produced identical vectors')
    cross_process = None
    if args.compare:
        prior = np.load(args.compare)
        cross_process = bool(np.array_equal(matrix, prior))
        if not cross_process:
            raise ValueError('Separate-process embedding determinism failed')
    out = OUTPUT / args.run_name
    out.mkdir(parents=True, exist_ok=True)
    np.save(out / 'embeddings.npy', matrix)
    rows.to_csv(out / 'rows.csv', index=False)
    evidence.update(rows=len(rows), dimensions=1024, dtype=str(matrix.dtype), device='cpu',
                    torch=torch.__version__, timm=timm.__version__, numpy=np.__version__, python=platform.python_version(),
                    platform=platform.platform(), cpu_threads=4, repeated_identical=True, cross_process_identical=cross_process,
                    mean_seconds_per_chip=float(np.mean(elapsed)), chip_sha256=chip_hashes,
                    embeddings_sha256=file_hash(out / 'embeddings.npy'), rows_sha256=file_hash(out / 'rows.csv'),
                    encoder_config_sha256=hashlib.sha256(json.dumps({k:v for k,v in config.items() if k != 'status'}, sort_keys=True).encode()).hexdigest(),
                    source_sha256=config['source_sha256'], model_fitted=False, pca_fitted=False,
                    implementation_sha256=file_hash(Path(__file__)),
                    scope='one deterministic eligible chip per city; not full-cohort extraction or cross-hardware reproducibility')
    (out / 'report.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps({k:v for k,v in evidence.items() if k != 'chip_sha256'}, indent=2))


if __name__ == '__main__':
    main()
