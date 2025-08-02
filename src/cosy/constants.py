from pathlib import Path
from enum import StrEnum

FOX_DIR = Path(__file__).parent.parent.absolute() / "fox"
RESULTS_DIR = Path(__file__).parent.parent.parent.absolute() / "results"


class Electrode(StrEnum):
    baseline = "baseline"
    V00 = "V00"
    V01 = "V01"
    V02 = "V02"
    V03 = "V03"
    V10 = "V10"
    V11 = "V11"
    V12 = "V12"
    V13 = "V13"
    V21 = "V21"
    V22 = "V22"
    V23 = "V23"
    V31 = "V31"
    V32 = "V32"
    V33 = "V33"


# all in mm
APER_0_Z = 108.33694
APER_0_D = 2.5
APER_1_Z = 274.68737
APER_1_D = 30
SAMPLE_Z = 0
DET_Z = 784.03886
DET_D = 25

HARDWARE_RESTRICTED_LENS_LIMITS = {
    Electrode.baseline: [0, 12],
    Electrode.V00: [0, 600],
    Electrode.V01: [0, 600],
    Electrode.V02: [0, 600],
    Electrode.V03: [0, 600],
    Electrode.V10: [0, 600],
    Electrode.V11: [0, 600],
    Electrode.V12: [0, 600],
    Electrode.V13: [0, 600],
    Electrode.V21: [0, 600],
    Electrode.V22: [0, 600],
    Electrode.V23: [0, 600],
    Electrode.V31: [0, 600],
    Electrode.V32: [0, 600],
    Electrode.V33: [0, 600],
}

CENTROIDS = {
    Electrode.V00: 1.278,  # very inaccurate
    Electrode.V01: 8.225,
    Electrode.V02: 21.715,
    Electrode.V03: 87.350,
    Electrode.V10: 131.815,
    Electrode.V11: 188.352,
    Electrode.V12: 197.327,
    Electrode.V13: 242.296,  # requires very long focal length
    Electrode.V21: 343.117,
    Electrode.V22: 375.854,
    Electrode.V23: 512.205,  # requires very long focal length
    Electrode.V31: 648.546,
    Electrode.V32: 681.312,
    Electrode.V33: 729.946,  # exceptionally inaccurate, don't use
}
