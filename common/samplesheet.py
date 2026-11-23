"""Reading input CSVs.

Every workflow's input starts with the same four columns describing where a
sample's BAM comes from:

    sample_id, ega_bam_file_id, ega_bai_file_id, file_path

Workflow-specific columns follow (e.g. chrom, start, end for subsectioning).
"""
import csv
from collections.abc import Iterator

from common.util import fail
from models import Region, SampleSource

SOURCE_COLUMNS = 4


def iter_rows(path: str) -> Iterator[tuple[str, list[str]]]:
    """Yield (location, stripped cells) for each data row, skipping blank and '#' rows.

    `location` is e.g. "input.csv line 3", for use in error messages.
    """
    try:
        fh = open(path, newline="")
    except FileNotFoundError:
        fail(f"Input file {path} not found - copy {path}.template and fill it out")

    with fh:
        reader = csv.reader(fh)
        for row in reader:
            cells = [cell.strip() for cell in row]

            # Skip empty rows
            if not cells or not cells[0]:
                continue

            # Skip header/comment lines
            if cells[0].startswith("#"):
                continue

            yield f"{path} line {reader.line_num}", cells


def parse_source(row: list[str], where: str) -> SampleSource:
    """Read the sample_id/EGA ID/file path columns and check they're consistent."""
    # Missing trailing columns are treated as empty (e.g. no trailing comma for file_path)
    sample_id, ega_bam_id, ega_bai_id, bam_path = (row + [""] * SOURCE_COLUMNS)[:SOURCE_COLUMNS]

    if ega_bam_id and bam_path:
        fail(f"Error in {where}: must supply either EGA IDs or a path to a BAM file, not both")

    if bool(ega_bam_id) != bool(ega_bai_id):
        fail(f"Error in {where}: if supplying EGA IDs, must provide both BAM and BAI file IDs")

    if not ega_bam_id and not bam_path:
        fail(f"Error in {where}: must supply either EGA IDs or a path to a BAM file")

    return SampleSource(
        sample_id=sample_id,
        ega_bam_id=ega_bam_id,
        ega_bai_id=ega_bai_id,
        bam_path=bam_path,
    )


def parse_region(row: list[str], where: str) -> Region:
    """Read the chrom, start, end columns that follow the source columns."""
    cells = row[SOURCE_COLUMNS:SOURCE_COLUMNS + 3]
    if len(cells) < 3 or not all(cells):
        fail(f"Error in {where}: expected chrom, start and end after the {SOURCE_COLUMNS} source columns")

    chrom, start_text, end_text = cells
    try:
        start, end = int(start_text), int(end_text)
    except ValueError:
        fail(f"Error in {where}: start and end must be whole numbers, got {start_text!r} and {end_text!r}")

    if not 1 <= start <= end:
        fail(f"Error in {where}: need 1 <= start <= end (1-based, inclusive), got {start}-{end}")

    return Region(chrom=chrom, start=start, end=end)
