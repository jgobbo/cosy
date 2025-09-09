from cosy import SpeemOptimizer, Electrode
from slappy import SlackMessenger, Users


def main() -> None:
    messenger = SlackMessenger(default_user=Users.Jacob)

    beam_parameters = [
        "intAng:=15*DEGRAD",
        "spotSize:=1*um2mm",
        "aper0D:=10*um2mm",
    ]
    map_procedure = None
    lens_table = {
        Electrode.V00: 70.3,
        Electrode.V01: 599.6,
        Electrode.V02: 566.5,
        Electrode.V03: -205.7,
        Electrode.V10: 573.7,
    }

    optimizer = SpeemOptimizer(
        beam_parameters=beam_parameters,
        messenger=messenger,
        default_lens_table=lens_table,
    )
    optimizer.map_procedure = map_procedure

    optimizer.raytracing(end="aper0Z")


if __name__ == "__main__":
    main()
