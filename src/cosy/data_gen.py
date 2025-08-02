"""To train ML models, you need a lot of data. The `DataGenerator` class allows for easy
data generation. Assuming you have a working COSY model and template file, you can
simply create an instance of the class with whatever `lens_limits` and call
`parallel_data_gen` to continuously generate data. There's no easy way to gracefully
shut down the data generation, so I just interrupt it and trim out the resulting bad
data when loading it later.
"""

import subprocess, random, time, os
from datetime import timedelta
from itertools import count
from multiprocessing import (
    Pool,
    Lock,
    current_process,
)
import numpy as np

from cosy.utils import process_file, create_file_from_template, LensTable
from cosy.constants import (
    FOX_DIR,
    RESULTS_DIR,
    Electrode,
    HARDWARE_RESTRICTED_LENS_LIMITS,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

LOCK = Lock()

FUNCTION_FILE = FOX_DIR / "DataGeneration.fox"
OUTPUT_FILE = FOX_DIR / "output.txt"
RESULT_FOLDER = RESULTS_DIR / "simulation_data" / "model_data"


class DataGenerator:
    lens_limits: dict[Electrode, tuple[float, float]]
    template_lines: list[str]

    def __init__(self, lens_limits=None):
        os.chdir(FOX_DIR)
        self.lens_limits = (
            HARDWARE_RESTRICTED_LENS_LIMITS if lens_limits is None else lens_limits
        )
        with open(FOX_DIR / "DataGenerationTemplate.fox", "rt") as f:
            self.template_lines = f.readlines()

    def generate_datum_for_model(self, filename: str) -> None:
        input_array = np.array(
            [
                random.uniform(lens_limit[0], lens_limit[1])
                for lens_limit in self.lens_limits.values()
            ]
        )
        lens_table = LensTable(
            zip(list(self.lens_limits.keys()), input_array.flatten())
        )

        try:
            (process_id,) = current_process()._identity
        except ValueError:
            process_id = 0
        curr_output_file = process_file(process_id, OUTPUT_FILE)
        curr_function_file = process_file(process_id, FUNCTION_FILE)

        with open(curr_output_file, "wt") as f:
            f.write("None")

        self._prep_function_file(
            process_id,
            lens_table,
            template_lines=self.template_lines,
            destination_file=curr_function_file,
        )

        try:
            subprocess.run(
                ["cosy", f"{curr_function_file}"], timeout=300, capture_output=True
            )
        except subprocess.TimeoutExpired:
            pass

        with open(curr_output_file, "rt") as f:
            lines = f.readlines()
            stripped_lines = [line.strip("\n") for line in lines]
            result = ",".join(stripped_lines).replace(" ", "")

        os.remove(curr_output_file)
        os.remove(curr_function_file)

        if result == "None":
            return
        output = ",".join(input_array.astype(str)) + f",{result}\n"
        with LOCK:
            with open(RESULT_FOLDER / f"{filename}_model_data.csv", "a") as f:
                f.write(output)

    def generate_data_for_model(self, filename: str, worker_id: int) -> None:
        """Generate model data infinitely. Send Ctrl+C to stop."""
        for i in count():
            start = time.perf_counter()
            self.generate_datum_for_model(filename)
            print(
                f"{worker_id} : {i} done in {str(timedelta(seconds=time.perf_counter()-start))[2:7]}"
            )

    def parallel_data_gen(self, filename: str, n_processes: int = 8) -> None:
        """Generate model data in parallel."""
        with Pool(n_processes) as pool:
            [
                pool.apply_async(
                    self.generate_data_for_model, args=(filename, worker_id)
                )
                for worker_id in range(n_processes)
            ]

            while True:
                time.sleep(1)

    @staticmethod
    def _prep_function_file(
        process_id: int,
        lens_table: dict,
        template_lines: list[str],
        destination_file: "Path",
    ) -> None:
        """
        Preps function file for each process using a specified process id
        """
        identifiers = ["OpenF 11 'OUTPUT.txt'"] + [
            f"{lens_name}:=" for lens_name in lens_table.keys()
        ]
        replacements = [f"OpenF 11 'output_{process_id}.txt' 'UNKNOWN'"] + [
            f"{lens_name}:={voltage}" for lens_name, voltage in lens_table.items()
        ]

        create_file_from_template(
            list(zip(identifiers, replacements)),
            template_lines=template_lines,
            filepath=destination_file,
        )
