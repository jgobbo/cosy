import time
from datetime import timedelta

from cosy.constants import Electrode
from cosy.optimizer import *
from cosy.objective import StandardObjectiveFunction

from slappy import *


def main():
    start = time.perf_counter()
    messenger = SlackMessenger(default_channel=Users.Jacob)
    optimizer = SpeemOptimizer(
        beam_parameters=[
            "intAng:=15*DEGRAD",
            "spotSize:=1*um2mm",
            "aper0D:=100*um2mm",
        ],
        messenger=messenger,
    )
    optimizer.lens_limits = {
        Electrode.V00: (0, 600),
        Electrode.V01: (-100, 600),
        Electrode.V02: (0, 600),
        Electrode.V03: (-300, 600),
        Electrode.V10: (0, 600),
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
    optimizer.default_lens_table = {
        electrode: value
        for electrode, value in zip(
            optimizer.lens_limits.keys(),
            [
                5.12350486e02,
                4.98770783e01,
                5.87030222e01,
                -1.10442296e01,
                2.79396772e-08,
                3.57338013e02,
                1.38668750e02,
                2.09217625e02,
                1.36313414e02,
                1.72192935e02,
                1.68942234e02,
                1.72276139e02,
                2.60148714e01,
                1.33649146e02,
            ],
        )
    }

    optimizer.objectives = (
        StandardObjectiveFunction.SPATIAL_FILTER_APERTURE_0 * 1000,
        StandardObjectiveFunction.ANGLE_RESOLVED_DETECTOR,
    )
    # optimizer.global_optimize()
    optimizer._update_record(
        132.6836283,
        optimizer.default_lens_table,
        "global",
        all_optimal_objectives=[
            152.2159141764564,
            152.5215527626439,
            151.7043298138927,
            152.4603218083171,
            152.2550560213256,
            152.381527495086,
            152.4984672675529,
            151.8402954905492,
            152.3249127086368,
            151.7357863137372,
            152.2656349293029,
            152.3990795961899,
            141.2260834746394,
            152.342186059884,
            152.2388351493432,
            152.2206203629726,
            152.4850150120328,
            152.4808522233846,
            152.2117172254304,
            151.6184598652581,
            132.6836283345823,
            152.1062518948213,
            152.5314168561734,
            136.2620721226136,
            152.2457654586619,
            152.5552303637919,
            151.4527361975324,
            152.481377354097,
            151.714048569987,
            151.6661194101292,
        ],
    )

    optimizer.save_record()
    optimizer.map_procedure = None
    optimizer.raytracing()

    print(f"Optimization time taken - {timedelta(seconds=time.perf_counter() - start)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_messenger = SlackMessenger(default_channel=Users.Jacob)
        error_messenger.send_message(f"Optimization failed with error: {e}")
        raise
