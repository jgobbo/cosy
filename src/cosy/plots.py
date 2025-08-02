from pathlib import Path
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle

from .constants import (
    FOX_DIR,
    DET_D,
    APER_0_D,
    APER_1_D,
    SAMPLE_Z,
    DET_Z,
    APER_0_Z,
    APER_1_Z,
)


__all__ = ["conversion_map", "plot_rays", "plot_lens"]

M_TO_MM = 1000


def conversion_map(
    root: Path = FOX_DIR,
    error_bars: bool = False,
    ax: plt.Axes = None,
) -> tuple[plt.Figure, plt.Axes]:
    # initial parameter setup
    if ax is None:
        fig, ax = plt.subplots(figsize=(15, 7))
    else:
        fig = plt.gcf()
    with open(root / "conversionMap.txt", "rt") as f:
        header = f.readline()
        angle_resolved = header[10:13] == "ang"
    energy: np.ndarray
    resolved: np.ndarray
    other: np.ndarray
    radius: np.ndarray
    time: np.ndarray
    energy, resolved, other, radius, time = np.loadtxt(
        root / "conversionMap.txt", skiprows=1, unpack=True
    )

    n_other = 1
    temp = resolved[0]
    while temp == resolved[n_other]:
        n_other += 1
    n_resolved = 1
    temp = energy[0]
    while temp == energy[n_resolved * n_other]:
        n_resolved += 1
    n_energies = energy.shape[0] // (n_resolved * n_other)
    if energy.shape[0] != n_energies * n_resolved * n_other:
        raise ValueError("Data dimensions don't multiply correctly.")

    if radius[-2] < 0:
        radius[:] = -radius[:]
        label_sign = "-"
    else:
        label_sign = ""

    if angle_resolved:
        title = f"spotsize = {other[n_other-1] - other[0]:0.2f}um"
    else:
        title = f"initial solid-angle = {other[n_other-1] - other[0]:0.2f}{chr(176)}"
    vertical_plots = np.ndarray((n_resolved, n_energies, 2), float)
    horizontal_plots = np.ndarray((n_energies, n_resolved, 2), float)
    x_width = radius.max() - radius.min()
    y_width = time.max() - time.min()
    side_text_buffer = max(x_width, DET_D / 2) / 20
    bottom_text_buffer = y_width / 20

    rs = []
    ts = []
    r_errors: list[list] = []
    t_errors = []
    for energy_i in range(n_energies):
        for resolved_i in range(n_resolved):
            row = (
                (n_resolved * n_other) * energy_i + n_other * resolved_i + n_other // 2
            )
            rs.append(r := radius[row])
            ts.append(t := time[row])

            negative_radial_error = radius[row - n_other // 2] - r
            positive_radial_error = radius[row + n_other // 2] - r
            if negative_radial_error < 0 and positive_radial_error > 0:
                r_errors.append([-negative_radial_error, positive_radial_error])
            elif negative_radial_error > 0 and positive_radial_error < 0:
                r_errors.append([-positive_radial_error, negative_radial_error])
            elif negative_radial_error < 0 and positive_radial_error < 0:
                r_errors.append(
                    [max(-negative_radial_error, -positive_radial_error), 0]
                )
            else:
                r_errors.append([0, max(negative_radial_error, positive_radial_error)])

            t_errors.append(
                [
                    t - min(time[row - n_other // 2 : row + n_other // 2]),
                    max(time[row - n_other // 2 : row + n_other // 2]) - t,
                ]
            )
            horizontal_plots[energy_i, resolved_i, :] = [r, t]
            vertical_plots[resolved_i, energy_i, :] = [r, t]

            if resolved_i == 0:
                ax.text(r - side_text_buffer, t, f"{energy[row]}eV", fontsize=8)

            if energy_i + 1 == n_energies:
                label_units = chr(176) if angle_resolved else "um"
                ax.text(
                    r,
                    t - bottom_text_buffer,
                    f"{label_sign}{resolved[row]}{label_units}",
                    fontsize=8,
                )

    ax.plot(*horizontal_plots.T)
    ax.plot(*vertical_plots.T)

    if error_bars:
        ax.errorbar(
            rs,
            ts,
            xerr=np.array(r_errors).T,
            yerr=np.array(t_errors).T,
            elinewidth=0,
            capsize=8,
            color="k",
            fmt=",",
        )
    else:
        for r, t, r_error in zip(rs, ts, r_errors):
            ax.text(
                r + side_text_buffer / 20,
                t + bottom_text_buffer / 10,
                f"{round((sum(r_error))*1000)}um",
                fontsize=6,
            )

    ax.set_xlabel("r [mm]")
    ax.set_ylabel("t [ns]")
    ax.set_title(title)

    x_lim = list(ax.get_xlim())
    y_lim = ax.get_ylim()
    x_lim[1] = max(DET_D / 2 + 0.1, x_lim[1])
    ax.set_xlim(x_lim[0] - side_text_buffer / 5, x_lim[1])
    ax.set_ylim(y_lim[0] - bottom_text_buffer, y_lim[1])
    ax.vlines(DET_D / 2, *ax.get_ylim(), colors="k", linestyles="--")
    ax.text(
        DET_D / 2 - side_text_buffer / 10,
        y_lim[0] - bottom_text_buffer / 1.5,
        "detector",
        horizontalalignment="right",
    )

    return fig, ax


def plot_rays(root: Path = FOX_DIR, ax: plt.Axes = None):
    rays_path = root / "rays.txt"
    table_path = root / "lensTable.txt"
    lens_path = root / "zrElec.txt"

    return _plot_rays(rays_path, table_path, lens_path, ax=ax)


# I separated this out for replotting rays
# There's probably a better way to do this
def _plot_rays(rays_path, table_path, lens_path, ax=None):
    if ax is None:
        fig, ax = plt.subplots(figsize=(14, 8))
    else:
        fig = plt.gcf()

    lensTable = []
    with open(table_path, "r") as f:
        metadata = f.readline().strip("\n")
        for line in f.readlines():
            pieces = line.split(":")
            voltage = float(pieces[1])
            lensTable.append(f"{pieces[0]}: {voltage:.3f}V")

    n_rays = ""
    with open(rays_path, "r") as f:
        n_headerlines = 4
        lines = f.readlines()

        n_rays = int(lines[1][17:27]) - 1
        n_angs = n_rays // 3
        f_length = len(lines)

        step_length = n_rays + n_headerlines
        n_steps = f_length // step_length  # ignore unfinished steps

        r_data = np.zeros((n_rays, n_steps))
        z_data = np.zeros(n_steps)
        for step_i in range(n_steps):
            start = step_i * step_length
            z_data[step_i] = float(lines[start])
            for ray_i, line in enumerate(
                lines[start + n_headerlines : start + n_headerlines + n_rays]
            ):
                r_data[ray_i, step_i] = float(line[0:15])

    lens_z = []
    lens_x = []
    with open(lens_path, "r") as f:
        for line in f:
            lens_z.append(float(line[0:27]) * M_TO_MM)
            lens_x.append(float(line[28:]) * M_TO_MM)

    colors = ["b", "g", "r"]
    legendVals = ["-spotsize/2", "0", "spotsize/2"]

    ax.scatter(lens_z, lens_x, c="k", marker=".", s=2)
    for i in range(3):
        for j in range(n_angs):
            label = legendVals[i] if j == 0 else None
            ax.plot(
                z_data,
                r_data[i * n_angs + j, :],
                color=colors[i],
                linewidth=0.5,
                label=label,
            )

    def draw_aperture(d, z=APER_0_Z, color="k"):
        points = [
            [z, -d / 2],
            [z, d / 2],
            [z + 0.508, d / 2 + 0.508],
            [z + 0.508, -d / 2 - 0.508],
            [z, -d / 2],
        ]
        ax.plot(*np.array(points).T, color=color, linewidth=1)

    draw_aperture(APER_0_D)
    draw_aperture(1)
    draw_aperture(0.75)
    draw_aperture(0.5)

    ax.vlines(APER_1_Z, -APER_1_D / 2, APER_1_D / 2, lw=1, colors="k")
    ax.add_patch(Rectangle((DET_Z, -DET_D / 2), 3, DET_D, fill=False, lw=1, color="k"))

    table_xs = [10, 180, 330, 625]
    table_ys = [-25, -30, -35, -40]

    ax.text(table_xs[0], table_ys[0] + 5, lensTable.pop(0))
    table_index = 0
    for i in range(4):
        j_range = 4 if i < 2 else 3
        for j in range(j_range):
            ax.text(table_xs[i], table_ys[j], lensTable[table_index])
            table_index += 1

    ax.set_title(metadata)
    ax.legend()
    ax.set_xlim(SAMPLE_Z - 5, DET_Z + 5)
    ax.set_ylim(-50, 50)

    return fig, ax


def plot_lens(root: Path = FOX_DIR, n_plots: int = 1):
    spacer = 0.001

    elec_path = root / "zrElec.txt"
    ring_path = root / "zrRing.txt"
    # test_path = root / Path("zrtest.txt").resolve()

    checkPath = root / "test-volt.txt"

    fig, ax = plt.subplots(n_plots, 1, figsize=(15, [5, 10, 10][n_plots - 1]))

    elec_z = []
    elec_r = []
    with open(elec_path, "r") as f:
        for line in f.readlines():
            elec_z.append(float(line[:25]) * 1000)
            elec_r.append(float(line[26:]) * 1000)

    ring_z = []
    ring_r = []
    with open(ring_path, "r") as f:
        for line in f.readlines():
            ring_z.append(float(line[:25]) * 1000)
            ring_r.append(float(line[26:]) * 1000)

    legend = ["electrode", "ring"]

    try:
        ax[0].scatter(elec_z, elec_r, marker=".")
        ax[0].scatter(ring_z, ring_r, marker=".")
        ax[0].set_xlim(min(elec_z) - spacer, max(elec_z) + spacer)
        ax[0].set_ylim(0, max(elec_r) + spacer)
        ax[0].legend(legend, loc=4)
    except:
        ax.scatter(elec_z, elec_r, marker=".")
        ax.scatter(ring_z, ring_r, marker=".")
        ax.set_xlim(min(elec_z) - spacer, max(elec_z) + spacer)
        ax.set_ylim(0, max(elec_r) + spacer)
        ax.legend(legend, loc=4)

    if n_plots > 1:
        values = []
        with open(checkPath, "r") as f:
            for line in f.readlines():
                values.append(float(line[6:]))

        ax[1].plot(values)

    if n_plots > 2:
        ax[2].set_xlim(min(elec_z) - spacer, max(elec_z) + spacer)
        ax[2].set_ylim(0, max(elec_r) + spacer)

        for i in range(len(elec_z)):
            ax[2].text(elec_z[i], elec_r[i], str(i + 1), fontsize=6)

    return fig, ax
