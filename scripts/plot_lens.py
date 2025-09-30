import sys
from cosy.plots import plot_lens
from matplotlib import pyplot as plt


def main():
    n_plots = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    fig, ax = plot_lens(n_plots=n_plots)
    plt.show()


if __name__ == "__main__":
    main()
