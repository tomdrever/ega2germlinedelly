import os
import shlex
from textwrap import dedent

from gwf import AnonymousTarget

from models import Region, SubsectionConfig


def subsection_template(
        sample_id: str,
        bam_path: str,
        bai_path: str,
        region: Region,
        samtools_sif: str,
        config: SubsectionConfig) -> AnonymousTarget:
    # INPUTS
    inputs = {
        "bam": bam_path,
        "bai": bai_path,
        "sif": samtools_sif
    }

    # OUTPUTS
    out_dir = os.path.join(config.out_dir, sample_id)
    out_prefix = os.path.join(out_dir, f"{sample_id}_sv_subregion_{region.label}")
    outputs = {
        "bam": f"{out_prefix}.bam",
        "bai": f"{out_prefix}.bam.bai"
    }

    # OPTIONS
    options = {
        "cores": 1,
        "memory": "2GB",
        "queue": "normal"
    }

    # SPEC
    # -X passes the index explicitly, so it doesn't matter whether it's named
    # x.bam.bai or x.bai. The output is written under a temporary name and only
    # moved into place once indexed, so a failed job never leaves a
    # complete-looking output for gwf to skip on the next run.
    tmp_bam = f"{outputs['bam']}.tmp.bam"
    tmp_bai = f"{tmp_bam}.bai"
    spec = dedent(
        rf"""
        {config.pre_script}
        set -euo pipefail
        mkdir -p {out_dir}

        singularity exec {config.singularity_flags} {inputs['sif']} \
            samtools view -b -X \
            -o {tmp_bam} \
            {inputs['bam']} {inputs['bai']} \
            {shlex.quote(region.samtools_region)}

        singularity exec {config.singularity_flags} {inputs['sif']} \
            samtools index {tmp_bam} {tmp_bai}

        mv {tmp_bam} {outputs['bam']}
        mv {tmp_bai} {outputs['bai']}
        {config.post_script}
        """
    )

    return AnonymousTarget(
        inputs=inputs, # type: ignore
        outputs=outputs, # type: ignore
        options=options,
        spec=spec
    )
