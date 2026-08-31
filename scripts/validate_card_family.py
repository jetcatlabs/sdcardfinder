import sys
from urllib.parse import urlparse

from card_common import (
    APPLICATION_CLASSES,
    BUSES,
    FORM_FACTORS,
    UHS_SPEED_CLASSES,
    VIDEO_SPEED_CLASSES,
    card_research_path,
    find_card_candidate,
    hostname_is_allowed,
    load_json,
    manufacturer_domains,
)


RESEARCH_STATUSES = {
    "todo",
    "researching",
    "needs-review",
    "verified",
    "published",
    "needs-reverification",
    "blocked",
}

CARD_STATUSES = {
    "draft",
    "verified",
}


def factual_fields(card_family):
    fields = []

    common = card_family.get(
        "common",
        {}
    )

    if common.get("form_factor") is not None:
        fields.append(
            "common.form_factor"
        )

    if common.get("bus") is not None:
        fields.append(
            "common.bus"
        )

    speed_classes = common.get(
        "speed_classes",
        {}
    )

    for key in (
        "uhs",
        "video",
        "application",
    ):
        if speed_classes.get(key) is not None:
            fields.append(
                "common.speed_classes.{}".format(
                    key
                )
            )

    performance = common.get(
        "performance",
        {}
    )

    for key in (
        "max_read_mbps",
        "max_write_mbps",
        "minimum_sustained_write_mbps",
    ):
        if performance.get(key) is not None:
            fields.append(
                "common.performance.{}".format(
                    key
                )
            )

    for index, variant in enumerate(
        card_family.get(
            "variants",
            []
        )
    ):
        if variant.get("capacity_gb") is not None:
            fields.append(
                "variants.{}.capacity_gb".format(
                    index
                )
            )

        if variant.get("part_number"):
            fields.append(
                "variants.{}.part_number".format(
                    index
                )
            )

    return fields


def validate(card_id):
    errors = []
    warnings = []

    path = card_research_path(
        card_id
    )

    if not path.exists():
        return (
            [
                "Research file not found: {}".format(
                    path
                )
            ],
            warnings,
        )

    record = load_json(
        path
    )

    research_status = record.get(
        "research_status"
    )

    if research_status not in RESEARCH_STATUSES:
        errors.append(
            "Unknown research_status: {}".format(
                research_status
            )
        )

    card_family = record.get(
        "card_family"
    )

    if not isinstance(
        card_family,
        dict
    ):
        errors.append(
            "card_family must be an object."
        )
        return errors, warnings

    if card_family.get("id") != card_id:
        errors.append(
            "card_family.id does not match filename."
        )

    candidate = find_card_candidate(
        card_id
    )

    if candidate is None:
        errors.append(
            "No candidate exists for: {}".format(
                card_id
            )
        )

    manufacturer = card_family.get(
        "manufacturer"
    )

    if not manufacturer:
        errors.append(
            "card_family.manufacturer is missing."
        )

    approved_domains = []

    if manufacturer:
        approved_domains = manufacturer_domains(
            manufacturer
        )

        if not approved_domains:
            errors.append(
                "No approved source domains configured "
                "for manufacturer: {}".format(
                    manufacturer
                )
            )

    common = card_family.get(
        "common",
        {}
    )

    form_factor = common.get(
        "form_factor"
    )

    if not form_factor:
        errors.append(
            "common.form_factor is missing."
        )
    elif form_factor not in FORM_FACTORS:
        errors.append(
            "Unknown form factor: {}".format(
                form_factor
            )
        )

    bus = common.get(
        "bus"
    )

    if not bus:
        errors.append(
            "common.bus is missing."
        )
    elif bus not in BUSES:
        errors.append(
            "Unknown bus: {}".format(
                bus
            )
        )

    speed_classes = common.get(
        "speed_classes",
        {}
    )

    uhs = speed_classes.get(
        "uhs"
    )

    if uhs is not None:
        if uhs not in UHS_SPEED_CLASSES:
            errors.append(
                "Unknown UHS speed class: {}".format(
                    uhs
                )
            )

    video = speed_classes.get(
        "video"
    )

    if video is not None:
        if video not in VIDEO_SPEED_CLASSES:
            errors.append(
                "Unknown video speed class: {}".format(
                    video
                )
            )

    application = speed_classes.get(
        "application"
    )

    if application is not None:
        if application not in APPLICATION_CLASSES:
            errors.append(
                "Unknown application class: {}".format(
                    application
                )
            )

    performance = common.get(
        "performance",
        {}
    )

    for key in (
        "max_read_mbps",
        "max_write_mbps",
        "minimum_sustained_write_mbps",
    ):
        value = performance.get(
            key
        )

        if value is not None:
            if not isinstance(
                value,
                (int, float)
            ) or value <= 0:
                errors.append(
                    "{} must be a positive number.".format(
                        "common.performance.{}".format(
                            key
                        )
                    )
                )

    video_minimums = {
        "V6": 6,
        "V10": 10,
        "V30": 30,
        "V60": 60,
        "V90": 90,
    }

    sustained = performance.get(
        "minimum_sustained_write_mbps"
    )

    if (
        video in video_minimums
        and sustained is not None
        and sustained < video_minimums[video]
    ):
        errors.append(
            "minimum_sustained_write_mbps contradicts "
            "{}.".format(
                video
            )
        )

    variants = card_family.get(
        "variants",
        []
    )

    if not variants:
        errors.append(
            "card_family.variants is empty."
        )

    capacities = set()
    part_numbers = set()

    for index, variant in enumerate(
        variants
    ):
        capacity = variant.get(
            "capacity_gb"
        )

        if (
            not isinstance(
                capacity,
                int
            )
            or capacity <= 0
        ):
            errors.append(
                "variants.{}.capacity_gb must be "
                "a positive integer.".format(
                    index
                )
            )
        elif capacity in capacities:
            errors.append(
                "Duplicate capacity: {} GB".format(
                    capacity
                )
            )
        else:
            capacities.add(
                capacity
            )

        part_number = variant.get(
            "part_number"
        )

        if not part_number:
            errors.append(
                "variants.{}.part_number is missing.".format(
                    index
                )
            )
        elif part_number in part_numbers:
            errors.append(
                "Duplicate part number: {}".format(
                    part_number
                )
            )
        else:
            part_numbers.add(
                part_number
            )

    sources = card_family.get(
        "sources",
        []
    )

    if not sources:
        errors.append(
            "card_family.sources is empty."
        )

    source_ids = set()

    for source in sources:
        source_id = source.get(
            "id"
        )

        if not source_id:
            errors.append(
                "Source is missing id."
            )
            continue

        if source_id in source_ids:
            errors.append(
                "Duplicate source id: {}".format(
                    source_id
                )
            )
        else:
            source_ids.add(
                source_id
            )

        if source.get(
            "authority"
        ) != "manufacturer":
            errors.append(
                "{} is not marked as manufacturer "
                "authority.".format(
                    source_id
                )
            )

        if source.get(
            "first_party_confirmed"
        ) is not True:
            errors.append(
                "{} is not confirmed first-party.".format(
                    source_id
                )
            )

        if not source.get(
            "verified_at"
        ):
            errors.append(
                "{} is missing verified_at.".format(
                    source_id
                )
            )

        url = source.get(
            "url",
            ""
        )

        parsed = urlparse(
            url
        )

        if (
            parsed.scheme != "https"
            or not parsed.hostname
        ):
            errors.append(
                "{} has invalid HTTPS URL.".format(
                    source_id
                )
            )
        elif approved_domains:
            if not hostname_is_allowed(
                parsed.hostname,
                approved_domains
            ):
                errors.append(
                    "{} source domain is not approved "
                    "for {}: {}".format(
                        source_id,
                        manufacturer,
                        parsed.hostname,
                    )
                )

    claims = record.get(
        "claims",
        []
    )

    claimed_fields = set()

    for claim in claims:
        field = claim.get(
            "field"
        )

        source_id = claim.get(
            "source_id"
        )

        evidence = claim.get(
            "evidence"
        )

        if not field:
            errors.append(
                "Claim is missing field."
            )
            continue

        claimed_fields.add(
            field
        )

        if source_id not in source_ids:
            errors.append(
                "{} references unknown source: {}".format(
                    field,
                    source_id,
                )
            )

        if not evidence:
            errors.append(
                "Claim has no evidence note: {}".format(
                    field
                )
            )

    for field in factual_fields(
        card_family
    ):
        if field not in claimed_fields:
            errors.append(
                "No manufacturer evidence for: {}".format(
                    field
                )
            )

    status = card_family.get(
        "status"
    )

    if status not in CARD_STATUSES:
        errors.append(
            "Unknown card_family.status: {}".format(
                status
            )
        )

    return errors, warnings


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python scripts\\validate_card_family.py "
            "<card-family-id>"
        )
        sys.exit(1)

    card_id = sys.argv[1]

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
        print(
            "FAIL: {} error(s)".format(
                len(errors)
            )
        )

        sys.exit(1)

    print(
        "PASS: {}".format(
            card_id
        )
    )


if __name__ == "__main__":
    main()