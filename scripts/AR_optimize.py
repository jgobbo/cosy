# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "cosy",
# ]
#
# [tool.uv.sources]
# cosy = { path = "../" }
# ///

import cosy


def main() -> None:
    print(cosy.constants.DET_Z)


if __name__ == "__main__":
    main()
