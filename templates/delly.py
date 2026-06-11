import os
from textwrap import dedent

from gwf import AnonymousTarget

from models import Config


def delly_call_template(
        sample_id: str,
        bam_path: str,
        bai_path: str,
        delly_sif: str,
        config: Config) -> AnonymousTarget:
    # INPUTS
    inputs = {
        "bam": bam_path,
        "bai": bai_path,
        "sif": delly_sif,
        "ref": config.ref_path,
        "sites": config.sites_path
    }

    # OUTPUTS
    outputs = {
        "bcf": os.path.join(config.out_dir, sample_id, f"{sample_id}.bcf"),
        "csi": os.path.join(config.out_dir, sample_id, f"{sample_id}.bcf.csi")
    }

    # OPTIONS
    options = {
        "cores": 2,
        "memory": "20GB",
        "queue": "normal"
    }

    # SPEC
    spec = dedent(
        rf"""
        {config.pre_script}
        set -euo pipefail
        singularity exec {config.singularity_flags} ${inputs['sif']} \
            delly call \
            -g {inputs['ref']} \
            -v {inputs['sites']} \
            -o {outputs['bcf']} \
            {inputs}
        {config.post_script}
        """
    )

    return AnonymousTarget(inputs=inputs, outputs=outputs, options=options, spec=spec) # type: ignore
