import time
from datetime import timedelta

from cosy.constants import Electrode
from cosy.optimizer import *
from cosy.objective import StandardObjectiveFunction

from slappy import *


def main():
    start = time.perf_counter()
    messenger = SlackMessenger(default_user=Users.Jacob)
    optimizer = SpeemOptimizer(
        beam_parameters=[
            "intAng:=30*DEGRAD",
            "spotSize:=100*um2mm",
            "aper0D:=2",
            "V02:=V00",
            "V03:=V00",
            "V10:=V00",
        ],
        messenger=messenger,
    )
    optimizer.lens_limits = {
        Electrode.V00: (0, 600),
        Electrode.V01: (-100, 600),
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

    optimizer.objectives = (
        StandardObjectiveFunction.CLEAR_APERTURE_0 * 10,
        StandardObjectiveFunction.MINNED_ANGLE_RESOLVED_DETECTOR,
    )
    optimizer.global_optimize(n_processes=7)

    optimizer.save_record()
    optimizer.raytracing()

    print(f"Optimization time taken - {timedelta(seconds=time.perf_counter() - start)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_messenger = SlackMessenger(default_user=Users.Jacob)
        error_messenger.send_message(f"Optimization failed with error: {e}")
        raise
