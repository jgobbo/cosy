import os

from slappy import SlackMessenger, Users
from cosy import FOX_DIR


def main() -> None:
    messenger = SlackMessenger(default_user=Users.Jacob)

    job_id = None
    limit = 10
    for message in messenger.get_dm_history(limit=limit):
        text: str = message["text"]
        if "slurm optimization finished" in text:
            job_id = int(text.split("-")[1])
            break

    if job_id is None:
        raise ValueError(f"No valid Slack message in last {limit} messages.")

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
