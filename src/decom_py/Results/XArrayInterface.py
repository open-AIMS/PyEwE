import warnings
from pathlib import Path

from .ResultsInterface import ResultsInterface
import xarray as xr
import polars as pl

class XarrayCSV(ResultsInterface):
    """A results interface based on Xarray for CSV-like datasets.

    Polars is used for fast CSV parsing, and collated data passed to an Xarray dataset.
    """
    def __init__(self, result_dir):
        self._result_dir = Path(result_dir)

    def extract_metadata(self, file_path):
        """
        Extract metadata from the top of a CSV file.

        The metadata is structured as header sections that start with "<HEADER section/>"
        and end with "<HEADER end/>".

        Args:
            file_path (str): Path to the CSV file

        Returns:
            dict: A nested dict with header section names as keys and their content as values
        """
        metadata = {}
        current_section = None
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()

                # Check if this is a header definition line
                if line.startswith('"<HEADER') and line.endswith('/>\"'):
                    # Extract section name
                    section_name = line.replace('"<HEADER', '').replace('/>"', '').strip()

                    # Check if this is the end marker
                    if section_name == "end":
                        break

                    # Start a new section
                    current_section = section_name
                    metadata[current_section] = {}

                # If we're in a section, add the data
                elif current_section is not None:
                    # Parse the key-value pair
                    line = line.strip('"')
                    parts = line.split(',', 1)  # Split only on the first comma
                    if len(parts) == 2:
                        key, value = parts
                        metadata[current_section][key] = value.strip('"')

        return metadata

    def extract_data(self, result_csv: Path):
        """Extract raw results from EwE outputs."""

        header_row = self._find_data_start(result_csv)

        # data = pl.read_csv(result_csv, skip_lines=header_row-1).to_numpy(structured=True)
        # tbl = xr.DataArray(data)
        data = pl.read_csv(result_csv, skip_lines=header_row)

        return data

    def _identify_row(self, results_csv: Path, needle: str):
        """Identify row with a given string.

        Returns identified row number and content or `None` if match is not found.
        """
        with open(results_csv, "r") as fp:
            for line_number, line in enumerate(fp, 1):
                if needle in line:
                    return line_number, line.strip()

        # No matches found, return none
        return None, None

    def _find_data_start(self, result_csv: Path):
        """
        Search file line-by-line until a table-like data structure is found.
        """
        md_end, _ = self._identify_row(result_csv, "<HEADER end/>")
        if md_end is None:
            raise ValueError("Metadata block could not be identified.")

        header_line = md_end + 1
        with open(result_csv, "r") as fp:
            # Move file pointer to line after header end
            for _ in range(md_end):
                next(fp, None)

            current_line = md_end
            valid_lines = 0
            line = fp.readline()
            while line:
                line = fp.readline()
                if line.strip() != "":
                    valid_lines += 1
                else:
                    valid_lines = 0

                if valid_lines == 2:
                    # Data must have at least two consecutive lines of content after metadata
                    header_line = current_line
                    break

                current_line += 1

        if header_line == (md_end + 1):
            warnings.warn("No data found!")

        return header_line
