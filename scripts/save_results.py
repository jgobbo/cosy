from cosy.plots import conversion_map, plot_rays
from cosy.constants import RESULTS_DIR, FOX_DIR
from pathlib import Path
from shutil import copyfile
from datetime import date
from matplotlib import pyplot as plt
import sys


def main():
    make_conversion_map = int(sys.argv[1]) if len(sys.argv) > 1 else True

    fig_r, _ = plot_rays()
    if make_conversion_map:
        fig_d, _ = conversion_map()

    plt.show()

    today = date.today()
    timestamp = f"{today.year}_{today.month}_{today.day}"
    filename = input("Gimme a name: ")

    rays_path = FOX_DIR / "rays.txt"
    table_path = FOX_DIR / "lensTable.txt"
    record_path = FOX_DIR / "optimization_record.json"
    copyfile(rays_path, RESULTS_DIR / Path(f"{timestamp} rays - {filename}.txt"))
    copyfile(table_path, RESULTS_DIR / Path(f"{timestamp} tabl - {filename}.txt"))
    copyfile(record_path, RESULTS_DIR / Path(f"{timestamp} rcrd - {filename}.json"))
    fig_r.savefig(RESULTS_DIR / Path(f"{timestamp} plot - {filename}.jpg"))
    if make_conversion_map:
        fig_d.savefig(RESULTS_DIR / Path(f"{timestamp} cmap - {filename}.jpg"))


if __name__ == "__main__":
    main()
