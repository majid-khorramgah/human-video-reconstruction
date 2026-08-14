from pathlib import Path
import json
import textwrap


NOTEBOOK_PATH = Path("01_dataset_audit/01_dataset_integrity.ipynb")


cells = []


# ============================================================
# CELL 1 — TITLE
# ============================================================

cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "# Dataset Integrity Audit\n",
        "\n",
        "This notebook validates the structural integrity of the human-video reconstruction dataset across all dataset shards.\n",
        "\n",
        "### Checks\n",
        "- Dataset shard discovery\n",
        "- Train / validation / test structure\n",
        "- Frame ID and video ID extraction\n",
        "- HR ↔ LR correspondence\n",
        "- HR ↔ mask correspondence\n",
        "- Missing files\n",
        "- Filename mismatches\n",
        "- Duplicate frames\n",
        "- Video-level train/validation/test leakage\n",
        "- Frame-level leakage\n",
        "- Cross-shard video overlap\n",
        "\n",
        "**Important:** This notebook does not modify, move, rename, or copy any dataset files.\n"
    ]
})


# ============================================================
# CELL 2 — IMPORTS + CONFIGURATION
# ============================================================

cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": textwrap.dedent("""
        from pathlib import Path
        from collections import defaultdict
        import re
        import json
        import time

        import pandas as pd
        import numpy as np

        from IPython.display import display

        print("Python environment ready.")
    """).strip().splitlines(True)
})


# ============================================================
# CELL 3 — CONFIGURATION
# ============================================================

cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 1. Configuration\n",
        "\n",
        "Set `DATA_ROOT` to the directory containing the five dataset shards.\n"
    ]
})

cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": textwrap.dedent("""
        # ============================================================
        # CHANGE ONLY THIS PATH
        # ============================================================

        DATA_ROOT = Path(r"E:\\")

        # Repository output directory
        OUTPUT_ROOT = Path("01_dataset_audit/results/integrity")

        # Expected dataset structure
        SPLITS = [
            "train",
            "val",
            "test",
        ]

        MODALITIES = [
            "Img_HR",
            "Img_LR",
            "Mask_Cloth_HR",
            "Mask_Cloth_LR",
            "Mask_Full_HR",
            "Mask_Full_LR",
            "Mask_Skin_HR",
            "Mask_Skin_LR",
        ]

        IMAGE_EXTENSIONS = {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".bmp",
            ".tif",
            ".tiff",
        }

        OUTPUT_ROOT.mkdir(
            parents=True,
            exist_ok=True
        )

        print("DATA_ROOT:", DATA_ROOT)
        print("OUTPUT_ROOT:", OUTPUT_ROOT)
    """).strip().splitlines(True)
})


# ============================================================
# CELL 4 — SHARD DISCOVERY
# ============================================================

cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 2. Discover dataset shards\n",
        "\n",
        "The notebook automatically discovers directories whose names begin with `Dataset_Shard_`.\n"
    ]
})

cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": textwrap.dedent("""
        shard_paths = sorted([
            p for p in DATA_ROOT.iterdir()
            if p.is_dir() and p.name.startswith("Dataset_Shard_")
        ])

        print(f"Shards discovered: {len(shard_paths)}")

        for shard in shard_paths:
            print(" -", shard)
    """).strip().splitlines(True)
})


# ============================================================
# CELL 5 — VALIDATE SHARDS
# ============================================================

cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": textwrap.dedent("""
        if len(shard_paths) == 0:
            raise RuntimeError(
                "No Dataset_Shard_* directories were found. "
                "Check DATA_ROOT."
            )

        missing_split_dirs = []

        for shard in shard_paths:
            for split in SPLITS:
                split_path = shard / split

                if not split_path.exists():
                    missing_split_dirs.append({
                        "shard": shard.name,
                        "split": split,
                        "path": str(split_path),
                    })

        if missing_split_dirs:
            print("WARNING: Missing split directories")
            display(pd.DataFrame(missing_split_dirs))
        else:
            print("All shards contain train / val / test.")
    """).strip().splitlines(True)
})


# ============================================================
# CELL 6 — VALIDATE MODALITIES
# ============================================================

cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 3. Validate modality directories"
    ]
})

cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": textwrap.dedent("""
        missing_modalities = []

        for shard in shard_paths:

            for split in SPLITS:

                split_path = shard / split

                for modality in MODALITIES:

                    modality_path = split_path / modality

                    if not modality_path.exists():
                        missing_modalities.append({
                            "shard": shard.name,
                            "split": split,
                            "modality": modality,
                            "path": str(modality_path),
                        })

        if missing_modalities:
            print("WARNING: Missing modality directories")
            display(pd.DataFrame(missing_modalities))
        else:
            print("All expected modality directories exist.")
    """).strip().splitlines(True)
})


# ============================================================
# CELL 7 — FILE DISCOVERY FUNCTION
# ============================================================

cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 4. File discovery\n",
        "\n",
        "Files are indexed by filename. The actual images are not loaded into memory."
    ]
})

cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": textwrap.dedent("""
        def list_image_files(directory):
            if not directory.exists():
                return []

            return sorted([
                p for p in directory.iterdir()
                if p.is_file()
                and p.suffix.lower() in IMAGE_EXTENSIONS
            ])


        def build_file_index(directory):
            files = list_image_files(directory)

            return {
                p.name: p
                for p in files
            }
    """).strip().splitlines(True)
})


# ============================================================
# CELL 8 — PARSE FRAME / VIDEO ID
# ============================================================

cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 5. Parse frame ID and video ID\n",
        "\n",
        "Expected filename example:\n",
        "\n",
        "`frame_0000033_-Hs-zuBOlQE.jpg`\n",
        "\n",
        "The parser extracts:\n",
        "- `frame_id = 33`\n",
        "- `video_id = -Hs-zuBOlQE`\n"
    ]
})

cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": textwrap.dedent("""
        FILENAME_PATTERN = re.compile(
            r"^frame_(\\\\d+)_([^./]+)\\\\.[^.]+$",
            re.IGNORECASE
        )


        def parse_filename(filename):

            match = FILENAME_PATTERN.match(filename)

            if match is None:
                return {
                    "frame_id": None,
                    "video_id": None,
                    "parse_ok": False,
                }

            frame_id = int(match.group(1))
            video_id = match.group(2)

            return {
                "frame_id": frame_id,
                "video_id": video_id,
                "parse_ok": True,
            }


        # Example
        example = "frame_0000033_-Hs-zuBOlQE.jpg"

        print(
            example,
            "→",
            parse_filename(example)
        )
    """).strip().splitlines(True)
})


# ============================================================
# CELL 9 — BUILD MASTER INDEX
# ============================================================

cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 6. Build master dataset index\n",
        "\n",
        "One row represents one frame identity in one split/shard."
    ]
})

cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": textwrap.dedent("""
        master_records = []

        start_time = time.time()

        for shard in shard_paths:

            print(f"\\nProcessing {shard.name}")

            for split in SPLITS:

                split_path = shard / split

                modality_indexes = {
                    modality: build_file_index(
                        split_path / modality
                    )
                    for modality in MODALITIES
                }

                # Use Img_HR as the primary frame index.
                primary_files = modality_indexes["Img_HR"]

                for filename in primary_files:

                    parsed = parse_filename(filename)

                    record = {
                        "shard": shard.name,
                        "split": split,
                        "filename": filename,
                        "frame_id": parsed["frame_id"],
                        "video_id": parsed["video_id"],
                        "parse_ok": parsed["parse_ok"],
                    }

                    for modality in MODALITIES:

                        record[f"has_{modality}"] = (
                            filename in modality_indexes[modality]
                        )

                    master_records.append(record)

        master_df = pd.DataFrame(master_records)

        elapsed = time.time() - start_time

        print(
            f"\\nMaster index created: "
            f"{len(master_df):,} rows "
            f"in {elapsed:.2f} seconds."
        )

        display(master_df.head())
    """).strip().splitlines(True)
})


# ============================================================
# CELL 10 — PARSE ERRORS
# ============================================================

cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 7. Filename parsing validation"
    ]
})

cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": textwrap.dedent("""
        parse_errors = master_df[
            ~master_df["parse_ok"]
        ].copy()

        print(
            f"Filename parsing errors: "
            f"{len(parse_errors):,}"
        )

        if len(parse_errors) > 0:
            display(
                parse_errors[
                    ["shard", "split", "filename"]
                ].head(50)
            )
    """).strip().splitlines(True)
})


# ============================================================
# CELL 11 — MISSING FILES
# ============================================================

cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 8. Missing corresponding files\n",
        "\n",
        "Every `Img_HR` frame should have all seven corresponding files."
    ]
})

cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": textwrap.dedent("""
        expected_columns = [
            f"has_{m}"
            for m in MODALITIES
        ]

        missing_records = []

        for _, row in master_df.iterrows():

            missing = [
                modality
                for modality in MODALITIES
                if not row[f"has_{modality}"]
            ]

            if missing:

                missing_records.append({
                    "shard": row["shard"],
                    "split": row["split"],
                    "filename": row["filename"],
                    "frame_id": row["frame_id"],
                    "video_id": row["video_id"],
                    "missing_modalities": ";".join(missing),
                })

        missing_df = pd.DataFrame(
            missing_records
        )

        print(
            f"Frames with missing corresponding files: "
            f"{len(missing_df):,}"
        )

        if len(missing_df) > 0:
            display(missing_df.head(20))
    """).strip().splitlines(True)
})


# ============================================================
# CELL 12 — ALL MODALITY COUNTS
# ============================================================

cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 9. File counts per modality"
    ]
})

cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": textwrap.dedent("""
        count_records = []

        for shard in shard_paths:

            for split in SPLITS:

                split_path = shard / split

                for modality in MODALITIES:

                    count = len(
                        list_image_files(
                            split_path / modality
                        )
                    )

                    count_records.append({
                        "shard": shard.name,
                        "split": split,
                        "modality": modality,
                        "file_count": count,
                    })

        counts_df = pd.DataFrame(
            count_records
        )

        display(
            counts_df.pivot_table(
                index=["shard", "split"],
                columns="modality",
                values="file_count",
                fill_value=0
            )
        )
    """).strip().splitlines(True)
})


# ============================================================
# CELL 13 — MISMATCHED FILES
# ============================================================

cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 10. Filename mismatch detection\n",
        "\n",
        "Checks whether modality directories contain files that do not exist in `Img_HR`."
    ]
})

cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": textwrap.dedent("""
        mismatch_records = []

        for shard in shard_paths:

            for split in SPLITS:

                split_path = shard / split

                hr_index = build_file_index(
                    split_path / "Img_HR"
                )

                hr_names = set(hr_index.keys())

                for modality in MODALITIES:

                    if modality == "Img_HR":
                        continue

                    modality_index = build_file_index(
                        split_path / modality
                    )

                    extra_files = (
                        set(modality_index.keys())
                        - hr_names
                    )

                    for filename in sorted(extra_files):

                        parsed = parse_filename(
                            filename
                        )

                        mismatch_records.append({
                            "shard": shard.name,
                            "split": split,
                            "modality": modality,
                            "filename": filename,
                            "frame_id": parsed["frame_id"],
                            "video_id": parsed["video_id"],
                            "reason": "file_not_present_in_Img_HR",
                        })

        mismatched_df = pd.DataFrame(
            mismatch_records
        )

        print(
            f"Unexpected/mismatched files: "
            f"{len(mismatched_df):,}"
        )

        if len(mismatched_df) > 0:
            display(
                mismatched_df.head(20)
            )
    """).strip().splitlines(True)
})


# ============================================================
# CELL 14 — DUPLICATES WITHIN SPLIT
# ============================================================

cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 11. Duplicate frame identities\n",
        "\n",
        "A frame identity is defined as `(video_id, frame_id)`."
    ]
})

cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": textwrap.dedent("""
        valid_ids = master_df[
            master_df["parse_ok"]
        ].copy()

        duplicate_mask = (
            valid_ids
            .duplicated(
                subset=[
                    "shard",
                    "split",
                    "video_id",
                    "frame_id"
                ],
                keep=False
            )
        )

        duplicate_df = (
            valid_ids[
                duplicate_mask
            ]
            .sort_values([
                "shard",
                "split",
                "video_id",
                "frame_id"
            ])
        )

        print(
            f"Duplicate frame records: "
            f"{len(duplicate_df):,}"
        )

        if len(duplicate_df) > 0:
            display(
                duplicate_df[
                    [
                        "shard",
                        "split",
                        "video_id",
                        "frame_id",
                        "filename"
                    ]
                ].head(50)
            )
    """).strip().splitlines(True)
})


# ============================================================
# CELL 15 — FRAME OVERLAP BETWEEN SPLITS
# ============================================================

cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 12. Frame-level split leakage"
    ]
})

cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": textwrap.dedent("""
        split_frame_sets = {}

        for split in SPLITS:

            subset = valid_ids[
                valid_ids["split"] == split
            ]

            split_frame_sets[split] = set(
                zip(
                    subset["video_id"],
                    subset["frame_id"]
                )
            )


        frame_overlap_records = []

        for i in range(len(SPLITS)):

            for j in range(i + 1, len(SPLITS)):

                split_a = SPLITS[i]
                split_b = SPLITS[j]

                overlap = (
                    split_frame_sets[split_a]
                    &
                    split_frame_sets[split_b]
                )

                frame_overlap_records.append({
                    "split_a": split_a,
                    "split_b": split_b,
                    "overlap_count": len(overlap),
                })

        frame_overlap_df = pd.DataFrame(
            frame_overlap_records
        )

        display(frame_overlap_df)
    """).strip().splitlines(True)
})


# ============================================================
# CELL 16 — VIDEO LEVEL SPLIT LEAKAGE
# ============================================================

cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 13. Video-level split leakage\n",
        "\n",
        "**This is one of the most important checks in the entire audit.**\n",
        "\n",
        "A video must belong to only one of train / val / test."
    ]
})

cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": textwrap.dedent("""
        split_video_sets = {}

        for split in SPLITS:

            split_video_sets[split] = set(
                valid_ids.loc[
                    valid_ids["split"] == split,
                    "video_id"
                ].dropna()
            )


        video_overlap_records = []

        for i in range(len(SPLITS)):

            for j in range(i + 1, len(SPLITS)):

                split_a = SPLITS[i]
                split_b = SPLITS[j]

                overlap = (
                    split_video_sets[split_a]
                    &
                    split_video_sets[split_b]
                )

                for video_id in sorted(overlap):

                    video_overlap_records.append({
                        "split_a": split_a,
                        "split_b": split_b,
                        "video_id": video_id,
                    })


        video_overlap_df = pd.DataFrame(
            video_overlap_records
        )

        print(
            f"Video-level leakage records: "
            f"{len(video_overlap_df):,}"
        )

        if len(video_overlap_df) > 0:
            display(video_overlap_df.head(50))
        else:
            print("PASS: No video-level overlap detected.")
    """).strip().splitlines(True)
})


# ============================================================
# CELL 17 — CROSS SHARD VIDEO OVERLAP
# ============================================================

cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 14. Cross-shard video overlap\n",
        "\n",
        "The same video should normally not appear in multiple shards unless this was intentional."
    ]
})

cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": textwrap.dedent("""
        video_to_shards = defaultdict(set)

        for _, row in valid_ids.iterrows():

            video_to_shards[row["video_id"]].add(
                row["shard"]
            )


        cross_shard_records = []

        for video_id, shards in video_to_shards.items():

            if len(shards) > 1:

                cross_shard_records.append({
                    "video_id": video_id,
                    "num_shards": len(shards),
                    "shards": ";".join(
                        sorted(shards)
                    ),
                })


        cross_shard_df = pd.DataFrame(
            cross_shard_records
        )

        print(
            f"Videos appearing in multiple shards: "
            f"{len(cross_shard_df):,}"
        )

        if len(cross_shard_df) > 0:
            display(
                cross_shard_df.head(50)
            )
        else:
            print(
                "PASS: No cross-shard video overlap detected."
            )
    """).strip().splitlines(True)
})


# ============================================================
# CELL 18 — VIDEO / FRAME COUNTS
# ============================================================

cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 15. Dataset structure summary"
    ]
})

cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": textwrap.dedent("""
        structure_records = []

        for shard in shard_paths:

            for split in SPLITS:

                subset = valid_ids[
                    (valid_ids["shard"] == shard.name)
                    &
                    (valid_ids["split"] == split)
                ]

                structure_records.append({
                    "shard": shard.name,
                    "split": split,
                    "frames": len(subset),
                    "videos": subset["video_id"].nunique(),
                })


        structure_df = pd.DataFrame(
            structure_records
        )

        display(structure_df)

        print("\\nTotals:")
        print(
            structure_df[
                ["frames", "videos"]
            ].sum()
        )
    """).strip().splitlines(True)
})


# ============================================================
# CELL 19 — VIDEO FRAME SEQUENCE CHECK
# ============================================================

cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 16. Temporal sequence sanity check\n",
        "\n",
        "Check whether frame IDs inside each video are monotonically increasing and whether there are gaps.\n",
        "\n",
        "Because frames were sampled approximately once per second, gaps may be meaningful and are therefore **reported, not automatically treated as errors**."
    ]
})

cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": textwrap.dedent("""
        sequence_records = []

        for (shard, split, video_id), group in valid_ids.groupby(
            ["shard", "split", "video_id"]
        ):

            frame_ids = sorted(
                group["frame_id"].astype(int).tolist()
            )

            if len(frame_ids) == 0:
                continue

            diffs = np.diff(frame_ids)

            sequence_records.append({
                "shard": shard,
                "split": split,
                "video_id": video_id,
                "num_frames": len(frame_ids),
                "min_frame_id": min(frame_ids),
                "max_frame_id": max(frame_ids),
                "num_gaps": int(np.sum(diffs > 1)),
                "max_gap": int(max(diffs)) if len(diffs) else 0,
                "monotonic": all(diffs > 0) if len(diffs) else True,
            })


        sequence_df = pd.DataFrame(
            sequence_records
        )

        display(
            sequence_df.head(20)
        )

        print(
            "Videos with frame-ID gaps:",
            int(
                (sequence_df["num_gaps"] > 0).sum()
            )
        )
    """).strip().splitlines(True)
})


# ============================================================
# CELL 20 — SAVE MASTER INDEX
# ============================================================

cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 17. Save integrity outputs"
    ]
})

cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": textwrap.dedent("""
        # Save master index
        master_df.to_csv(
            OUTPUT_ROOT / "master_index.csv",
            index=False
        )

        # Missing files
        missing_df.to_csv(
            OUTPUT_ROOT / "missing_files.csv",
            index=False
        )

        # Mismatches
        mismatched_df.to_csv(
            OUTPUT_ROOT / "mismatched_files.csv",
            index=False
        )

        # Duplicates
        duplicate_df.to_csv(
            OUTPUT_ROOT / "duplicate_frames.csv",
            index=False
        )

        # Video overlap
        video_overlap_df.to_csv(
            OUTPUT_ROOT / "split_overlap.csv",
            index=False
        )

        # Frame overlap
        frame_overlap_df.to_csv(
            OUTPUT_ROOT / "frame_split_overlap.csv",
            index=False
        )

        # Cross-shard overlap
        cross_shard_df.to_csv(
            OUTPUT_ROOT / "cross_shard_video_overlap.csv",
            index=False
        )

        # Sequence information
        sequence_df.to_csv(
            OUTPUT_ROOT / "video_sequence_statistics.csv",
            index=False
        )

        # Structure
        structure_df.to_csv(
            OUTPUT_ROOT / "dataset_structure.csv",
            index=False
        )

        print("All integrity outputs saved.")
    """).strip().splitlines(True)
})


# ============================================================
# CELL 21 — FINAL PASS/FAIL REPORT
# ============================================================

cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 18. Final integrity report"
    ]
})

cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": textwrap.dedent("""
        checks = {}

        checks["shards_found"] = len(shard_paths) > 0

        checks["all_splits_present"] = (
            len(missing_split_dirs) == 0
        )

        checks["all_modalities_present"] = (
            len(missing_modalities) == 0
        )

        checks["filename_parsing"] = (
            len(parse_errors) == 0
        )

        checks["no_missing_corresponding_files"] = (
            len(missing_df) == 0
        )

        checks["no_unexpected_files"] = (
            len(mismatched_df) == 0
        )

        checks["no_duplicate_frames"] = (
            len(duplicate_df) == 0
        )

        checks["no_frame_split_overlap"] = (
            frame_overlap_df["overlap_count"].sum() == 0
        )

        checks["no_video_split_overlap"] = (
            len(video_overlap_df) == 0
        )

        # Cross-shard overlap is reported separately.
        checks["no_cross_shard_video_overlap"] = (
            len(cross_shard_df) == 0
        )


        print("=" * 70)
        print("DATASET INTEGRITY REPORT")
        print("=" * 70)

        for name, passed in checks.items():

            status = "PASS" if passed else "FAIL"

            print(
                f"{status:>5}  {name}"
            )

        print("=" * 70)


        overall_core_pass = all([
            checks["shards_found"],
            checks["all_splits_present"],
            checks["all_modalities_present"],
            checks["filename_parsing"],
            checks["no_missing_corresponding_files"],
            checks["no_unexpected_files"],
            checks["no_duplicate_frames"],
            checks["no_frame_split_overlap"],
            checks["no_video_split_overlap"],
        ])

        print()

        if overall_core_pass:
            print(
                "CORE INTEGRITY: PASS"
            )
        else:
            print(
                "CORE INTEGRITY: FAIL"
            )

        print(
            "\\nCross-shard video overlap is reported separately "
            "because it may be intentional depending on how "
            "the shards were generated."
        )
    """).strip().splitlines(True)
})


# ============================================================
# CELL 22 — JSON SUMMARY
# ============================================================

cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 19. Save machine-readable summary"
    ]
})

cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": textwrap.dedent("""
        summary = {
            "num_shards": len(shard_paths),
            "num_master_records": len(master_df),
            "num_videos": int(
                valid_ids["video_id"].nunique()
            ),
            "num_missing_records": len(missing_df),
            "num_mismatched_records": len(mismatched_df),
            "num_duplicate_records": len(duplicate_df),
            "num_video_split_overlap_records": len(
                video_overlap_df
            ),
            "num_frame_split_overlap_pairs": int(
                len(frame_overlap_df)
            ),
            "num_cross_shard_video_overlap": len(
                cross_shard_df
            ),
            "checks": checks,
            "core_integrity_pass": overall_core_pass,
        }


        with open(
            OUTPUT_ROOT / "integrity_summary.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                summary,
                f,
                indent=2
            )


        print(
            json.dumps(
                summary,
                indent=2
            )
        )
    """).strip().splitlines(True)
})


# ============================================================
# CELL 23 — README-STYLE FINAL NOTES
# ============================================================

cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "# Interpretation\n",
        "\n",
        "This notebook does not determine whether the dataset is scientifically useful for super-resolution or temporal reconstruction.\n",
        "\n",
        "It answers a more basic question:\n",
        "\n",
        "> **Is the dataset structurally reliable enough to support later research experiments?**\n",
        "\n",
        "Only after the core integrity checks pass should the project proceed to dataset statistics and visual analysis.\n"
    ]
})


# ============================================================
# CREATE NOTEBOOK
# ============================================================

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.x"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 5
}


NOTEBOOK_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)


with open(
    NOTEBOOK_PATH,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        notebook,
        f,
        indent=2
    )


print(
    f"Notebook created successfully:\\n{NOTEBOOK_PATH}"
)
