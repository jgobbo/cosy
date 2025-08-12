import time, os, ssl, certifi
from datetime import timedelta

from cosy import *
from slappy import *


def main(messenger):
    start = time.perf_counter()

    optimizer = SpeemOptimizer(
        beam_parameters=[
            "intAng:=5*DEGRAD",
            "spotSize:=50*um2mm",
            "aper0D:=0.125",
            "V02:=V00",
            "V10:=V00",
        ],
    )
    optimizer.lens_limits = {
        Electrode.baseline: (-0.5, 10),
        Electrode.V00: (0, 6000),
        Electrode.V01: (-100, 550),
        Electrode.V03: (-300, 550),
        Electrode.V11: (0, 550),
        Electrode.V12: (0, 550),
        Electrode.V13: (0, 550),
        Electrode.V21: (0, 50),
        Electrode.V32: (0, 50),
    }
    optimizer.objectives = (
        StandardObjectiveFunction.ANGLE_RESOLVED_APERTURE_0 * 10000,
        StandardObjectiveFunction.MINNED_SPATIAL_RESOLVED_DETECTOR,
    )
    n_processors = int(os.getenv("SLURM_NTASKS_PER_NODE")) * int(os.getenv("SLURM_NNODES"))
    optimizer.global_optimize(n_runs=n_processors, n_processors=n_processors)

    optimizer.save_record()

    end = time.perf_counter()
    print(f"Optimization time taken - {timedelta(seconds=end - start)}")

    messenger.send_message("slurm optimization finished")


if __name__ == "__main__":
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    messenger = SlackMessenger(default_channel=Users.Jacob, ssl=ssl_context)

    try:
        main(messenger)
    except Exception as e:
        messenger.send_message(f"slurm_optimization failed with {e}")

