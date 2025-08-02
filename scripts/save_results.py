from cosy.plots import conversion_map, plot_rays
from cosy.constants import RESULTS_DIR
from pathlib import Path
from shutil import copyfile
from datetime import date
from matplotlib import pyplot as plt
import sys


def main(root: Path = RESULTS_DIR):
    make_conversion_map = int(sys.argv[1]) if len(sys.argv) > 1 else True

    fig_r, _ = plot_rays(root)
    if make_conversion_map:
        fig_d, _ = conversion_map(root)

    plt.show()

    today = date.today()
    timestamp = f"{today.year}_{today.month}_{today.day}"
    filename = input("Gimme a name: ")

    rays_path = root / "rays.txt"
    table_path = root / "lensTable.txt"
    record_path = root / "optimization_record.json"
    save_root = root / "lensTables"
    copyfile(rays_path, save_root / Path(f"{timestamp} rays - {filename}.txt"))
    copyfile(table_path, save_root / Path(f"{timestamp} tabl - {filename}.txt"))
    copyfile(record_path, save_root / Path(f"{timestamp} rcrd - {filename}.json"))
    fig_r.savefig(save_root / Path(f"{timestamp} plot - {filename}.jpg"))
    if make_conversion_map:
        fig_d.savefig(save_root / Path(f"{timestamp} cmap - {filename}.jpg"))


if __name__ == "__main__":
    main()
