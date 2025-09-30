"""Fetch an optimization record from the LRC and generate raytracing and conversion map
results for it. You can provide the job id as the first argument in the terminal, or it
can be read automatically from the last valid Slack message sent to the specified user.
"""

import os, sys

from slappy import SlackMessenger, Users
from cosy import FOX_DIR


def main() -> None:
    argv = sys.argv
    job_id = None
    if len(argv) > 1:
        job_id = int(argv[1])
    else:
        messenger = SlackMessenger(default_user=Users.Jacob)

        limit = 10
        for message in messenger.get_dm_history(limit=limit):
            text: str = message["text"]
            if "slurm optimization finished" in text:
                job_id = int(text.split("-")[1])
                break

    if job_id is None:
        raise ValueError(
            f"No valid Slack message in last {limit} messages and no job "
            "id supplied."
        )

    os.system(
        "scp jgobbo@lrc-xfer.lbl.gov:/global/home/users/jgobbo/cosy/"
        f'results/optimization_record_{job_id}.json "{FOX_DIR}"'
    )
    os.system(
        f'move /y "{FOX_DIR}\\optimization_record_{job_id}.json" '
        f'"{FOX_DIR}\\optimization_record.json"'
    )
    os.system("uv run raytrace_from_record.py")


if __name__ == "__main__":
    main()
