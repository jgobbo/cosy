from matplotlib import pyplot as plt
from pathlib import Path

from tkinter import Tk
from tkinter.filedialog import askopenfilename

from cosy.plots import _plot_rays
from cosy.constants import FOX_DIR


def main():
    Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
    ray_path = Path(
        askopenfilename()
    )  # show an "Open" dialog box and return the path to the selected file
    table_path = ray_path.parent / ray_path.name.replace("rays", "tabl")
    lens_path = FOX_DIR / "zrElec.txt"

    _plot_rays(ray_path, table_path, lens_path)
    plt.show()


if __name__ == "__main__":
    main()
