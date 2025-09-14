import time, os, ssl, certifi
from datetime import timedelta

from cosy import *
from slappy import *


def main(messenger: SlackMessenger):
    start = time.perf_counter()

    mode="spatial"
    if mode=="angle":
        beam_parameters = [
            "intAng:=15*DEGRAD",
            "spotSize:=1*um2mm",
            "aper0D:=0.1",
            "V02:=V00",
            "V10:=V00",
        ]
        lens_limits = {
            Electrode.V00: (0, 6000),
            Electrode.V01: (-100, 600),
            Electrode.V03: (-300, 600),
            Electrode.V11: (0, 550),
            Electrode.V12: (0, 550),
            Electrode.V13: (0, 550),
            Electrode.V21: (0, 300),
            Electrode.V22: (0, 300),
            Electrode.V23: (0, 300),
            Electrode.V31: (0, 300),
            Electrode.V32: (0, 300),
            Electrode.V33: (0, 300),
        }
        objectives = (
            StandardObjectiveFunction.SPATIAL_FILTER_APERTURE_0 * 1000,
            StandardObjectiveFunction.MINNED_ANGLE_RESOLVED_DETECTOR,
        )
    elif mode=="spatial":
        beam_parameters=[
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
    n_processors = (
        int(os.getenv("SLURM_NTASKS_PER_NODE")) * int(os.getenv("SLURM_NNODES"))
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
