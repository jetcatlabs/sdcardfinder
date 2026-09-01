import argparse
import re
import subprocess
import sys
from pathlib import Path

from device_common import (
    CANDIDATES_PATH,
    DEVICES_PATH,
    load_json as load_device_json,
    research_path,
    write_json as write_device_json,
)

from card_common import (
    CARD_CANDIDATES_PATH,
    card_research_path,
    load_json as load_card_json,
    write_json as write_card_json,
)


VALID_PRIORITIES = {
    "high",
    "medium",
    "low",
}


VALID_DEVICE_CATEGORIES = {
    "gaming-handheld",
    "action-camera",
    "camera",
    "single-board-computer",
    "dash-camera",
}


ID_PATTERN = re.compile(
    r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
)

SCRIPTS_DIR = Path(__file__).resolve().parent


def start_research(candidate_type, candidate_id):
    if candidate_type == "device":
        script = SCRIPTS_DIR / "new_device.py"
    elif candidate_type == "card":
        script = SCRIPTS_DIR / "new_card_family.py"
    else:
        print(
            "ERROR: Unknown candidate type: {}".format(
                candidate_type
            )
        )
        return 1

    print()
    print(
        "Starting research: {}".format(
            candidate_id
        )
    )

    result = subprocess.run([
        sys.executable,
        str(script),
        candidate_id,
    ])

    if result.returncode != 0:
        print()
        print(
            "ERROR: Candidate was created, but "
            "research could not be started."
        )
        print(
            "Candidate remains available as todo "
            "unless the scaffold script changed it."
        )
        return result.returncode

    return 0

def validate_common_id(candidate_id):
    errors = []

    if not ID_PATTERN.fullmatch(candidate_id):
        errors.append(
            "ID must use lowercase letters, numbers, "
            "and single hyphens only."
        )

    return errors


def add_device_candidate(args):
    errors = validate_common_id(
        args.id
    )

    if args.priority not in VALID_PRIORITIES:
        errors.append(
            "Invalid priority: {}".format(
                args.priority
            )
        )

    if args.category not in VALID_DEVICE_CATEGORIES:
        errors.append(
            "Invalid device category: {}".format(
                args.category
            )
        )

    candidates = load_device_json(
        CANDIDATES_PATH
    )

    if any(
        item.get("id") == args.id
        for item in candidates
    ):
        errors.append(
            "Device candidate already exists: {}".format(
                args.id
            )
        )

    if research_path(args.id).exists():
        errors.append(
            "Device research file already exists: {}".format(
                args.id
            )
        )

    devices = load_device_json(
        DEVICES_PATH
    )

    if any(
        item.get("id") == args.id
        for item in devices
    ):
        errors.append(
            "Production device already exists: {}".format(
                args.id
            )
        )

    if errors:
        for error in errors:
            print(
                "ERROR: {}".format(
                    error
                )
            )

        return 1

    candidate = {
        "id": args.id,
        "manufacturer": args.manufacturer,
        "model": args.model,
        "category": args.category,
        "priority": args.priority,
        "status": "todo",
    }

    candidates.append(
        candidate
    )

    write_device_json(
        CANDIDATES_PATH,
        candidates
    )

    print(
        "Added device candidate: {}".format(
            args.id
        )
    )

    print(
        "Status: todo"
    )

    if args.start:
        return start_research(
            "device",
            args.id,
        )

    return 0


def add_card_candidate(args):
    errors = validate_common_id(
        args.id
    )

    if args.priority not in VALID_PRIORITIES:
        errors.append(
            "Invalid priority: {}".format(
                args.priority
            )
        )

    candidates = load_card_json(
        CARD_CANDIDATES_PATH
    )

    if any(
        item.get("id") == args.id
        for item in candidates
    ):
        errors.append(
            "Card candidate already exists: {}".format(
                args.id
            )
        )

    if card_research_path(
        args.id
    ).exists():
        errors.append(
            "Card research file already exists: {}".format(
                args.id
            )
        )

    if errors:
        for error in errors:
            print(
                "ERROR: {}".format(
                    error
                )
            )

        return 1

    candidate = {
        "id": args.id,
        "manufacturer": args.manufacturer,
        "product_family": args.product_family,
        "priority": args.priority,
        "status": "todo",
    }

    candidates.append(
        candidate
    )

    write_card_json(
        CARD_CANDIDATES_PATH,
        candidates
    )

    print(
        "Added card-family candidate: {}".format(
            args.id
        )
    )

    print(
        "Status: todo"
    )

    if args.start:
        return start_research(
            "card",
            args.id,
        )

    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Add an SD Card Finder research candidate."
        )
    )

    subparsers = parser.add_subparsers(
        dest="candidate_type",
        required=True,
    )

    device_parser = subparsers.add_parser(
        "device",
        help="Add a device candidate.",
    )

    device_parser.add_argument(
        "id"
    )

    device_parser.add_argument(
        "--manufacturer",
        required=True,
    )

    device_parser.add_argument(
        "--model",
        required=True,
    )

    device_parser.add_argument(
        "--category",
        required=True,
        choices=sorted(
            VALID_DEVICE_CATEGORIES
        ),
    )

    device_parser.add_argument(
        "--priority",
        default="medium",
        choices=sorted(
            VALID_PRIORITIES
        ),
    )

    device_parser.set_defaults(
        handler=add_device_candidate
    )
    
    device_parser.add_argument(
        "--start",
        action="store_true",
        help=(
            "Immediately create the research "
            "record after adding the candidate."
        ),
    )

    card_parser = subparsers.add_parser(
        "card",
        help="Add a card-family candidate.",
    )

    card_parser.add_argument(
        "id"
    )

    card_parser.add_argument(
        "--manufacturer",
        required=True,
    )

    card_parser.add_argument(
        "--product-family",
        required=True,
    )

    card_parser.add_argument(
        "--priority",
        default="medium",
        choices=sorted(
            VALID_PRIORITIES
        ),
    )
    
    card_parser.add_argument(
        "--start",
        action="store_true",
        help=(
            "Immediately create the research "
            "record after adding the candidate."
        ),
    )

    card_parser.set_defaults(
        handler=add_card_candidate
    )

    return parser


def main():
    parser = build_parser()

    args = parser.parse_args()

    return args.handler(
        args
    )


if __name__ == "__main__":
    sys.exit(
        main()
    )