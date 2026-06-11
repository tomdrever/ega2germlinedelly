from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Config:
    ref_path: str
    sites_path: str
    staging_dir: str
    out_dir: str
    pre_script: str = ""
    post_script: str = ""
    singularity_flags: str = ""
    do_delete: bool = False
    ega_credentials_path: str | None = None
    gpg_key_path: str | None = None
