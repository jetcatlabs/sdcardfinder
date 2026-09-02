import argparse
import subprocess
import sys
from pathlib import Path

from device_common import (
    CANDIDATES_PATH,
    DEVICES_PATH,
    find_candidate,
    load_json,
    manufacturer_domains,
    research_path,
    write_json,
)


SCRIPTS_DIR = Path(__file__).resolve().parent


def production_device(device_id):
    devices = load_json(
        DEVICES_PATH
    )

    for device in devices:
        if device.get("id") == device_id:
            return device

    return None


def identity_duplicate(candidate):
    devices = load_json(
        DEVICES_PATH
    )

    manufacturer = (
        candidate.get("manufacturer", "")
        .strip()
        .casefold()
    )

    model = (
        candidate.get("model", "")
        .strip()
        .casefold()
    )

    for device in devices:
        if device.get("id") == candidate.get("id"):
            continue

        device_manufacturer = (
            device.get("manufacturer", "")
            .strip()
            .casefold()
        )

        device_model = (
            device.get("model", "")
            .strip()
            .casefold()
        )

        if (
            device_manufacturer == manufacturer
            and device_model == model
        ):
            return device

    return None


def run_preflight(candidate):
    errors = []
    warnings = []

    device_id = candidate["id"]

    status = candidate.get(
        "status"
    )

    if status != "todo":
        errors.append(
            "Candidate status is {} rather than todo."
            .format(status)
        )

    domains = manufacturer_domains(
        candidate.get("manufacturer")
    )

    if not domains:
        errors.append(
            "Manufacturer has no approved source "
            "domains configured."
        )

    production = production_device(
        device_id
    )

    if production is not None:
        errors.append(
            "Production device already exists with "
            "this ID."
        )

    duplicate = identity_duplicate(
        candidate
    )

    if duplicate is not None:
        errors.append(
            "Possible production duplicate: {}"
            .format(
                duplicate.get("id")
            )
        )

    path = research_path(
        device_id
    )

    if path.exists():
        errors.append(
            "Research file already exists."
        )

    return errors, warnings


def print_preflight(candidate, errors, warnings):
    print()
    print("Device triage")
    print("-------------")
    print()

    print(
        "Candidate: {}".format(
            candidate["id"]
        )
    )

    print(
        "Manufacturer: {}".format(
            candidate.get("manufacturer")
        )
    )

    print(
        "Model: {}".format(
            candidate.get("model")
        )
    )

    print(
        "Category: {}".format(
            candidate.get("category")
        )
    )

    print(
        "Priority: {}".format(
            candidate.get("priority")
        )
    )

    print()
    print("Preflight")
    print("---------")

    if errors:
        for error in errors:
            print(
                "FAIL  {}".format(
                    error
                )
            )
    else:
        print("PASS  Candidate status is todo")
        print(
            "PASS  Manufacturer has approved "
            "source domains"
        )
        print(
            "PASS  No production device with "
            "this ID"
        )
        print(
            "PASS  No manufacturer/model "
            "duplicate"
        )
        print(
            "PASS  Research has not already "
            "started"
        )

    for warning in warnings:
        print(
            "WARN  {}".format(
                warning
            )
        )

    if not errors:
        print()
        print("Human check")
        print("-----------")
        print(
            "CHECK Confirm in first-party "
            "manufacturer documentation that "
            "the device accepts removable "
            "SD/microSD storage."
        )


def start_research(candidate):
    answer = input(
        "\nConfirmed removable SD/microSD storage "
        "in manufacturer documentation? [y/N]: "
    )

    if answer.strip().lower() not in {
        "y",
        "yes",
    }:
        print()
        print(
            "Research not started."
        )
        print(
            "Use --block-no-slot if manufacturer "
            "documentation confirms the device "
            "has no removable SD/microSD slot."
        )
        return 1

    script = (
        SCRIPTS_DIR
        / "new_device.py"
    )

    result = subprocess.run([
        sys.executable,
        str(script),
        candidate["id"],
    ])

    return result.returncode


def block_no_slot(candidate, reason):
    candidates = load_json(
        CANDIDATES_PATH
    )

    candidate_id = candidate["id"]

    updated = False

    for item in candidates:
        if item.get("id") != candidate_id:
            continue

        item["status"] = "blocked"

        item["blocked_reason"] = reason

        updated = True
        break

    if not updated:
        print(
            "ERROR: Candidate disappeared "
            "during triage."
        )
        return 1

    path = research_path(
        candidate_id
    )

    if path.exists():
        record = load_json(
            path
        )

        record["research_status"] = (
            "blocked"
        )

        device = record.get(
            "device",
            {}
        )

        notes = device.setdefault(
            "notes",
            []
        )

        if reason not in notes:
            notes.append(
                reason
            )

        write_json(
            path,
            record
        )

    write_json(
        CANDIDATES_PATH,
        candidates
    )

    print()
    print(
        "Blocked: {}".format(
            candidate_id
        )
    )

    print(
        "Reason: {}".format(
            reason
        )
    )

    if path.exists():
        print(
            "Research status synchronized "
            "to blocked."
        )
    else:
        print(
            "Blocked before research scaffold."
        )

    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Preflight a device candidate before "
            "starting compatibility research."
        )
    )

    parser.add_argument(
        "device_id"
    )

    actions = parser.add_mutually_exclusive_group()

    actions.add_argument(
        "--start",
        action="store_true",
        help=(
            "Run preflight, require human storage "
            "confirmation, then start research."
        ),
    )

    actions.add_argument(
        "--block-no-slot",
        action="store_true",
        help=(
            "Mark the candidate blocked because "
            "manufacturer documentation confirms "
            "there is no removable SD/microSD slot."
        ),
    )

    parser.add_argument(
        "--reason",
        help=(
            "Persistent reason used with "
            "--block-no-slot."
        ),
    )

    return parser


def main():
    parser = build_parser()

    args = parser.parse_args()

    candidate = find_candidate(
        args.device_id
    )

    if candidate is None:
        print(
            "ERROR: Candidate not found: {}".format(
                args.device_id
            )
        )
        return 1

    if args.block_no_slot:
        if candidate.get("status") not in {
            "todo",
            "researching",
        }:
            print(
                "ERROR: Cannot block candidate "
                "from status: {}".format(
                    candidate.get("status")
                )
            )
            return 1

        reason = args.reason

        if not reason:
            reason = (
                "Manufacturer documentation "
                "indicates this device does not "
                "provide removable SD/microSD "
                "storage."
            )

        print()
        print(
            "This action marks the device blocked."
        )
        print(
            "Use it only after checking first-party "
            "manufacturer documentation."
        )

        answer = input(
            "Confirm no removable SD/microSD "
            "slot? [y/N]: "
        )

        if answer.strip().lower() not in {
            "y",
            "yes",
        }:
            print(
                "No changes made."
            )
            return 1

        return block_no_slot(
            candidate,
            reason
        )

    errors, warnings = run_preflight(
        candidate
    )

    print_preflight(
        candidate,
        errors,
        warnings
    )

    if errors:
        return 1

    if args.start:
        return start_research(
            candidate
        )

    print()
    print("Next")
    print("----")
    print(
        "Start research:"
    )
    print(
        "  python scripts\\triage_device.py "
        "{} --start".format(
            candidate["id"]
        )
    )

    print()
    print(
        "If first-party documentation confirms "
        "there is no removable slot:"
    )
    print(
        "  python scripts\\triage_device.py "
        "{} --block-no-slot".format(
            candidate["id"]
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())