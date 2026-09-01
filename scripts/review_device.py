import sys
from datetime import date

from device_common import (
    CANDIDATES_PATH,
    find_candidate,
    load_json,
    research_path,
    write_json,
)

from validate_device import validate


REVIEWABLE_STATUSES = {
    "researching",
    "needs-review",
    "needs-reverification",
}


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python scripts\\review_device.py "
            "<device-id>"
        )
        return 1

    device_id = sys.argv[1]

    candidate = find_candidate(
        device_id
    )

    if candidate is None:
        print(
            "ERROR: Candidate not found: {}".format(
                device_id
            )
        )
        return 1

    if candidate.get("status") not in REVIEWABLE_STATUSES:
        print(
            "ERROR: Candidate is not reviewable. "
            "Current status: {}"
            .format(
                candidate.get("status")
            )
        )
        return 1

    path = research_path(
        device_id
    )

    if not path.exists():
        print(
            "ERROR: Research file not found: {}".format(
                path
            )
        )
        return 1

    record = load_json(
        path
    )

    research_status = record.get(
        "research_status"
    )

    if research_status not in REVIEWABLE_STATUSES:
        print(
            "ERROR: Research record is not reviewable. "
            "Current status: {}"
            .format(
                research_status
            )
        )
        return 1

    errors, warnings = validate(
        device_id
    )

    for warning in warnings:
        print(
            "WARNING: {}".format(
                warning
            )
        )

    if errors:
        for error in errors:
            print(
                "ERROR: {}".format(
                    error
                )
            )

        print()
        print("Review refused.")
        return 1

    today = date.today().isoformat()

    device = record.get(
        "device",
        {}
    )

    record["research_status"] = "verified"
    record["reviewed_by_human"] = True

    device["status"] = "verified"
    device["last_verified"] = today

    write_json(
        path,
        record
    )

    candidates = load_json(
        CANDIDATES_PATH
    )

    for item in candidates:
        if item.get("id") == device_id:
            item["status"] = "verified"
            break

    write_json(
        CANDIDATES_PATH,
        candidates
    )

    print(
        "Human review recorded: {}".format(
            device_id
        )
    )

    print(
        "Candidate and research marked verified."
    )

    print(
        "last_verified: {}".format(
            today
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())