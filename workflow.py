import os
import sys
import csv
import json
from textwrap import dedent

from gwf import Workflow

from models import Config
from templates.io import download_template, encrypt_template, remove_template
from templates.delly import delly_call_template


def _exit(message: str) -> None:
    print(message)
    sys.exit(1)


gwf = Workflow(".")

# Parse config
with open("config.json") as fh:
    try: 
        config = Config(**json.load(fh))
    except TypeError as e:
        print(str(e))
        sys.exit(1)

delly_sif_path = os.path.join(config.out_dir, "delly_v0.8.7.sif")
get_delly_sif = (
    gwf.target(
        "get_delly_sif",
        inputs={},
        outputs={
            "sif": delly_sif_path,
        },
    )
    << dedent(
        rf"""
        {config.pre_script}
        set -euo pipefail
        wget -O {delly_sif_path} https://github.com/dellytools/delly/releases/download/v0.8.7/delly_v0.8.7.sif
        {config.post_script}
        """
    )
)

# Per-sample targets
with open('input.csv', "r") as file:
    for i, row in enumerate(csv.reader(file)):
        # Skip header/comment lines
        if row[0].startswith("#"):
            continue

        # Read sample sheet lines
        sample_id = row[0].strip()
        sample_id_safe = sample_id.replace("-", "_")
        ega_bam_id = row[1].strip()
        ega_bai_id = row[2].strip()
        bam_path = row[3].strip()

        # Check either using ega file IDs or bam paths
        if ega_bam_id and bam_path:
            _exit(f"Error in input line {i}: must supply either ega IDs or a path to a BAM file")

        if bool(ega_bam_id) and not bool(ega_bai_id):
            _exit(f"Error in input line {i}: if supplying ega IDs must provide both BAM and BAI File IDs")
        
        # Staging samples
        if ega_bam_id:
            download_sample_bam = gwf.target_from_template(
                name=f"ega_stage_bam_{sample_id_safe}",
                template=download_template(
                    ega_file_id=ega_bam_id,
                    staging_dir=os.path.join(config.staging_dir, sample_id),
                    out_file=f"{sample_id}.bam",
                    config=config
                )
            )
            download_sample_bai = gwf.target_from_template(
                name=f"ega_stage_bai_{sample_id_safe}",
                template=download_template(
                    ega_file_id=ega_bai_id,
                    staging_dir=os.path.join(config.staging_dir, sample_id),
                    out_file=f"{sample_id}.bam.bai",
                    config=config
                )
            )
            bam_path = download_sample_bam.outputs["file"] # type: ignore
            bai_path = download_sample_bai.outputs["file"] # type: ignore
        else:
            bai_path = bam_path + ".bai"

        # Delly call
        delly_call = gwf.target_from_template(
            name=f"delly_call_{sample_id_safe}",
            template=delly_call_template(
                sample_id=sample_id,
                bam_path=bam_path,
                bai_path=bai_path,
                delly_sif=get_delly_sif.outputs['sif'], # type: ignore
                config=config
            )
        )

        # Remove staged files
        if ega_bam_id and config.do_delete:
            for i, file in enumerate([bam_path, bai_path]):
                gwf.target_from_template(
                    name=f"unstage_{sample_id_safe}_{i}",
                    template=remove_template(
                        file=file, # type: ignore
                        done_file=delly_call.outputs['bcf'], # type: ignore
                        config=config
                    )
                )

        # Encrypt if enabled
        if config.gpg_key_path:
            for i, file in enumerate([delly_call.outputs['bcf'], delly_call.outputs['csi']]): # type: ignore
                encyrpt_bcf = gwf.target_from_template(
                    name=f"encrypt_{sample_id_safe}_result_{i}",
                    template=encrypt_template(
                        file=file, # type: ignore
                        config=config
                    )
                )
