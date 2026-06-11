import os
from textwrap import dedent

from gwf import AnonymousTarget

from models import Config


def download_template(
        ega_file_id: str,
        staging_dir: str,
        out_file: str,
        config: Config
        ) -> AnonymousTarget:
    # INPUTS
    inputs = {
        "credentials": config.ega_credentials_path
    }

    # OUTPUTS
    outputs = {
        "file": os.path.join(staging_dir, out_file)
    }

    # SPEC
    spec = dedent(
        rf"""
        {config.pre_script}
        set -euo pipefail

        mkdir -p {staging_dir}

        tmp_dir=$(mktemp -d -p {staging_dir})
        trap "rm -f ${{tmp_dir}}" EXIT

        pyega3 -cf {inputs['credentials']} fetch {ega_file_id} --output-dir ${{tmp_dir}}

        mv ${{tmp_dir}}/{ega_file_id}/* {outputs['file']}

        {config.post_script}
        """
    )

    return AnonymousTarget(inputs=inputs, outputs=outputs, options={}, spec=spec) # type: ignore


def remove_template(file: str, done_file: str, config: Config) -> AnonymousTarget:
    # INPUTS
    inputs = {
        "file": file,
        "required_done": done_file
    }

    # OUTPUTS
    outputs = {
        "done": file + ".remove.done"
    }

    # SPEC
    spec = dedent(
        rf"""
        {config.pre_script}
        set -euo pipefail
        rm {inputs['file']}
        touch {outputs['done']}
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
        -o {outputs['gpg']}
        {config.post_script}
        """
    )

    return AnonymousTarget(inputs=inputs, outputs=outputs, options={}, spec=spec) # type: ignore
