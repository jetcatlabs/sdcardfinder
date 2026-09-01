import sys
from datetime import date

from card_common import (
    CARD_CANDIDATES_PATH,
    card_research_path,
    find_card_candidate,
    load_json,
    write_json,
)

from validate_card_family import validate


REVIEWABLE_STATUSES = {
    "researching",
    "needs-review",
    "needs-reverification",
}


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python scripts\\review_card_family.py "
            "<card-family-id>"
        )
        return 1

    card_id = sys.argv[1]

    candidate = find_card_candidate(
        card_id
    )

    if candidate is None:
        print(
            "ERROR: Candidate not found: {}".format(
                card_id
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

    path = card_research_path(
        card_id
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
        card_id
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

    card_family = record.get(
        "card_family",
        {}
    )

    record["research_status"] = "verified"
    record["reviewed_by_human"] = True

    card_family["status"] = "verified"
    card_family["last_verified"] = today

    write_json(
        path,
        record
    )

    candidates = load_json(
        CARD_CANDIDATES_PATH
    )

    for item in candidates:
        if item.get("id") == card_id:
            item["status"] = "verified"
            break

    write_json(
        CARD_CANDIDATES_PATH,
        candidates
    )

    print(
        "Human review recorded: {}".format(
            card_id
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