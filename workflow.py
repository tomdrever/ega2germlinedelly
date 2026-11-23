"""Germline Delly workflow - the default entrypoint (`gwf status`, `gwf run`, `gwf clean`).

Reads config.json and input.csv from the current directory.
"""
from gwf import Workflow

from common.config import load_config
from common.samplesheet import iter_rows, parse_source
from common.targets import add_encrypt_targets, add_sif_target, stage_sample
from common.util import safe_name
from models import DellyConfig
from templates.delly import delly_call_template

CONFIG_PATH = "config.json"
INPUT_PATH = "input.csv"
DELLY_SIF_URL = "https://github.com/dellytools/delly/releases/download/v0.8.7/delly_v0.8.7.sif"


gwf = Workflow(".") # type: ignore

config = load_config(CONFIG_PATH, DellyConfig)

# Download delly sif
get_delly_sif = add_sif_target(
    gwf,
    name="get_delly_sif",
    source=DELLY_SIF_URL,
    out_dir=config.out_dir,
    config=config
)

# Per-sample targets
for where, row in iter_rows(INPUT_PATH):
    source = parse_source(row, where)
    sample_id_safe = safe_name(source.sample_id)

    # Staging samples (no-op for local BAMs)
    bam_path, bai_path = stage_sample(gwf, source, config)

    # Delly call
    delly_call = gwf.target_from_template(
        name=f"delly_call_{sample_id_safe}",
        template=delly_call_template(
            sample_id=source.sample_id,
            bam_path=bam_path,
            bai_path=bai_path,
            delly_sif=get_delly_sif.outputs["sif"], # type: ignore
            config=config
        )
    )

    # Encrypt if enabled
    add_encrypt_targets(gwf, delly_call, sample_id_safe, config)
