from dataclasses import dataclass

from common.util import safe_name


# kw_only lets the per-workflow subclasses add required fields after the
# base class's defaulted ones. Configs are always built from keyword arguments
# (see common/config.py: load_config).
@dataclass(slots=True, frozen=True, kw_only=True)
class BaseConfig:
    """Settings shared by every workflow: staging, outputs, encryption and job wrapping."""
    staging_dir: str
    out_dir: str
    pre_script: str = ""
    post_script: str = ""
    singularity_flags: str = ""
    ega_credentials_path: str | None = None
    gpg_key_path: str | None = None


@dataclass(slots=True, frozen=True, kw_only=True)
class DellyConfig(BaseConfig):
    ref_path: str
    sites_path: str


@dataclass(slots=True, frozen=True, kw_only=True)
class SubsectionConfig(BaseConfig):
    samtools_image: str = "docker://quay.io/biocontainers/samtools:1.23.1--ha83d96e_0"


@dataclass(slots=True, frozen=True)
class SampleSource:
    """Where a sample's BAM comes from: EGA file IDs to download, or a local path."""
    sample_id: str
    ega_bam_id: str
    ega_bai_id: str
    bam_path: str

    @property
    def from_ega(self) -> bool:
        return bool(self.ega_bam_id)


@dataclass(slots=True, frozen=True)
class Region:
    """A 1-based, inclusive genomic interval, as samtools expects."""
    chrom: str
    start: int
    end: int

    @property
    def samtools_region(self) -> str:
        # samtools needs braces around contig names containing ':' (e.g. HLA alleles)
        chrom = f"{{{self.chrom}}}" if ":" in self.chrom else self.chrom
        return f"{chrom}:{self.start}-{self.end}"

    @property
    def label(self) -> str:
        """Target-name and filename safe form, e.g. chr8_127700000_127800000."""
        return f"{safe_name(self.chrom)}_{self.start}_{self.end}"
