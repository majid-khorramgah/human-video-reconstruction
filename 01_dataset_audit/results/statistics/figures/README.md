# Figures

This directory contains the visual summaries and diagnostic figures generated during the dataset audit and statistical analysis of the PhySense-Human dataset.

The figures are intended to make the structure, scale, diversity, and temporal characteristics of the dataset easy to inspect without opening the raw data.

---

## Purpose

The goal of this directory is to provide a compact visual overview of the dataset.

The figures answer questions such as:

- How large is the dataset?
- How are frames distributed across train / validation / test?
- How many videos contribute to each split?
- How many frames are extracted from each video?
- What resolutions are present?
- How long are the extracted video sequences?
- Is the dataset dominated by a small number of videos?
- Are there unusual or potentially problematic videos?
- What does a typical sample from the dataset look like?

These visualizations are part of the dataset audit and are not intended to represent final experimental results.

---

# Figure Organization

The current figures are organized around four main aspects:

1. **Dataset scale**
2. **Dataset composition**
3. **Video and temporal structure**
4. **Image / resolution characteristics**

---

## 1. Dataset Overview

### `dataset_overview.png`

A high-level visual summary of the dataset.

This figure should provide a quick understanding of the overall dataset composition, including:

- total number of frames
- total number of videos
- train / validation / test distribution
- number of dataset shards
- distribution of frames across splits

This is the first figure a reader should inspect when trying to understand the dataset.

![Dataset Overview](dataset_overview.png)

---

## 2. Resolution Distribution

### `resolution_distribution.png`

Shows the distribution of image resolutions across the dataset.

This figure is important because the dataset is being investigated for image and video reconstruction / super-resolution research.

It helps answer:

- Are all HR images the same resolution?
- Are there multiple source resolutions?
- Is the LR resolution consistent?
- Are there unusual resolution groups?
- Does the dataset contain heterogeneous image sizes?

![Resolution Distribution](resolution_distribution.png)

### Why this matters

Resolution consistency is important for designing super-resolution experiments.

If the dataset contains multiple resolutions, experiments may need to explicitly account for this rather than assuming a single fixed input/output resolution.

---

## 3. Frames per Video

### `frames_per_video.png`

Shows how many extracted frames are available for each source video.

The dataset was constructed by sampling frames from YouTube videos at approximately one-second intervals.

Therefore, the number of frames associated with a video provides an approximate indication of the temporal duration represented in the dataset.

![Frames per Video](frames_per_video.png)

### Why this matters

This distribution is particularly relevant for temporal reconstruction.

A video with many frames can provide substantially more temporal information than a video contributing only a small number of frames.

The figure can therefore reveal:

- short videos
- long videos
- unusually large videos
- highly unbalanced contributions
- potential dataset concentration around a small number of sources

---

## 4. Videos per Split

### `videos_per_split.png`

Shows the number of unique source videos assigned to:

- training
- validation
- testing

![Videos per Split](videos_per_split.png)

### Why this matters

For video-based learning, the split should be considered at the **video level**, rather than treating individual frames as independent samples.

Frames extracted from the same video are highly correlated.

Therefore, keeping all frames from a source video within a single split prevents temporal information from the same source from leaking between training and evaluation.

The integrity audit confirmed that there is currently no detected video-level overlap between train, validation, and test.

---

# Temporal Analysis

The dataset is sampled temporally rather than consisting of independent still images.

This makes temporal statistics especially important.

Future temporal figures may include:

- frame spacing
- frames per video
- sequence length distribution
- frame-ID continuity
- temporal gaps
- video duration estimates
- motion statistics

These figures help determine whether the dataset contains sufficient temporal redundancy to investigate multi-frame reconstruction.

---

# Dataset Structure

The dataset contains:

- approximately **500,507 HR frames**
- approximately **547 source videos**
- multiple dataset shards
- train / validation / test splits
- HR images
- LR images
- cloth masks
- full-body masks
- skin masks

Each frame is associated with a source video identifier and a frame identifier.

The filename convention contains both the frame number and the source YouTube video identifier.

Example:

`frame_0000033_-Hs-zuBOlQE.jpg`

where:

- `0000033` identifies the frame index
- `-Hs-zuBOlQE` identifies the source video

This structure allows the analysis to operate at both the **frame level** and the **video level**.

---

# Relation to the Research Direction

These figures are not merely dataset documentation.

They are intended to help answer an important research question:

> Does the temporal redundancy naturally present in human-centric video provide useful information for reconstructing higher-quality images from low-resolution observations?

The statistical analysis therefore focuses not only on dataset size, but also on:

- temporal redundancy
- inter-frame similarity
- human motion
- visual correspondence
- spatial resolution
- source-video diversity

The results of these analyses will determine which experimental direction is most promising.

---

# Figure Naming Convention

Figures should use descriptive names rather than generic names such as:

`figure1.png`

Prefer:

`resolution_distribution.png`

instead of:

`figure1.png`

For experiment-specific figures, use:

`exp01_temporal_redundancy.png`

or:

`exp02_single_vs_multi_frame.png`

This makes the repository easier to navigate and keeps figures understandable outside the original notebook.

---

# Recommended Future Figures

As the project progresses, the following figures may be added:

### Dataset composition

- `frames_per_shard.png`
- `frames_per_split.png`
- `videos_per_shard.png`
- `frames_per_video.png`

### Temporal structure

- `frame_interval_distribution.png`
- `sequence_length_distribution.png`
- `temporal_redundancy.png`
- `frame_id_continuity.png`

### Human-centric characteristics

- `person_scale_distribution.png`
- `person_bbox_distribution.png`
- `cloth_area_distribution.png`
- `skin_area_distribution.png`

### Visual correspondence

- `inter_frame_similarity.png`
- `optical_flow_distribution.png`
- `motion_magnitude_distribution.png`
- `correspondence_quality.png`

### Data quality

- `image_quality_distribution.png`
- `brightness_distribution.png`
- `blur_distribution.png`
- `compression_artifacts.png`

Only figures that contribute to a meaningful research or dataset-analysis question should be added.

---

# Source of Figures

Figures in this directory are generated from the dataset statistics and analysis notebooks located elsewhere in the repository.

The raw dataset is **not** stored in this Git repository.

Large intermediate files, raw images, and generated datasets should not be committed unless explicitly required.

The figures stored here are lightweight research artifacts intended to make the analysis reproducible and inspectable.

---

# Interpretation Policy

A figure should not be interpreted as evidence of a research claim by itself.

Figures in this directory are primarily exploratory and diagnostic.

A research claim should be supported by:

1. the underlying dataset statistics,
2. a clearly defined experimental protocol,
3. quantitative measurements,
4. appropriate baselines,
5. and, where possible, statistical or qualitative validation.

The purpose of these figures is to help identify promising research directions before committing to a full experimental pipeline.

---

# Current Status

| Category | Status |
|---|---|
| Dataset overview | Available / In progress |
| Resolution analysis | Available / In progress |
| Frames per video | Available / In progress |
| Videos per split | Available / In progress |
| Temporal analysis | In progress |
| Motion analysis | Planned |
| Visual correspondence | Planned |
| Reconstruction analysis | Planned |

---

## Next Step

The figures generated during the dataset statistics stage will be used to identify the most important characteristics of the dataset.

The next analysis stages will focus on:

**temporal redundancy → motion → visual correspondence → reconstruction potential**

These analyses will eventually determine whether the dataset supports a novel multi-frame human-video reconstruction or super-resolution problem.
