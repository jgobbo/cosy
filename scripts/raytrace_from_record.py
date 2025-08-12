import json

from cosy import SpeemOptimizer, FOX_DIR
from cosy.objective import ObjectiveFunction
from slappy import SlackMessenger, Users


def main() -> None:
    messenger = SlackMessenger(default_channel=Users.Jacob)

    with open(FOX_DIR / "optimization_record.json") as f:
        optimization_record = json.load(f)[-1]

    objectives = [
        ObjectiveFunction(**objective_dict)
        for objective_dict in optimization_record["objectives"]
    ]

    optimizer = SpeemOptimizer(
        objectives=objectives,
        beam_parameters=optimization_record["beam_parameters"],
        default_lens_table=optimization_record["optimal_lens_table"],
        messenger=messenger,
    )

    optimizer.raytracing()


if __name__ == "__main__":
    main()
