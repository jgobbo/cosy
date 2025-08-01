"""
Following: M.H.Rashid "Simple analytical method to design electrostatic einzel lens" Proceedings of the DAE Symp. on Nucl. Phys. 56 (2011)
"""

import sympy as sp


def phi_gapped_apertures(z: float, V1: float, V2: float, S: float, D: float) -> float:
    """
    Calculates the electric potential of two apertures of diameter D and spacing S at the central axis
    location z (calculated from the center of the gap) with the first aperture at V1 and the second at V2.
    """
    z_plus = 2 * z + S
    z_minus = 2 * z - S
    return (V2 - V1) * D / (2 * sp.pi * S) * (
        z_plus / D * sp.atan2(z_plus, D) - z_minus / D * sp.atan2(z_minus, D)
    ) + (V1 + V2) / 2


def phi_einzel(z, V1, V2, S, D, L):
    """
    Calculates the electric potential of an einzel lens with aperture diameter D, spacing S,
    center aperture length L, and voltages V, V0 on the central, end apertures respectively.
    """
    d = (L + S) / 2
    return (
        -phi_gapped_apertures(z - d, V1, V2, S, D)
        + phi_gapped_apertures(z + d, V1, V2, S, D)
        + V1
    )


def force_constant(z, V0, V1, V2, S, D, L):
    """
    Calculates the force constant of a particle with initial potential V0 (kinetic energy / charge) at z in an einzel lens.
    """
    # z_sym = sp.symbols("z_sym")
    # phi_prime = sp.Derivative(phi_einzel(z_sym, V1, V2, S, D, L), z_sym, evaluate=True)
    # phi_prime_at_z = phi_prime.subs(z_sym, z)
    phi_prime = sp.Derivative(phi_einzel(z, V1, V2, S, D, L), z, evaluate=True)
    return sp.sqrt(3) * phi_prime / 4 / (V0 - phi_einzel(z, V1, V2, S, D, L))


def inv_f_i(force_constant, drift_length):
    """
    Calculates the focal length of a single thin lens
    """
    return force_constant * sp.sin(force_constant * drift_length)


def einzel_focal_length(
    V0: float,
    V1: float,
    V2: float,
    S: float,
    D: float,
    L: float,
    n_thin_lenses: int = 1000,
):
    """
    Calculates the focal length of an einzel lens with end potential V1, central potential V2, spacing S,
    diameter D, and center length L for a particle with initial potential V0 (kinetic energy / charge)
    """

    total_length = 2.5 * (L + 2 * S)
    drift_length = total_length / n_thin_lenses

    z = sp.symbols("z")
    force_constant_func = force_constant(z, V0, V1, V2, S, D, L)

    lam_inv_f_i = sp.lambdify(z, inv_f_i(force_constant_func, drift_length))

    inverse_focal_length = 0
    for i in range(n_thin_lenses):
        z_i = drift_length * (i + 1 / 2) - total_length / 2
        inverse_focal_length += lam_inv_f_i(z_i)
    return 1 / inverse_focal_length


def run_tests():
    def almost_equals(a, b, tol=1e-2):
        return abs(a - b) < tol

    def test(function, result):
        try:
            assert almost_equals(float(eval(function)), result)
        except Exception as e:
            print(
                f"{function} equals {float(eval(function))} but should equal {result}"
            )
            return False
        return True

    tests = [
        ("phi_gapped_apertures(-1e9, 12, 0, 1, 2)", 12),
        ("phi_gapped_apertures(1e9, 12, 0, 1, 2)", 0),
        ("phi_gapped_apertures(-1e9, 0, 12, 1, 2)", 0),
        ("phi_gapped_apertures(1e9, 0, 12, 1, 2)", 12),
        ("phi_einzel(0, 12, 0, 1, 2, 50)", 12),
        ("phi_einzel(0, 0, 12, 1, 2, 50)", 0),
        ("phi_einzel(1e9, 12, 0, 1, 2, 3)", 0),
        ("phi_einzel(-1e9, 12, 0, 1, 2, 3)", 0),
        ("phi_einzel(1e9, 0, 12, 1, 2, 3)", 12),
        ("phi_einzel(-1e9, 0, 12, 1, 2, 3)", 12),
    ]

    all_passed = True
    for function, result in tests:
        result = test(function, result)
        all_passed = all_passed and result

    if all_passed:
        print("Tests passed")


def diagnostic_plots():
    from matplotlib import pyplot as plt
    import numpy as np

    n_steps = 500

    S = 10  # cm
    D = 10  # cm
    L = 20  # cm
    total_length = 2.5 * (L + 2 * S)
    drift_length = total_length / n_steps

    V0 = 10  # kV
    V1 = 0  # kV
    V2 = 5  # kV

    ax: list[plt.Axes]
    fig, ax = plt.subplots(1, 3, figsize=(20, 8))
    z = np.linspace(-total_length / 2, total_length / 2, n_steps)

    ax[0].plot(z, np.array([phi_einzel(z_i, V1, V2, S, D, L) for z_i in z]))
    ax[0].set_title("Potential along principal axis")
    ax[0].set_xlabel("z [cm]")
    ax[0].set_ylabel("V [kV]")

    z_sym = sp.symbols("z_sym")
    lam_force_constant = sp.lambdify(z_sym, force_constant(z_sym, V0, V1, V2, S, D, L))

    ax[1].plot(z, np.array([lam_force_constant(z_i) for z_i in z]))
    ax[1].set_title("Force constant along principal axis")
    ax[1].set_xlabel("z [cm]")
    ax[1].set_ylabel(r"$\omega [cm^{-1}]$")

    ax[2].plot(
        z,
        np.array([inv_f_i(lam_force_constant(z_i), drift_length) * 1000 for z_i in z]),
    )
    ax[2].set_title("Inverse focal length for thin lenses along principal axis")
    ax[2].set_xlabel("z [cm]")
    ax[2].set_ylabel(r"$1/f_i [cm^{-1}]$")
    plt.show()

    print(einzel_focal_length(10, 0, 5, 10, 10, 20, 866))
    # run_tests()


def operating_voltage(
    focal_length: float,
    kinetic_energy: float,
    diameter: float,
    spacing: float,
    length: float,
) -> float:
    from functools import partial
    from scipy.optimize import minimize_scalar

    # objective_function = partial(
    #     einzel_focal_length, V0=kinetic_energy, V1=0, S=spacing, D=diameter, L=length
    # )

    objective_function = (
        lambda V: (
            einzel_focal_length(kinetic_energy, 0, V, spacing, diameter, length)
            - focal_length
        )
        ** 2
    )

    result = minimize_scalar(objective_function, bounds=(0, 10), method="bounded")

    print(
        f"operating voltage for focal length {einzel_focal_length(kinetic_energy, 0, result.x, spacing, diameter, length)} is {result.x} in same units as kinetic energy"
    )


if __name__ == "__main__":
    operating_voltage(
        focal_length=100, kinetic_energy=2, diameter=4.3, spacing=2.4, length=1.2
    )
