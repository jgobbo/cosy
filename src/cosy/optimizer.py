import os, time, subprocess, json, re, random, shutil
from dataclasses import asdict
from typing import TextIO, TYPE_CHECKING
from pathlib import Path
from datetime import timedelta
from copy import deepcopy
import numpy as np
from colorama import Fore, Style
from multiprocessing import current_process
from pathos.multiprocessing import ProcessingPool

from .constants import HARDWARE_RESTRICTED_LENS_LIMITS, FOX_DIR, RESULTS_DIR, Electrode
from .utils import (
    lis_purge,
    edit_lines,
    create_file_from_template,
    process_file,
    LensTable,
)
from .objective import ObjectiveFunction

from pybads import BADS

from scipy.optimize import minimize


if TYPE_CHECKING:
    from slappy import *
    from pybads import OptimizeResult


__all__ = [
    "SpeemOptimizer",
    "LensTable",
]

FUNCTION_FILE = FOX_DIR / "Objective.fox"
TEMPLATE_FILE = FOX_DIR / "ObjectiveTemplate.fox"
OBJECTIVE_FILE = FOX_DIR / "objective.txt"
RAYTRACING_FILE = FOX_DIR / "RaytracingTemplate.fox"
RECORD_FILE = FOX_DIR / "optimization_record.json"


class SpeemOptimizer:
    template_file: Path = TEMPLATE_FILE
    objective_file: Path = OBJECTIVE_FILE
    function_file: Path = FUNCTION_FILE
    record_file: Path = RECORD_FILE
    raw_template_lines: list[str] = None
    template_lines: list[str] = None
    map_procedure: str = None
    record: list = []

    def __init__(
        self,
        objectives: list["ObjectiveFunction"] = None,
        lens_limits: dict[Electrode, list] | None = None,
        default_lens_table: LensTable = LensTable(),
        beam_parameters: list[str] = None,
        messenger: "SlackMessenger" = None,
    ) -> None:
        os.chdir(FOX_DIR)
        self._default_lens_table = default_lens_table
        self._beam_parameters = beam_parameters
        self.lens_limits = (
            HARDWARE_RESTRICTED_LENS_LIMITS if lens_limits is None else lens_limits
        )

        with open(self.template_file, "rt") as f:
            self.raw_template_lines = f.readlines()
        self.objectives = objectives

        self.messenger = messenger
        if messenger is not None and messenger.default_user is None:
            print("Messenger doesn't have a default user. No messages will be sent.")
            self.messenger = None

    def _update_template(
        self,
    ) -> list[str]:
        replacements = []

        replacements.append(
            (
                "BEAMREDEFINITIONS",
                (
                    self.beam_parameters + ["RedefineBeam"]
                    if self.beam_parameters is not None
                    else None
                ),
            )
        )

        for lens_name, default_voltage in self.default_lens_table.items():
            replacements.append((f"{lens_name}:=", f"{lens_name}:={default_voltage}"))

        objective_calls = []
        objective_functions = []
        for objective in self.objectives:
            objective_functions += objective.function
            objective_calls.append(f"GenerateMap voltages sampleZ {objective.endpoint}")
            objective_calls.append(f"obj:=obj+{objective.call}")
        replacements.append(("OBJECTIVE_FUNCTIONS;", objective_functions))
        replacements.append(("OBJECTIVE;", objective_calls))

        new_lines = edit_lines(
            replacements=replacements, template_lines=self.raw_template_lines
        )
        return new_lines

    def _update_map_procedure(self) -> None:
        if not self.objectives:
            return
        elif "Angle" in self.objectives[-1].call:
            self.map_procedure = "ArConversionMap"
        elif "Spatial" in self.objectives[-1].call:
            self.map_procedure = "SrConversionMap"
        else:
            self.map_procedure = None

    @property
    def objectives(self) -> list[ObjectiveFunction]:
        return self._objectives

    @objectives.setter
    def objectives(
        self, objectives: list[ObjectiveFunction] | ObjectiveFunction
    ) -> None:
        if objectives is None:
            objectives = []
        elif isinstance(objectives, ObjectiveFunction):
            objectives = [objectives]

        self._objectives = objectives
        self._update_map_procedure()
        self.template_lines = self._update_template()

    @property
    def default_lens_table(self) -> dict[str, float]:
        return self._default_lens_table

    @default_lens_table.setter
    def default_lens_table(self, default_lens_table: dict[str, float]) -> None:
        self._default_lens_table = default_lens_table
        self.template_lines = self._update_template()

    @property
    def beam_parameters(self) -> list[str]:
        return self._beam_parameters

    @beam_parameters.setter
    def beam_parameters(self, beam_parameters: list[str]) -> None:
        self._beam_parameters = beam_parameters
        self.template_lines = self._update_template()

    def objective(
        self, table_values: np.ndarray | list, process_id: int = None
    ) -> float:
        if isinstance(table_values, list):
            table_values = np.array(table_values)

        start = time.perf_counter()

        lens_table = LensTable(
            zip(list(self.lens_limits.keys()), table_values.flatten())
        )
        # print(f"{Fore.RED}{lens_table}{Style.RESET_ALL}")

        # this should prevent race conditions regardless of the number of processes
        if process_id is None:
            process_id= random.randrange(0, int(1e4))
        curr_objective_file = process_file(process_id, self.objective_file)
        curr_function_file = process_file(process_id, self.function_file)
        for _ in range(3):
            if curr_objective_file.exists() or curr_function_file.exists():
                process_id = random.randrange(0, int(1e4))
                curr_objective_file = process_file(process_id, self.objective_file)
                curr_function_file = process_file(process_id, self.function_file)
            else:
                break

        # prepping objective output file in case cosy crashes and outputs nothing
        with open(curr_objective_file, "wt") as f:
            f.write("1e9")

        self._prep_function_file(
            process_id,
            lens_table,
            template_lines=self.template_lines,
            destination_file=curr_function_file,
        )
        try:
            subprocess.call(
                ["cosy", curr_function_file.name],
                stdout=open(os.devnull, "wb"),
                timeout=900,
            )
        except subprocess.TimeoutExpired:
            pass
        with open(curr_objective_file, "rt") as f:
            obj = float(f.readline())

        try:
            os.remove(curr_objective_file)
        except FileNotFoundError:
            pass
        try:
            os.remove(curr_function_file)
        except FileNotFoundError:
            pass

        end = time.perf_counter()
        #print(
        #  f"{Fore.GREEN}{process_id} obj: {obj:.2e} with {lens_table} in "
        #  f"{str(timedelta(seconds=end-start))[2:7]}{Style.RESET_ALL}"
        #)
        return obj

    def EGO_objective(self, table_values: np.ndarray):
        return [self.objective(table_values)]

    @staticmethod
    def _prep_function_file(
        process_id: int,
        lens_table: dict,
        template_lines: list[str] = None,
        destination_file: Path = FUNCTION_FILE,
    ) -> None:
        """
        Preps function file for each process using a specified process id
        """
        identifiers = ["OpenF 11 'OBJECTIVE.txt'"] + [
            f"{lens_name}:=" for lens_name in lens_table.keys()
        ]
        replacements = [f"OpenF 11 'objective_{process_id}.txt' 'UNKNOWN'"] + [
            f"{lens_name}:={voltage}" for lens_name, voltage in lens_table.items()
        ]

        create_file_from_template(
            list(zip(identifiers, replacements)),
            template_lines=template_lines,
            filepath=destination_file,
        )

    def _get_aberrations(self, lens_table: LensTable) -> list[str]:
        process_id = random.randrange(0,int(1e4))
        aberrations_file = f"aberrations_{process_id}.txt"
        common_identifiers = [f"{lens_name}:=" for lens_name in lens_table.keys()] + [
            "OBJECTIVE_FUNCTIONS;",
            "BEAMREDEFINITIONS",
            "OpenF 11 'OBJECTIVE.txt'",
            "Write 11 S(obj);",
        ]
        common_replacements = [
            f"{lens_name}:={voltage}" for lens_name, voltage in lens_table.items()
        ] + [
            None,
            (
                self.beam_parameters + ["RedefineBeam"]
                if self.beam_parameters is not None
                else None
            ),
            f"OpenF 11 '{aberrations_file}' 'UNKNOWN'",
            "PA 11",
        ]

        aberrations = {}
        for objective in self.objectives:
            # avoid reading old files if call fails
            try:
                os.remove(aberrations_file)
            except OSError:
                pass

            filepath = FOX_DIR / f"Aberrations_Temp_{objective.endpoint}_{process_id}.fox"
            print(f"Getting aberrations at {objective.endpoint}.")
            identifiers = common_identifiers + [f"OBJECTIVE;"]
            replacements = common_replacements + [
                f"GenerateMap voltages sampleZ {objective.endpoint}"
            ]
            create_file_from_template(
                list(zip(identifiers, replacements)),
                template_lines=self.raw_template_lines,
                filepath=filepath,
            )
            subprocess.call(["cosy", filepath.name], stdout=open(os.devnull, "wb"))
            os.remove(filepath)
            with open(aberrations_file, "rt") as f:
                aberrations[objective.endpoint] = self._format_aberrations(f)

        return aberrations

    def _format_aberrations(self, aberrations_file: TextIO) -> list[list[str]]:
        item_length = 14
        n_items_per_line = 5
        all_aberrations = []
        for line in aberrations_file.readlines()[:-1]:
            all_aberrations.append(
                [
                    line[1 + i * item_length : 1 + (i + 1) * item_length]
                    for i in range(n_items_per_line)
                ]
                + [line[item_length * n_items_per_line + 2 : -1]]
            )

        return all_aberrations

    def _objective_parameters(self) -> dict:
        return {
            "default_lens_table": self.default_lens_table,
            "lens_limits": self.lens_limits,
            "beam_parameters": self.beam_parameters,
            "objectives": [asdict(objective) for objective in self.objectives],
        }

    def _update_record(
        self,
        optimal_objective: float,
        optimal_lens_table: LensTable,
        optimization_type: str,
        all_optimal_objectives: list[float] | None = None,
    ) -> None:
        optimization_record = self._objective_parameters()
        optimization_record["optimal_objective"] = optimal_objective
        optimization_record["optimal_lens_table"] = optimal_lens_table
        optimization_record["aberrations"] = self._get_aberrations(optimal_lens_table)
        optimization_record["optimization_type"] = optimization_type
        if all_optimal_objectives is not None:
            optimization_record["all_optimal_objectives"] = all_optimal_objectives
        self.record.append(optimization_record)

    def save_record(self, id: int = None) -> None:
        output = json.dumps(self.record, indent=4)

        # making lowest level lists into single lines
        output_list = output.split("\n")
        pattern_started = False
        active = False
        for i, line in enumerate(output_list):
            output_list[i] = line + "\n"
            # I'm sorry this is so hideous
            if ("lens_limits" in line) or ("aberrations" in line):
                active = True
            elif (active is True) and ("}" in line):
                active = False
            if "[" in line and active:
                pattern_start = i
                pattern_started = True
            elif "]" in line and pattern_started:
                pattern_started = False

                output_list[pattern_start] = output_list[pattern_start].strip("\n")
                output_list[pattern_start + 1 : i] = [
                    re.sub(r"\s+", "", line)
                    for line in output_list[pattern_start + 1 : i]
                ]
                output_list[i] = re.sub(r"[ \t]+", "", output_list[i])
        output = "".join(output_list)

        filepath = (
            self.record_file
            if id is None
            else RESULTS_DIR / f"optimization_record_{id}.json"
        )
        if not filepath.parent.exists():
            filepath.parent.mkdir()
        with open(filepath, "w") as f:
            f.write(output)

    def dummy_objective(self, table_values: np.ndarray) -> float:
        result = abs(table_values.sum())
        print(f"{Fore.GREEN}{result}:{table_values}{Style.RESET_ALL}")
        return result

    def global_optimize(
        self, n_runs: int = 30, n_processes: int = 12, **kwargs
    ) -> None:
        """
        Run a global optimization

        Args
        ----
        n_runs: int
            Number of independent optimizations to run. The global optimization result
            is random depending on the starting points randomly sampled. It's best to
            take the smallest result of multiple optimization runs.
        n_processes: int
            Number of optimizations to run in parallel. You can drastically decrease the
            full optimization time by running more processes up to the limit of your
            cpu. Running too many processes can slow each one down enough to cause
            timeouts and ruin the optimization.
        """
        voltage_limits = np.array(list(self.lens_limits.values()))

        hard_lower_bounds = voltage_limits[:, 0]
        hard_upper_bounds = voltage_limits[:, 1]

        plausible_bounds: dict = kwargs.get("plausible_limits", None)
        if plausible_bounds is None:
            bound_widths = hard_upper_bounds - hard_lower_bounds
            plausible_lower_bounds = hard_lower_bounds + 0.05 * bound_widths
            plausible_upper_bounds = hard_upper_bounds - 0.05 * bound_widths
        else:
            plausible_bounds = np.array(list(plausible_bounds.values()))
            plausible_lower_bounds = plausible_bounds[:, 0]
            plausible_upper_bounds = plausible_bounds[:, 1]

        def worker(process_id: int | None = None):
            start = time.perf_counter()
            print(f"starting worker {process_id}")
            bads = BADS(
                    fun=lambda x: self.objective(x),
                lower_bounds=voltage_limits[:, 0],
                upper_bounds=voltage_limits[:, 1],
                plausible_lower_bounds=plausible_lower_bounds,
                plausible_upper_bounds=plausible_upper_bounds,
                options={
                    "display": "off",
                    "uncertainty_handling": False,
                    "random_seed": random.randint(0, int(1e9)),
                },
            )
            result: "OptimizeResult" = bads.optimize()
            optimal_objective = result.fval
            optimal_lens_table = result.x
            print(
                f"run {process_id} done with obj={optimal_objective} in "
                f"{str(timedelta(seconds=(time.perf_counter()-start)))}"
            )
            return optimal_objective, optimal_lens_table

        with ProcessingPool(processes=n_processes) as pool:
            async_result = pool.amap(worker, range(n_runs))
            results = async_result.get()

        optimal_objectives, optimal_lens_tables = zip(*results)
        optimal_objectives = list(optimal_objectives)
        optimal_lens_tables = list(optimal_lens_tables)
        print("optimal_objectives:")
        print(optimal_objectives)

        min_index = optimal_objectives.index(min(optimal_objectives))

        optimal_objective = optimal_objectives[min_index]
        optimal_lens_table = optimal_lens_tables[min_index]
        optimal_lens_table = LensTable(
            zip(list(self.lens_limits.keys()), optimal_lens_table)
        )

        full_optimal_lens_table = deepcopy(self.default_lens_table)
        full_optimal_lens_table.update(optimal_lens_table)

        self._update_record(
            optimal_objective,
            full_optimal_lens_table,
            "global",
            all_optimal_objectives=optimal_objectives,
        )
        self.default_lens_table = full_optimal_lens_table
        print(f"best objective: {optimal_objective} achieved with {optimal_lens_table}")

        lis_purge()

        if self.messenger is not None:
            self.messenger.send_message(
                f"global optimization complete. best objective: {optimal_objective} "
                f"achieved with {optimal_lens_table}"
            )

    def local_optimize(
        self,
        method: str = "Nelder-Mead",
        tol: float = 1.0,
        max_iter: int = None,
    ) -> None:
        starting_point = []
        for lens_name in self.lens_limits.keys():
            starting_point.append(self.default_lens_table[lens_name])

        result = minimize(
            self.objective,
            starting_point,
            method=method,
            tol=tol,
            bounds=list(self.lens_limits.values()),
            options={"maxiter": max_iter},
        )
        optimal_objective = result["fun"]
        optimal_lens_table = LensTable(zip(list(self.lens_limits.keys()), result["x"]))
        full_optimal_lens_table = deepcopy(self.default_lens_table)
        full_optimal_lens_table.update(optimal_lens_table)
        self._update_record(
            optimal_objective, full_optimal_lens_table, f"local-{method}"
        )
        self.default_lens_table = full_optimal_lens_table
        print(
            f"{optimal_objective:.3e} achieved with final lens table: "
            f"{optimal_lens_table}"
        )

        if self.messenger is not None:
            self.messenger.send_message(
                f"local optimization complete. best objective: {optimal_objective} "
                f"achieved with {optimal_lens_table}"
            )

    def generate_data_for_metric(self, n: int, filename: str) -> None:
        result_folder = RESULTS_DIR / "simulation_data"

        self.record.append(self._objective_parameters())
        self.save_record(result_folder / f"{filename}_metric_metadata.json")
        with open(result_folder / f"{filename}_metric_data.csv", "x") as f:
            for _ in range(n):
                lens_table = np.array(
                    [
                        random.uniform(lens_limit[0], lens_limit[1])
                        for lens_limit in self.lens_limits.values()
                    ]
                )
                objective = self.objective(lens_table)

                output = ",".join(lens_table.astype(str)) + f",{objective}\n"
                f.write(output)

    def raytracing(
        self,
        lens_table: dict = None,
        start: str = "sampleZ",
        end: str = "detZ",
    ) -> None:
        lens_table = self.default_lens_table if lens_table is None else lens_table

        print(f"raytracing with {lens_table}")
        filepath = self._prep_raytracing_file(lens_table, start=start, end=end)
        subprocess.call(["cosy", filepath.name])
        os.remove(filepath)

        if self.messenger is not None:
            self.messenger.send_message(f"raytracing complete with {lens_table}")

    def _prep_raytracing_file(
        self,
        lens_table: dict,
        start: str,
        end: str,
    ) -> Path:
        with open(RAYTRACING_FILE, "rt") as f:
            template_lines = f.readlines()

        identifiers = (
            ["BEAMREDEFINITIONS"]
            + ["RayTracing sampleZ detZ"]
            + [f"{lens_name}:=" for lens_name in lens_table.keys()]
            + ["CONVERSIONMAP"]
        )
        beam_parameters = (
            self.beam_parameters + ["RedefineBeam"]
            if self.beam_parameters is not None
            else None
        )
        conversion_map = (
            f"{self.map_procedure} {start} {end}"
            if self.map_procedure is not None
            else None
        )
        replacements = (
            [beam_parameters]
            + [f"RayTracing {start} {end}"]
            + [f"{lens_name}:={voltage}" for lens_name, voltage in lens_table.items()]
            + [conversion_map]
        )

        destination_file = FOX_DIR / "Raytracing_Temp.fox"

        create_file_from_template(
            list(zip(identifiers, replacements)),
            template_lines=template_lines,
            filepath=destination_file,
        )

        return destination_file
