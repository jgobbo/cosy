import time, os, ssl, certifi
from datetime import timedelta

from cosy import *
from slappy import *


def main(messenger: SlackMessenger):
    start = time.perf_counter()

    mode = "angle"
    if mode == "angle":
        beam_parameters = [
            "intAng:=80*DEGRAD",
            "spotSize:=100*um2mm",
            "aper0D:=2",
            "V02:=V00",
            "V10:=V00",
        ]
        lens_limits = {
            Electrode.baseline: (5, 12),
            Electrode.V00: (0, 6000),
            Electrode.V01: (-100, 600),
            Electrode.V03: (-300, 600),
            Electrode.V11: (0, 550),
            Electrode.V12: (0, 550),
            Electrode.V13: (0, 550),
            Electrode.V21: (0, 50),
            Electrode.V22: (0, 50),
            Electrode.V31: (0, 50),
            Electrode.V32: (0, 50),
        }
        objectives = (
            StandardObjectiveFunction.SPATIAL_FILTER_APERTURE_0 * 10,
            StandardObjectiveFunction.MAXED_ANGLE_RESOLVED_DETECTOR,
        )
    elif mode == "spatial":
        beam_parameters = [
            "intAng:=5*DEGRAD",
            "spotSize:=50*um2mm",
            "aper0D:=0.05",
        ]
        lens_limits = {
            Electrode.baseline: (3, 6),
            Electrode.V00: (0, 6000),
            Electrode.V01: (-100, 550),
            Electrode.V03: (-300, 550),
            Electrode.V11: (0, 550),
            Electrode.V12: (0, 550),
            Electrode.V13: (0, 550),
            Electrode.V21: (0, 50),
            Electrode.V32: (0, 50),
        }
        objectives = (
            StandardObjectiveFunction.ANGLE_FILTER_APERTURE_0 * 10000,
            StandardObjectiveFunction.MINNED_SPATIAL_RESOLVED_DETECTOR,
        )

    job_id = int(os.getenv("SLURM_JOB_ID"))
    n_processors = int(os.getenv("SLURM_NTASKS_PER_NODE")) * int(
        os.getenv("SLURM_NNODES")
    )
    print(f"{n_processors=}")

    optimizer = SpeemOptimizer(
        beam_parameters=beam_parameters,
        lens_limits=lens_limits,
        objectives=objectives,
    )

    messenger.send_message(f"starting slurm optimization - {job_id} {mode}")
    optimizer.global_optimize(n_runs=n_processors, n_processors=n_processors)

    optimizer.save_record(job_id)

    end = time.perf_counter()
    print(f"Optimization time taken - {timedelta(seconds=end - start)}")

    messenger.send_message(f"slurm optimization finished - {job_id}")


if __name__ == "__main__":
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    messenger = SlackMessenger(default_user=Users.Jacob, ssl=ssl_context)

    try:
        main(messenger)
    except Exception as e:
        messenger.send_message(f"slurm_optimization failed with {e}")
        raise e
