# ega2germlinedelly

Small [GWF](https://github.com/gwforg/gwf) workflow for running germline Delly 0.8.7. If EGAF IDs and a valid [EGA credential file](https://github.com/EGA-archive/ega-download-client/blob/master/pyega3/config/default_credential_file.json) is provided, will also use pyega3 to download the BAM and BAI files.

```mermaid
flowchart TB

get_delly_sif --> delly_call

subgraph per_sample["Per sample"]
stage_bam -.-> delly_call
stage_bai -.-> delly_call
delly_call -.-> encrypt_bcf
delly_call -.-> encrypt_csi
end

style per_sample fill:#eee,stroke:#333

class stage_bam,stage_bai,encrypt_bcf,encrypt_csi opt
class get_delly_sif,stage_bam,stage_bai,delly_call,encrypt_bcf,encrypt_csi node
classDef opt stroke-dasharray: 5 5
classDef node fill:#fff,stroke:#333
```

## Requirements
- python3 3.10.12
- [gwf](https://github.com/gwforg/gwf) 2.1.1
- [singularity](https://sylabs.io/singularity) 3.11.0
- [pyega3](https://github.com/EGA-archive/ega-download-client) 5.1.0 (optional)

## Installation
```
git clone git@github.com:tomdrever/ega2germlinedelly.git
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Usage
1. Copy and fill out the template config file and input csv. These specify staging and output directories, whether to encrypt the result files with a gpg key.
    ```
    cp config.json.template config.json
    cp input.csv.template input.csv
    ```

2. Check the targets generated.
    ```
    gwf status
    ```

3. Run the workflow.
    ```
    gwf run
    ```

4. (Optional) Remove the intermediates (Delly sif, staged EGA files if downloading and unencrypted Delly BCFs if encrypting).
    ```
    gwf clean
    ```
