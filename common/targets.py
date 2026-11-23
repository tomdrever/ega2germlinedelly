"""Target-building steps shared between workflows.

Target names produced here are tracked by the LSF backend
(.gwf/lsf-backend-tracked.json), so changing them makes gwf lose track of
submitted jobs. Keep them stable.
"""
import os
import re
from textwrap import dedent

from gwf import Workflow
from gwf.core import Target

from common.util import fail, safe_name
from models import BaseConfig, SampleSource
from templates.io import download_template, encrypt_template


def sif_filename(source: str) -> str:
    """Local filename for a container source.

    https://.../delly_v0.8.7.sif                      -> delly_v0.8.7.sif
    docker://quay.io/biocontainers/samtools:1.23.1--x -> samtools_1.23.1--x.sif
    """
    name = source.rstrip("/").rsplit("/", 1)[-1]
    if name.endswith(".sif"):
        return name
    return re.sub(r"[^A-Za-z0-9._-]", "_", name) + ".sif"


def add_sif_target(gwf: Workflow, name: str, source: str, out_dir: str, config: BaseConfig) -> Target:
    """Fetch a singularity image into `out_dir`: wget for a .sif URL, `singularity pull` otherwise.

    The image is protected, so `gwf clean` keeps it for later runs.
    """
    sif_path = os.path.join(out_dir, sif_filename(source))

    if source.startswith(("http://", "https://")):
        fetch = f"wget -O {sif_path} {source}"
    else:
        # docker://, library://, oras:// ... --force replaces any partial image
        fetch = f"mkdir -p {out_dir} && singularity pull --force {sif_path} {source}"

    return (
        gwf.target(
            name,
            inputs={},
            outputs={
                "sif": sif_path,
            },
            protect=[sif_path]
        )
        << dedent(
            rf"""
            {config.pre_script}
            set -euo pipefail
            {fetch}
            {config.post_script}
            """
        )
    )


def stage_sample(gwf: Workflow, source: SampleSource, config: BaseConfig) -> tuple[str, str]:
    """Return (bam, bai) paths for a sample, adding EGA download targets if needed.

    Local BAMs are used in place, with the index expected at <bam>.bai.
    Call once per sample: target names are per sample, and gwf rejects duplicates.
    """
    if not source.from_ega:
        return source.bam_path, source.bam_path + ".bai"

    if not config.ega_credentials_path:
        fail(f"Sample {source.sample_id} uses EGA file IDs, but ega_credentials_path is not set in the config")

    sample_id_safe = safe_name(source.sample_id)
    staging_dir = os.path.join(config.staging_dir, source.sample_id)

    download_sample_bam = gwf.target_from_template(
        name=f"ega_stage_bam_{sample_id_safe}",
        template=download_template(
            ega_file_id=source.ega_bam_id,
            staging_dir=staging_dir,
            out_file_path=f"{source.sample_id}.bam",
            config=config
        )
    )
    download_sample_bai = gwf.target_from_template(
        name=f"ega_stage_bai_{sample_id_safe}",
        template=download_template(
            ega_file_id=source.ega_bai_id,
            staging_dir=staging_dir,
            out_file_path=f"{source.sample_id}.bam.bai",
            config=config
        )
    )
    return download_sample_bam.outputs["file"], download_sample_bai.outputs["file"]  # type: ignore


def add_encrypt_targets(gwf: Workflow, target: Target, stem: str, config: BaseConfig) -> list[Target]:
    """If gpg_key_path is set, encrypt each output of `target` as encrypt_{stem}_{output key}.

    Encrypting makes `target` an intermediate, so `gwf clean` removes the
    plaintext outputs and keeps the .gpg files.
    """
    if not config.gpg_key_path:
        return []

    return [
        gwf.target_from_template(
            name=f"encrypt_{stem}_{key}",
            template=encrypt_template(
                file=path,
                config=config
            )
        )
        for key, path in target.outputs.items()  # type: ignore
    ]
