import sys

from card_common import (
    CARD_CANDIDATES_PATH,
    RESEARCH_CARDS_DIR,
    card_research_path,
    find_card_candidate,
    load_json,
    write_json,
)


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python scripts\\new_card_family.py "
            "<candidate-id>"
        )
        sys.exit(1)

    card_id = sys.argv[1]

    candidate = find_card_candidate(
        card_id
    )

    if candidate is None:
        print(
            "ERROR: Card candidate not found: {}".format(
                card_id
            )
        )
        sys.exit(1)

    path = card_research_path(
        card_id
    )

    if path.exists():
        print(
            "ERROR: Research file already exists: {}".format(
                path
            )
        )
        sys.exit(1)

    RESEARCH_CARDS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    record = {
        "research_status": "researching",
        "reviewed_by_human": False,

        "card_family": {
            "id": candidate["id"],
            "manufacturer": candidate["manufacturer"],
            "product_family": candidate["product_family"],

            "common": {
                "form_factor": None,
                "bus": None,

                "speed_classes": {
                "sd": None,
                "uhs": None,
                "video": None,
                "application": None,
                "express": None
                },

                "performance": {
                    "max_read_mbps": None,
                    "max_write_mbps": None,
                    "minimum_sustained_write_mbps": None
                },
                
                "endurance": {
                    "continuous_recording": None,
                    "recording_hours": None,
                    "pe_cycles": None
                }
            },

            "variants": [],

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
        CARD_CANDIDATES_PATH
    )

    for item in candidates:
        if item.get("id") == card_id:
            item["status"] = "researching"
            break

    write_json(
        CARD_CANDIDATES_PATH,
        candidates
    )

    print(
        "Created: {}".format(
            path
        )
    )


if __name__ == "__main__":
    main()