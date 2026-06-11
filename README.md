# ega2germlinedelly

Small [GWF](https://github.com/gwforg/gwf workflow for running germline Delly 0.8.7 on . Optionally 

## Requirements

- python3 3.10.12
- [gwf](https://github.com/gwforg/gwf) 2.1.1
- [singularity](https://sylabs.io/singularity) 3.11.0
- [pyega2](https://github.com/EGA-archive/ega-download-client) 5.1.0

## Installation

```
git clone git@github.com:tomdrever/ega2germlinedelly.git
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Copy and fill out the template config file and 

```
cp config.json.template config.json
cp input.csv.template input.csv
```
