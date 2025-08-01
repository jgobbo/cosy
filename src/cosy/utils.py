import os
from pathlib import Path

from .constants import ROOT_DIR

__all__ = [
    "edit_lines",
    "create_file_from_template",
    "process_file",
    "lis_purge",
    "LensTable",
]


def edit_lines(
    replacements: list[tuple[str, list[str] | str]],
    template_lines: list[str],
) -> None:
    """Edit lines of COSY scripts.

    Args
    ----
    replacements : list[tuple[str, str | list[str]]]
        A list of replacements for the `template_lines`. The first element of each tuple
        is a string which identifies the line you want to change. The second element is
        either a string of the replacement line or a list of strings, each of which is
        a replacement line.
    template_lines : list[str]
        A list of lines of COSY code. Typically a list is loaded with `.readlines()` on
        a COSY file.

    Returns
    -------
    new_lines : list[str]
        The edited lines
    """
    new_lines = []
    for line in template_lines:
        replaced = False
        for identifier, replacement in replacements:
            if identifier in line:
                replaced = True
                if isinstance(replacement, list):
                    for individual_replacement in replacement:
                        new_lines.append(f"{individual_replacement};\n")
                elif isinstance(replacement, str):
                    new_lines.append(f"{replacement};\n")
                else:
                    assert replacement is None
        if not replaced:
            new_lines.append(line)
    return new_lines


def create_file_from_template(
    replacements: list[tuple[str, str | list[str]]],
    template_lines: list[str],
    filepath: Path,
) -> None:
    """Create a COSY file from the template with specified replacements.

    Args
    ----
    replacements : list[tuple[str, str | list[str]]]
        A list of replacements for the `template_lines`. The first element of each tuple
        is a string which identifies the line you want to change. The second element is
        either a string of the replacement line or a list of strings, each of which is
        a replacement line.
    template_lines : list[str]
        A list of lines of COSY code. Typically a list is loaded with `.readlines()` and
        the raw lines are edited with `edit_lines`.
    filepath: Path
        The filepath for the created file
    """

    new_lines = edit_lines(replacements=replacements, template_lines=template_lines)
    with open(filepath, "wt") as f:
        f.writelines(new_lines)


def process_file(process_id: int, file: Path) -> Path:
    """Append the `process_id` to the `file` and return the full `Path`."""
    split_name = file.name.split(".")
    return ROOT_DIR / f"{split_name[0]}_{process_id}.{split_name[1]}"


def lis_purge(folder: Path = ROOT_DIR) -> None:
    """Delete all .lis files in the provided folder."""
    for file in os.listdir(folder):
        if file.endswith(".lis"):
            os.remove(folder / file)


class LensTable(dict):
    """A `dict` subclass for prettier printing"""

    def __str__(self):
        string = "{"
        for key, val in self.items():
            string += f"{key}: {val:.1f}, "
        string = "".join(string.rsplit(", ", 1)) + "}"
        return string
