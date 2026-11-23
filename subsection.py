"""Subsectioning workflow - extract chrom:start-end regions from BAMs with samtools.

Run with `gwf -f subsection.py <command>` (status, run, clean, ...).
Reads subsection_config.json and subsection_input.csv from the current directory.
"""
from gwf import Workflow

from common.config import load_config
from common.samplesheet import iter_rows, parse_region, parse_source
from common.targets import add_encrypt_targets, add_sif_target, stage_sample
from common.util import fail, safe_name
from models import Region, SampleSource, SubsectionConfig
from templates.samtools import subsection_template

CONFIG_PATH = "subsection_config.json"
INPUT_PATH = "subsection_input.csv"


gwf = Workflow(".") # type: ignore

config = load_config(CONFIG_PATH, SubsectionConfig)

# Download samtools sif
get_samtools_sif = add_sif_target(
    gwf,
    name="get_samtools_sif",
    source=config.samtools_image,
    out_dir=config.out_dir,
    config=config
)

# Read input, grouping regions by sample so each BAM is staged once
# however many regions are taken from it
sources: dict[str, SampleSource] = {}
regions: dict[str, list[Region]] = {}
for where, row in iter_rows(INPUT_PATH):
    source = parse_source(row, where)
    region = parse_region(row, where)

    if sources.setdefault(source.sample_id, source) != source:
        fail(f"Error in {where}: sample {source.sample_id} has different EGA IDs or file path to an earlier row")

    sample_regions = regions.setdefault(source.sample_id, [])
    if region in sample_regions:
        fail(f"Error in {where}: duplicate region {region.samtools_region} for sample {source.sample_id}")
    sample_regions.append(region)

# Per-sample, per-region targets
for sample_id, source in sources.items():
    # Staging samples (no-op for local BAMs)
    bam_path, bai_path = stage_sample(gwf, source, config)

    for region in regions[sample_id]:
        stem = f"{safe_name(sample_id)}_{region.label}"

        # Subsection
        subsection = gwf.target_from_template(
            name=f"subsection_{stem}",
            template=subsection_template(
                sample_id=sample_id,
                bam_path=bam_path,
                bai_path=bai_path,
                region=region,
                samtools_sif=get_samtools_sif.outputs["sif"], # type: ignore
                config=config
            )
        )

        # Encrypt if enabled
        add_encrypt_targets(gwf, subsection, stem, config)
