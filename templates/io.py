import os
from textwrap import dedent

from gwf import AnonymousTarget

from models import Config


def download_template(
        ega_file_id: str,
        staging_dir: str,
        out_file_path: str,
        config: Config
        ) -> AnonymousTarget:
    # INPUTS
    inputs = {
        "credentials": config.ega_credentials_path
    }

    # OUTPUTS
    outputs = {
        "file": os.path.join(staging_dir, out_file_path)
    }

    # SPEC
    spec = dedent(
        rf"""
        {config.pre_script}
        set -euo pipefail

        pyega3 -cf {inputs['credentials']} fetch {ega_file_id} --output-dir {staging_dir}

        mapfile -t file_hits < <(find "{staging_dir}/{ega_file_id}" -maxdepth 1 -type f ! -name '*.md5')
        if [ "${{#file_hits[@]}}" -ne 1 ]; then
            echo "Expected one data file in {staging_dir}/{ega_file_id}, found ${{#file_hits[@]}}: ${{file_hits[*]}}" >&2
            exit 1
        fi

        mv "${{file_hits[0]}}" "{outputs['file']}"

        rm -r "{staging_dir}/{ega_file_id}"

        {config.post_script}
        """
    )

    return AnonymousTarget(inputs=inputs, outputs=outputs, options={}, spec=spec) # type: ignore


def encrypt_template(file: str, config: Config) -> AnonymousTarget:
    # INPUTS
    inputs = {
        "file": file,
        "key": config.gpg_key_path
    }

    # OUTPUTS
    outputs = {
        "gpg": file + ".gpg"
    }

    # SPEC
    spec = dedent(
        rf"""
        {config.pre_script}
        set -euo pipefail
        gpg --batch --yes --pinentry-mode loopback \
        --passphrase-file {inputs['key']} \
        --symmetric --cipher-algo AES256 \
        -o {outputs['gpg']} {inputs['file']}
        {config.post_script}
        """
    )

    return AnonymousTarget(inputs=inputs, outputs=outputs, options={}, spec=spec) # type: ignore
