"""Helper utilities for parsing COBOL artifacts."""
import re
import pathlib
from typing import Dict, List, Tuple


def parse_copybook_fields(filepath: pathlib.Path) -> List[Dict]:
    """Parse a COBOL copybook and return field definitions.

    Returns a list of dicts with keys: level, name, pic, size.
    Also includes group-level items (no PIC) with size=0.
    """
    fields = []
    text = filepath.read_text()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("*") or not stripped:
            continue
        # Match fields with PIC clauses
        match = re.match(
            r"(\d{2})\s+([\w-]+)\s+PIC\s+(.+?)\.",
            stripped,
        )
        if match:
            level = int(match.group(1))
            name = match.group(2)
            pic = match.group(3).strip()
            size = compute_pic_size(pic)
            fields.append(
                {"level": level, "name": name, "pic": pic, "size": size}
            )
        else:
            # Match group-level items (no PIC clause)
            grp = re.match(r"(\d{2})\s+([\w-]+)\.", stripped)
            if grp:
                level = int(grp.group(1))
                name = grp.group(2)
                fields.append(
                    {"level": level, "name": name, "pic": "", "size": 0}
                )
    return fields


def compute_pic_size(pic: str) -> int:
    """Compute the storage size in bytes for a PIC clause.

    In COBOL DISPLAY format:
    - S (sign) is stored in the zone of the last digit, no extra byte
    - V (implied decimal) occupies no storage
    - 9, X each occupy 1 byte per character position
    """
    pic = pic.strip()

    # Remove leading S (sign) - no extra storage in DISPLAY format
    pic_clean = re.sub(r"^S", "", pic)
    # Remove V (implied decimal point) - no storage
    pic_clean = re.sub(r"V", "", pic_clean)

    total = 0
    # Match repeated groups like 9(11), X(16), etc.
    pattern = re.compile(r"([9X])\((\d+)\)|([9X])")
    for m in pattern.finditer(pic_clean):
        if m.group(1):
            total += int(m.group(2))
        elif m.group(3):
            total += 1
    return total


def compute_record_length(filepath: pathlib.Path) -> int:
    """Compute total record length from a copybook including FILLER."""
    fields = parse_copybook_fields(filepath)
    total = 0
    for f in fields:
        if f["level"] > 1:
            total += f["size"]
    return total


def get_declared_record_length(filepath: pathlib.Path) -> int:
    """Extract the declared record length from a copybook comment like (RECLN 300)."""
    text = filepath.read_text()
    match = re.search(r"RECLN\s*=?\s*(\d+)", text)
    if match:
        return int(match.group(1))
    return -1


def parse_cobol_copy_statements(filepath: pathlib.Path) -> List[str]:
    """Extract all COPY copybook references from a COBOL program."""
    copies = []
    text = filepath.read_text()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("*"):
            continue
        match = re.search(r"COPY\s+([\w]+)\.", stripped)
        if match:
            copies.append(match.group(1))
    return copies


def parse_cobol_program_id(filepath: pathlib.Path) -> str:
    """Extract PROGRAM-ID from a COBOL source file."""
    text = filepath.read_text()
    match = re.search(r"PROGRAM-ID\.\s*([\w]+)", text, re.IGNORECASE)
    return match.group(1) if match else ""


def parse_cobol_paragraphs(filepath: pathlib.Path) -> List[str]:
    """Extract paragraph names from the PROCEDURE DIVISION."""
    paragraphs = []
    text = filepath.read_text()
    in_procedure = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("*"):
            continue
        if "PROCEDURE DIVISION" in stripped.upper():
            in_procedure = True
            continue
        if in_procedure:
            match = re.match(r"^([\w][\w-]+)\.", stripped)
            if match:
                name = match.group(1)
                if name.upper() not in (
                    "STOP", "EXIT", "GOBACK", "END",
                ):
                    paragraphs.append(name)
    return paragraphs


def parse_jcl_programs(filepath: pathlib.Path) -> List[str]:
    """Extract program names from EXEC PGM= statements in JCL."""
    programs = []
    text = filepath.read_text()
    for line in text.splitlines():
        match = re.search(r"EXEC\s+PGM=([\w]+)", line, re.IGNORECASE)
        if match:
            programs.append(match.group(1))
    return programs


def parse_jcl_datasets(filepath: pathlib.Path) -> List[str]:
    """Extract dataset names (DSN=) from JCL."""
    datasets = []
    text = filepath.read_text()
    for line in text.splitlines():
        match = re.search(r"DSN=([\w.()+ ]+)", line, re.IGNORECASE)
        if match:
            datasets.append(match.group(1).strip())
    return datasets


def parse_bms_mapset_name(filepath: pathlib.Path) -> str:
    """Extract the mapset name from BMS source."""
    text = filepath.read_text()
    match = re.search(r"^(\w+)\s+DFHMSD", text, re.MULTILINE)
    return match.group(1) if match else ""


def parse_bms_map_names(filepath: pathlib.Path) -> List[str]:
    """Extract map names (DFHMDI) from BMS source."""
    maps = []
    text = filepath.read_text()
    for match in re.finditer(r"^(\w+)\s+DFHMDI", text, re.MULTILINE):
        maps.append(match.group(1))
    return maps


def parse_bms_field_names(filepath: pathlib.Path) -> List[str]:
    """Extract named field definitions (DFHMDF with a label) from BMS source."""
    fields = []
    text = filepath.read_text()
    for match in re.finditer(r"^(\w+)\s+DFHMDF", text, re.MULTILINE):
        fields.append(match.group(1))
    return fields
