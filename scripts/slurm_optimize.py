import time, os, ssl, certifi
from datetime import timedelta

from cosy import *
from slappy import *


def main(messenger):
    start = time.perf_counter()

    optimizer = SpeemOptimizer(
        beam_parameters=[
            "intAng:=20*DEGRAD",
            "spotSize:=1*um2mm",
            "aper0D:=0.5",
            "V02:=V00",
            "V10:=V00",
        ],
    )
    optimizer.lens_limits = {
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
    #optimizer.objectives = (
    #    StandardObjectiveFunction.ANGLE_FILTER_APERTURE_0 * 10000,
    #    StandardObjectiveFunction.MINNED_SPATIAL_RESOLVED_DETECTOR,
    #)
    optimizer.objectives = (StandardObjectiveFunction.SPATIAL_FILTER_APERTURE_0 * 1000,
            StandardObjectiveFunction.MINNED_ANGLE_RESOLVED_DETECTOR)

    n_processors = int(os.getenv("SLURM_NTASKS_PER_NODE")) * int(os.getenv("SLURM_NNODES")) * 2
    optimizer.global_optimize(n_runs=n_processors, n_processors=n_processors)

    job_id = int(os.getenv("SLURM_JOB_ID"))
    optimizer.save_record(job_id)

    end = time.perf_counter()
    print(f"Optimization time taken - {timedelta(seconds=end - start)}")

    messenger.send_message(f"slurm optimization finished - {job_id}")


if __name__ == "__main__":
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    messenger = SlackMessenger(default_channel=Users.Jacob, ssl=ssl_context)

    try:
        main(messenger)
    except Exception as e:
        messenger.send_message(f"slurm_optimization failed with {e}")

