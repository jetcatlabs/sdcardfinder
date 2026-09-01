import copy
import sys

from device_common import (
    CANDIDATES_PATH,
    DEVICES_PATH,
    load_json,
    research_path,
    write_json,
)

from validate_device import validate


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python scripts\\promote_device.py "
            "<device-id>"
        )
        return 1

    device_id = sys.argv[1]

    path = research_path(device_id)

    if not path.exists():
        print(
            "Research file not found: {}".format(
                path
            )
        )
        return 1

    record = load_json(path)

    if record.get("research_status") != "verified":
        print(
            "ERROR: research_status must be verified."
        )
        return 1

    if record.get("reviewed_by_human") is not True:
        print(
            "ERROR: reviewed_by_human must be true."
        )
        return 1

    device = record.get("device", {})

    if device.get("status") != "verified":
        print(
            "ERROR: device.status must be verified."
        )
        return 1

    errors, warnings = validate(device_id)

    for warning in warnings:
        print(
            "WARNING: {}".format(warning)
        )

    if errors:
        for error in errors:
            print(
                "ERROR: {}".format(error)
            )

        print()
        print(
            "Promotion refused."
        )
        return 1

    production_device = copy.deepcopy(
        device
    )

    # Build source.supports automatically from claims.
    claims = record.get(
        "claims",
        []
    )

    source_supports = {}

    for claim in claims:
        source_id = claim["source_id"]
        field = claim["field"]

        source_supports.setdefault(
            source_id,
            []
        ).append(field)

    for source in production_device.get(
        "sources",
        []
    ):
        source["supports"] = sorted(
            source_supports.get(
                source["id"],
                []
            )
        )
    
        source.pop(
            "authority",
            None
        )
    
        source.pop(
            "first_party_confirmed",
            None
        )

    devices = load_json(
        DEVICES_PATH
    )

    existing_index = None

    for index, existing in enumerate(devices):
        if existing["id"] == device_id:
            existing_index = index
            break

    if existing_index is None:
        devices.append(
            production_device
        )
    
        print(
            "Added production device: {}".format(
                device_id
            )
        )
    else:
        devices[existing_index] = (
            production_device
        )
    
        print(
            "Updated production device: {}".format(
                device_id
            )
        )

    # Add reciprocal related-device links.
    related_ids = device.get(
        "related_devices",
        []
    )

    for related_id in related_ids:
        for related_device in devices:
            if related_device["id"] != related_id:
                continue

            reciprocal = related_device.setdefault(
                "related_devices",
                []
            )

            if device_id not in reciprocal:
                reciprocal.append(device_id)
                reciprocal.sort()

    write_json(
        DEVICES_PATH,
        devices
    )

    # Mark candidate published.
    candidates = load_json(
        CANDIDATES_PATH
    )

    for candidate in candidates:
        if candidate["id"] == device_id:
            candidate["status"] = "published"
            break

    write_json(
        CANDIDATES_PATH,
        candidates
    )

    # Keep research record as an audit trail.
    record["research_status"] = "published"

    write_json(
        path,
        record
    )

    print(
        "Candidate marked published."
    )

    print(
        "Research record retained for audit."
    )

    print()
    print(
        "Promotion complete: {}".format(
            device_id
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())