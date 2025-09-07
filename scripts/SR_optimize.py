import time
from datetime import timedelta

from cosy import *
from slappy import *


def main():
    start = time.perf_counter()
    messenger = SlackMessenger(default_channel=Users.Jacob)

    optimizer = SpeemOptimizer(
        beam_parameters=[
            "intAng:=5*DEGRAD",
            "spotSize:=100*um2mm",
            "aper0D:=0.05",
            "V02:=V00",
            "V10:=V00",
        ],
        messenger=messenger,
    )
    optimizer.lens_limits = {
        Electrode.baseline: (3, 8),
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
        StandardObjectiveFunction.ANGLE_FILTER_APERTURE_0 * 10000,
        StandardObjectiveFunction.MINNED_SPATIAL_RESOLVED_DETECTOR,
    )
    optimizer.global_optimize(n_runs=50)

    optimizer.save_record()
    optimizer.raytracing()

    end = time.perf_counter()
    print(f"Optimization time taken - {timedelta(seconds=end - start)}")


if __name__ == "__main__":
    # main()
    try:
        main()
    except Exception as e:
        error_messenger = SlackMessenger(default_channel=Users.Jacob)
        error_messenger.send_message(f"Optimization failed with error: {e}")
        raise
