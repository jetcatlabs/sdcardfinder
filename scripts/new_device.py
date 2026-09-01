from device_common import (
    CANDIDATES_PATH,
    find_candidate,
    load_json,
    research_path,
    write_json,
)
import sys

from device_common import (
    find_candidate,
    research_path,
    write_json,
)


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python scripts\\new_device.py "
            "<device-id>"
        )
        return 1

    device_id = sys.argv[1]

    candidate = find_candidate(
        device_id
    )

    if candidate is None:
        print(
            "Candidate not found: {}".format(
                device_id
            )
        )
        return 1
    
    if candidate.get("status") != "todo":
        print(
            "ERROR: Candidate status must be todo "
            "to start research. Current status: {}"
            .format(
                candidate.get("status")
            )
        )
        return 1

    path = research_path(
        device_id
    )

    if path.exists():
        print(
            "Research file already exists:"
        )
        print(path)
        return 1

    record = {
        "research_status": "researching",
        "reviewed_by_human": False,

        "device": {
            "id": candidate["id"],
            "category": candidate["category"],
            "manufacturer": candidate[
                "manufacturer"
            ],
            "model": candidate["model"],

            "aliases": [],

            "related_devices": [],

            "storage": {
                "slots": [
                    {
                        "slot": 1,
                        "accepted_formats": [],
                        "bus_support": [],
                        "requirements": {},
                        "recommendations": {},
                        "setup_requirements": {},
                        "min_capacity_gb": None,
                        "max_capacity_gb": None,
                        "max_capacity_status":
                            "not_documented"
                    }
                ]
            },

            "usage_profiles": [],

            "notes": [],

            "sources": [],

            "status": "draft",

            "last_verified": None
        },

        "claims": []
    }

    write_json(
        path,
        record
    )
    
    candidates = load_json(
        CANDIDATES_PATH
    )

    for item in candidates:
        if item.get("id") == device_id:
            item["status"] = "researching"
            break

    write_json(
        CANDIDATES_PATH,
        candidates
    )

    print(
        "Created: {}".format(path)
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())