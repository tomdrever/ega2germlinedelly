import os
from textwrap import dedent

from gwf import AnonymousTarget # pyright: ignore[reportMissingImports]

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

    # OPTIONS
    # NOTE - will need configuring for other schedulers. This uses a 
    # custom GWF option "tokens" for Sanger LSF - use resource tokens 
    # to limit the number of concurrrent jobs. An alternative would be 
    # to run jobs in batches (multiple input.csv files)
    options = {
        "cores": 1,
        "memory": "500MB",
        "queue": "normal",
        "tokens": ["casm_highio", 50]
    }

    # SPEC
    # Runs pyega3 fetch, then expects to get 1 non-md5 output file in
    # the staging dir, and moves that to the defined output
    spec = dedent(
        rf"""
        {config.pre_script}
        set -euo pipefail

        mkdir -p {staging_dir}

        pyega3 -cf {inputs['credentials']} fetch {ega_file_id} \
            --output-dir {staging_dir} \
            --max-retries -1 \
            --retry-wait 60 \
            --delete-temp-files

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

    return AnonymousTarget(
        inputs=inputs,
        outputs=outputs,
        options=options,
        spec=spec
    ) # type: ignore


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
    # Use a temp GNUPGHOME, and ensure it is cleaned up once the gpg process finishes
    spec = dedent(
        rf"""
        {config.pre_script}
        set -euo pipefail

        export GNUPGHOME="$(mktemp -d "/tmp/gnupg.XXXXXX")"
        chmod 700 "$GNUPGHOME"

        cleanup() {{
            gpgconf --kill gpg-agent 2>/dev/null || true
            rm -rf "${{GNUPGHOME:?}}"
        }}

        trap cleanup EXIT INT TERM HUP

        gpg --batch --yes --pinentry-mode loopback \
            --passphrase-file {inputs['key']} \
            --symmetric --cipher-algo AES256 \
            -o {outputs['gpg']} {inputs['file']}
        {config.post_script}
        """
    )

    return AnonymousTarget(
        inputs=inputs,
        outputs=outputs,
        options={},
        spec=spec
    ) # type: ignore
