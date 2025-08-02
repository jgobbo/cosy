from math import sqrt

ELECTRON_MASS = 9.1093837015e-31  # kg
EV_TO_JOULES = 1.6021e-19
LENS_LENGTH = 784 / 1000  # m
NS_PER_PIXEL = 0.2469
LASER_DELAY = 934  # ns
PIXEL_MAX = 4096 // 8


def main():
    mode = 0
    while mode != 3:
        mode = int(
            input(
                "Enter 0 for time from energy, 1 for energy from time, 2 for energy "
                "from delay, or 3 to exit: "
            )
        )

        if mode == 0:
            energy = float(input("What energy electron (eV)?  "))
            velocity = sqrt(2 * (energy * EV_TO_JOULES) / ELECTRON_MASS)
            print(velocity)
            tof = LENS_LENGTH / velocity * 1e9  # ns
            print(f"tof = {tof:.4f}ns")
        elif mode == 1:
            tof = float(input("What electron tof (ns)?  ")) * 1e-9
            velocity = LENS_LENGTH / tof
            energy = ELECTRON_MASS * (velocity**2) / 2 / EV_TO_JOULES
            print(f"energy = {energy:.4f}ev")
        # this mode may be broken or needs calibration
        elif mode == 2:
            peak_pixel = int(input("What pixel is the peak at?  "))
            raw_delay = float(input("What is the delay set at (ns)?  "))
            peak_time = (PIXEL_MAX - peak_pixel) * NS_PER_PIXEL
            delay = raw_delay + peak_time - LASER_DELAY  # ns
            tof = delay * 1e-9  # s
            velocity = LENS_LENGTH / tof
            energy = ELECTRON_MASS * velocity**2 / 2 / EV_TO_JOULES
            print(f"energy = {energy:.4f}eV")


if __name__ == "__main__":
    main()
