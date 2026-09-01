import sys
from urllib.parse import urlparse

from card_common import (
    APPLICATION_CLASSES,
    BUSES,
    FORM_FACTORS,
    UHS_SPEED_CLASSES,
    VIDEO_SPEED_CLASSES,
    SD_SPEED_CLASSES,
    SD_EXPRESS_SPEED_CLASSES,
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
        "sd",
        "express"
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

    endurance = common.get(
        "endurance",
        {}
    )

    for key in (
        "continuous_recording",
        "recording_hours",
        "pe_cycles",
    ):
        if endurance.get(key) is not None:
            fields.append(
                "common.endurance.{}".format(
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
            
        overrides = variant.get(
            "overrides",
            {}
        )

        if overrides.get(
            "form_factor"
        ) is not None:
            fields.append(
                "variants.{}.overrides.form_factor".format(
                    index
                )
            )

        if overrides.get(
            "bus"
        ) is not None:
            fields.append(
                "variants.{}.overrides.bus".format(
                    index
                )
            )

        override_speed = overrides.get(
            "speed_classes",
            {}
        )

        for key in (
            "sd",
            "uhs",
            "video",
            "application",
            "express",
        ):
            if override_speed.get(
                key
            ) is not None:
                fields.append(
                    "variants.{}.overrides.speed_classes.{}".format(
                        index,
                        key,
                    )
                )

        override_performance = overrides.get(
            "performance",
            {}
        )

        for key in (
            "max_read_mbps",
            "max_write_mbps",
            "minimum_sustained_write_mbps",
        ):
            if override_performance.get(
                key
            ) is not None:
                fields.append(
                    "variants.{}.overrides.performance.{}".format(
                        index,
                        key,
                    )
                )

        override_endurance = overrides.get(
            "endurance",
            {}
        )

        for key in (
            "continuous_recording",
            "recording_hours",
            "pe_cycles",
        ):
            if override_endurance.get(
                key
            ) is not None:
                fields.append(
                    "variants.{}.overrides.endurance.{}".format(
                        index,
                        key,
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

    if (
        form_factor is not None
        and form_factor not in FORM_FACTORS
    ):
        errors.append(
            "Unknown form factor: {}".format(
                form_factor
            )
        )

    bus = common.get(
        "bus"
    )

    if (
        bus is not None
        and bus not in BUSES
    ):
        errors.append(
            "Unknown bus: {}".format(
                bus
            )
        )

    speed_classes = common.get(
        "speed_classes",
        {}
    )

    sd_class = speed_classes.get(
        "sd"
    )

    if (
        sd_class is not None
        and sd_class not in SD_SPEED_CLASSES
    ):
        errors.append(
            "Unknown SD Speed Class: {}".format(
                sd_class
            )
        )

    express_class = speed_classes.get(
        "express"
    )

    if (
        express_class is not None
        and express_class not in SD_EXPRESS_SPEED_CLASSES
    ):
        errors.append(
            "Unknown SD Express Speed Class: {}".format(
                express_class
            )
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

    endurance = common.get(
        "endurance",
        {}
    )

    continuous_recording = endurance.get(
        "continuous_recording"
    )

    if (
        continuous_recording is not None
        and not isinstance(
            continuous_recording,
            bool
        )
    ):
        errors.append(
            "common.endurance.continuous_recording "
            "must be true or false."
        )

    recording_hours = endurance.get(
        "recording_hours"
    )

    if (
        recording_hours is not None
        and (
            not isinstance(
                recording_hours,
                (int, float)
            )
            or recording_hours <= 0
        )
    ):
        errors.append(
            "common.endurance.recording_hours "
            "must be a positive number."
        )

    pe_cycles = endurance.get(
        "pe_cycles"
    )

    if (
        pe_cycles is not None
        and (
            not isinstance(
                pe_cycles,
                int
            )
            or pe_cycles <= 0
        )
    ):
        errors.append(
            "common.endurance.pe_cycles "
            "must be a positive integer."
        )

    variants = card_family.get(
        "variants",
        []
    )

    if not variants:
        errors.append(
            "card_family.variants is empty."
        )
    
    if form_factor is None:
        for index, variant in enumerate(
            variants
        ):
            variant_form_factor = (
                variant.get(
                    "overrides",
                    {}
                ).get(
                    "form_factor"
                )
            )
    
            if variant_form_factor is None:
                errors.append(
                    "common.form_factor is missing and "
                    "variants.{}.overrides.form_factor "
                    "is not set.".format(
                        index
                    )
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

        if part_number:
            if part_number in part_numbers:
                errors.append(
                    "Duplicate part number: {}".format(
                    part_number
                )
            )
        else:
            part_numbers.add(
                part_number
            )
            
        overrides = variant.get(
            "overrides",
            {}
        )

        override_form_factor = overrides.get(
            "form_factor"
        )

        if (
            override_form_factor is not None
            and override_form_factor not in FORM_FACTORS
        ):
            errors.append(
                "Unknown form factor override: {}".format(
                    override_form_factor
                )
            )

        override_bus = overrides.get(
            "bus"
        )

        if (
            override_bus is not None
            and override_bus not in BUSES
        ):
            errors.append(
                "Unknown bus override: {}".format(
                    override_bus
                )
            )

        override_speed = overrides.get(
            "speed_classes",
            {}
        )
        
        override_sd = override_speed.get(
            "sd"
        )

        if (
            override_sd is not None
            and override_sd not in SD_SPEED_CLASSES
        ):
            errors.append(
                "Unknown SD Speed Class override: {}".format(
                    override_sd
                )
            )

        override_express = override_speed.get(
            "express"
        )

        if (
            override_express is not None
            and override_express not in SD_EXPRESS_SPEED_CLASSES
        ):
            errors.append(
                "Unknown SD Express Speed Class override: {}".format(
                    override_express
                )
            )

        override_uhs = override_speed.get(
            "uhs"
        )

        if (
            override_uhs is not None
            and override_uhs not in UHS_SPEED_CLASSES
        ):
            errors.append(
                "Unknown UHS speed class override: {}".format(
                    override_uhs
                )
            )

        override_video = override_speed.get(
            "video"
        )

        if (
            override_video is not None
            and override_video not in VIDEO_SPEED_CLASSES
        ):
            errors.append(
                "Unknown video speed class override: {}".format(
                    override_video
                )
            )

        override_application = override_speed.get(
            "application"
        )

        if (
            override_application is not None
            and override_application not in APPLICATION_CLASSES
        ):
            errors.append(
                "Unknown application class override: {}".format(
                    override_application
                )
            )

        override_performance = overrides.get(
            "performance",
            {}
        )

        for key, value in override_performance.items():
            if key not in {
                "max_read_mbps",
                "max_write_mbps",
                "minimum_sustained_write_mbps",
            }:
                errors.append(
                    "Unknown performance override: {}".format(
                        key
                    )
                )
                continue

            if (
                not isinstance(
                    value,
                    (int, float)
                )
                or value <= 0
            ):
                errors.append(
                    "variants.{}.overrides.performance.{} "
                    "must be a positive number.".format(
                        index,
                        key,
                    )
                )

        override_endurance = overrides.get(
            "endurance",
            {}
        )

        override_continuous = override_endurance.get(
            "continuous_recording"
        )

        if (
            override_continuous is not None
            and not isinstance(
                override_continuous,
                bool
            )
        ):
            errors.append(
                "variants.{}.overrides.endurance."
                "continuous_recording must be true or false.".format(
                    index
                )
            )

        override_hours = override_endurance.get(
            "recording_hours"
        )

        if (
            override_hours is not None
            and (
                not isinstance(
                    override_hours,
                    (int, float)
                )
                or override_hours <= 0
            )
        ):
            errors.append(
                "variants.{}.overrides.endurance."
                "recording_hours must be a positive number.".format(
                    index
                )
            )

        override_cycles = override_endurance.get(
            "pe_cycles"
        )

        if (
            override_cycles is not None
            and (
                not isinstance(
                    override_cycles,
                    int
                )
                or override_cycles <= 0
            )
        ):
            errors.append(
                "variants.{}.overrides.endurance."
                "pe_cycles must be a positive integer.".format(
                    index
                )
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