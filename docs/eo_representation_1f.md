# Frozen EO encoder research

No weights downloaded; no inference/training performed. Metadata and source links below define the design; weights and inference remain a 2A preflight.

## Primary: original multispectral SatMAE ViT-Large

Select **ViT-Large**, the multispectral checkpoint available from the official deposit, `pretrain-vit-large-e199.pth`, Zenodo record7325339, published2022-11-17, 3,949,597,273bytes, MD5 `436bcd815194afdae38f3e023c74e9cd`. Archive includes optimizer; inference uses encoder only. Do not use the separate supervised-finetuned checkpoint. Weight deposit license: **CC BY4.0**. [Record](https://zenodo.org/records/7325339), [API](https://zenodo.org/api/records/7325339).

Pin source to pre-event commit `117135b3354fa70a81df453be7f34e3da8b36032` (2023-02-01). **Code license CC BY-NC4.0**, distinct from weights/data rights. [License](https://github.com/sustainlab-group/SatMAE/blob/117135b3354fa70a81df453be7f34e3da8b36032/LICENSE).

Paper describes global fMoW-location Sentinel-2 surface-reflectance90-day composites,712,874training images. Exact pretraining overlap with Turkish cities was not checked. Pre-event checkpoint excludes February2023 damage-event learning, but does not prove unseen geography. [Paper](https://arxiv.org/html/2207.08051).

### Project input contract

- One composite per building; locked pre-event window and QA. Sensing time before cutoff; no random augmentations or silent cloudy/empty-pixel zero fill. Primary strict eligibility requires complete composite support.
- North-up96×96grid at10m in local UTM, centred on survey coordinate:960×960m context. Bilinear reflectance resampling; nearest QA. Upsampling20mbands does not increase physical detail. Fixed support intentionally replaces upstream variable-size resize/centre-crop evaluation: document as project adaptation.
- Band order `B02,B03,B04,B05,B06,B07,B08,B8A,B11,B12`; groups `[[0,1,2,6],[3,4,5,7],[8,9]]`.
- Apply source scale/offset to get reflectance, then multiply10000. Do not feed additive-offset raw DN or double-scale.
- Normalization is **not z-score**: `uint8(clip(255*(DN-(mean-2*std))/(4*std),0,255))/255`. Use pinned code constants; paper table differs in some entries. Means `[1184.3824625,1120.77120066,1136.26026392,1263.73947144,1645.40315151,1846.87040806,1762.59530783,1972.62420416,1732.16362238,1247.91870117]`. Stds `[650.2842772,712.12507725,965.23119807,948.9819932,1108.06650639,1258.36394548,1233.1492281,1364.38688993,1310.36996126,1087.6020813]`.

[Pinned preprocessing](https://github.com/sustainlab-group/SatMAE/blob/117135b3354fa70a81df453be7f34e3da8b36032/util/datasets.py).

### Encoder contract

Instantiate `models_mae_group_channels.mae_vit_large_patch16(img_size=96,patch_size=8,in_chans=10,channel_groups=((0,1,2,6),(3,4,5,7),(8,9)))`. Factory alias sayspatch16 but explicit8sets actual patches. Width1024,depth24,heads16;432non-CLS tokens (3×12×12),80m patch support. Strict encoder-key/shape check; omit decoder,optimizer,head without accepting missing/random encoder weights. Eval,requires_gradfalse,inference mode.

Upstream mask_ratio0 still random-sorts tokens. Use documented identity no-mask branch or equivalent explicit patch/channel/position→CLS→blocks→final-norm path. Mean pool432non-CLS final-normalized tokens into **1024-D** vector. Pooling is project choice. Record checkpoint checksum,code revision,preprocessing manifest hash,dtype/backend. No task-specific encoder adaptation. [Pinned model](https://github.com/sustainlab-group/SatMAE/blob/117135b3354fa70a81df453be7f34e3da8b36032/models_mae_group_channels.py).

One frozen extraction for559short sequences is bounded, but memory/runtime not measured. Checksum and deterministic smoke test are required before full extraction. This is executable design, not an inference-tested implementation.

## Secondary candidate: Prithvi EO1.0 100M — deferred sensitivity

Official revision `f3a9ea7a1723621b0aeceb4de993093704d712c5`; `Prithvi_100M.pt`,453,671,052bytes,LFS SHA256 `7fac0c8a8693198e32a055e0c5a967f8b005f382182b63df1b29fdcd5c880731`; card declaresApache2.0. CONUS HLSV2L30 pretraining at30m,6bands blue/green/red/narrowNIR/SWIR1/SWIR2; HLSL30 B02/B03/B04/B05/B06/B07. S30 equivalents B02/B03/B04/B8A/B11/B12 require explicit mapping. One-frame inference supported. [Official card/files](https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-1.0-100M/tree/f3a9ea7a1723621b0aeceb4de993093704d712c5), [checksum API](https://huggingface.co/api/models/ibm-nasa-geospatial/Prithvi-EO-1.0-100M?blobs=true).

224×224pixels,patch16,width768,12layers; one-frame196tokens. Context6.72km differs from primary960m: not an isolated architecture comparison. DN normalization means `[775.2290211032589,1080.992780391705,1228.5855250417867,2497.2022620507532,2204.2139147975554,1610.8324823273745]`; stds `[1281.526139861424,1270.0297974547493,1399.4802505642526,1368.3446143747644,1291.6764008585435,1154.505683480695]`. Divide both by10000 for reflectance. [Config](https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-1.0-100M/blob/f3a9ea7a1723621b0aeceb4de993093704d712c5/config.yaml).

Candidate extraction `forward_features(x)[-1][:,1:,:].mean(1)`, temporal/locationencodings disabled. Current source is a later refactor: check checkpoint remapping/strict encoder coverage before running. [Implementation](https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-1.0-100M/blob/f3a9ea7a1723621b0aeceb4de993093704d712c5/prithvi_mae.py).

**ReleasedAugust2023**, not historically available before earthquake. CONUS geography avoids direct Turkish event pixels, but exact pretraining-image endpoints not established here. Exclude from strict primary chronology allowlist; retrospective sensitivity needs protocol amendment/HLS audit. Choosing SatMAE alone meets1–2candidate scope without ambiguity.

## Leakage distinction

Globally pretrained frozen features at test cities support transfer conditional on prior representation, not a claim that foundation pretraining never saw those cities. Prohibit reconstruction adaptation on test chips,test-city normalization/PCA,choice by heldout performance,ACI133-label tuning,spatial damage products,and post-event imagery. Fit all task-specific learned transforms inside training folds only. Use identical eligible records for H,H+X,engineered,GeoAI comparisons to avoid availability confounding.
