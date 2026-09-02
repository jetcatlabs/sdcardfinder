import sys
from urllib.parse import urlparse

from device_common import (
    ALLOWED_APPLICATION_CLASSES,
    ALLOWED_BUSES,
    ALLOWED_CATEGORIES,
    ALLOWED_FORMATS,
    FILESYSTEMS,
    ALLOWED_RESEARCH_STATUSES,
    ALLOWED_UHS_SPEED_CLASSES,
    ALLOWED_VIDEO_SPEED_CLASSES,
    hostname_is_allowed,
    manufacturer_domains,
    research_path,
    load_json,
)


def validate(device_id):
    errors = []
    warnings = []

    path = research_path(
        device_id
    )

    if not path.exists():
        errors.append(
            "Research file does not exist."
        )

        return errors, warnings

    record = load_json(path)

    status = record.get(
        "research_status"
    )

    if status not in \
            ALLOWED_RESEARCH_STATUSES:
        errors.append(
            "Invalid research_status."
        )

    device = record.get(
        "device",
        {}
    )

    if device.get("id") != device_id:
        errors.append(
            "Device ID does not match filename."
        )

    if device.get("category") not in \
            ALLOWED_CATEGORIES:
        errors.append(
            "Unknown category: {}".format(
                device.get("category")
            )
        )

    slots = (
        device
        .get("storage", {})
        .get("slots", [])
    )

    if not slots:
        errors.append(
            "At least one storage slot is required."
        )

    for index, slot in enumerate(slots):
        prefix = "storage.slots.{}".format(
            index
        )

        formats = slot.get(
            "accepted_formats",
            []
        )

        if not formats:
            errors.append(
                "{}.accepted_formats is empty."
                .format(prefix)
            )

        for card_format in formats:
            if card_format not in \
                    ALLOWED_FORMATS:
                errors.append(
                    "Unknown format: {}".format(
                        card_format
                    )
                )

        buses = slot.get(
            "bus_support",
            []
        )

        for bus in buses:
            if bus not in ALLOWED_BUSES:
                errors.append(
                    "Unknown bus: {}".format(
                        bus
                    )
                )

        incompatible = slot.get(
            "explicitly_incompatible_buses",
            []
        )

        for bus in incompatible:
            if bus not in ALLOWED_BUSES:
                errors.append(
                    "Unknown incompatible bus: "
                    "{}".format(bus)
                )

        maximum = slot.get(
            "max_capacity_gb"
        )

        maximum_status = slot.get(
            "max_capacity_status"
        )

        if maximum_status == \
                "not_documented" \
                and maximum is not None:

            errors.append(
                "{} has max_capacity_gb but "
                "status is not_documented."
                .format(prefix)
            )

        if maximum_status == \
                "manufacturer_documented" \
                and maximum is None:

            errors.append(
                "{} says capacity is documented "
                "but max_capacity_gb is null."
                .format(prefix)
            )
        
        min_capacity = slot.get(
            "min_capacity_gb"
        )
        
        if (
            min_capacity is not None
            and (
                not isinstance(min_capacity, int)
                or isinstance(min_capacity, bool)
                or min_capacity <= 0
            )
        ):
            errors.append(
                "{} min_capacity_gb must be a positive integer or null."
                .format(prefix)
            )

        if (
            min_capacity is not None
            and maximum is not None
            and min_capacity > maximum
        ):
            errors.append(
                "{} min_capacity_gb cannot exceed max_capacity_gb."
                .format(prefix)
            )

        max_capacity = slot.get(
            "max_capacity_gb"
        )
        
        if (
            min_capacity is not None
            and max_capacity is not None
            and min_capacity > max_capacity
        ):
            errors.append(
                "storage.slots.{}.min_capacity_gb cannot exceed max_capacity_gb.".format(
                    slot_index
                )
            )
        
        requirements = slot.get(
            "requirements",
            {}
        )
        
        required_bus = requirements.get(
            "required_bus"
        )
        
        if (
            required_bus is not None
            and required_bus not in ALLOWED_BUSES
        ):
            errors.append(
                "Unknown required bus: {}".format(
                    required_bus
                )
            )
        
        validate_speed_values(
            requirements,
            errors
        )

        validate_speed_values(
            slot.get(
                "recommendations",
                {}
            ),
            errors
        )
        
        setup_requirements = slot.get(
            "setup_requirements",
            {}
        )
        
        if not isinstance(
            setup_requirements,
            dict
        ):
            errors.append(
                "{} setup_requirements must be an object."
                .format(prefix)
            )
        else:
            allowed_setup_keys = {
                "filesystem",
            }
        
            unknown_setup_keys = (
                set(setup_requirements)
                - allowed_setup_keys
            )
        
            for key in sorted(
                unknown_setup_keys
            ):
                errors.append(
                    "{} unknown setup requirement: {}"
                    .format(
                        prefix,
                        key
                    )
                )
        
            filesystem = (
                setup_requirements
                .get("filesystem")
            )
        
            if (
                filesystem is not None
                and filesystem not in FILESYSTEMS
            ):
                errors.append(
                    "{} unsupported filesystem: {}"
                    .format(
                        prefix,
                        filesystem
                    )
                )
        
    for profile in device.get(
        "usage_profiles",
        []
    ):
        validate_speed_values(
            profile.get(
                "requirements",
                {}
            ),
            errors
        )

        validate_speed_values(
            profile.get(
                "recommendations",
                {}
            ),
            errors
        )

    manufacturer = device.get(
        "manufacturer"
    )
    
    allowed_source_domains = manufacturer_domains(
        manufacturer
    )
    
    if not allowed_source_domains:
        errors.append(
            "No approved source domains configured "
            "for manufacturer: {}".format(
                manufacturer
            )
        )

    sources = device.get(
        "sources",
        []
    )

    source_lookup = {}

    for source in sources:
        source_id = source.get("id")

        if not source_id:
            errors.append(
                "Source missing id."
            )
            continue

        if source_id in source_lookup:
            errors.append(
                "Duplicate source ID: {}".format(
                    source_id
                )
            )

        source_lookup[source_id] = source

        if source.get("authority") != \
                "manufacturer":

            errors.append(
                "{} is not marked as "
                "manufacturer authority."
                .format(source_id)
            )
        
        if not source.get("publisher"):
            errors.append(
                "{} missing publisher.".format(
                    source.get("id", "<unknown source>")
                )
            )
        
        if source.get(
            "first_party_confirmed"
        ) is not True:

            errors.append(
                "{} has not been explicitly "
                "confirmed first-party."
                .format(source_id)
            )

        url = source.get(
            "url",
            ""
        )

        parsed = urlparse(url)

        hostname = parsed.hostname or ""
        
        if not hostname_is_allowed(
            hostname,
            allowed_source_domains
        ):
            errors.append(
                "{} source domain is not approved "
                "for {}: {}".format(
                    source_id,
                    manufacturer,
                    hostname
                )
            )

        if parsed.scheme != "https" \
                or not parsed.netloc:

            errors.append(
                "{} has invalid HTTPS URL."
                .format(source_id)
            )

        if not source.get(
            "verified_at"
        ):
            errors.append(
                "{} missing verified_at."
                .format(source_id)
            )

    claims = record.get(
        "claims",
        []
    )

    claimed_fields = set()

    for claim in claims:
        field = claim.get("field")
        source_id = claim.get(
            "source_id"
        )

        if not field:
            errors.append(
                "Claim missing field."
            )
            continue

        claimed_fields.add(field)

        if source_id not in \
                source_lookup:

            errors.append(
                "Claim {} references unknown "
                "source {}."
                .format(
                    field,
                    source_id
                )
            )

        if not claim.get(
            "evidence"
        ):
            errors.append(
                "Claim {} has no evidence note."
                .format(field)
            )

    required_claims = \
        factual_fields(device)

    missing_claims = sorted(
        required_claims
        - claimed_fields
    )

    for field in missing_claims:
        errors.append(
            "No manufacturer evidence for: "
            "{}".format(field)
        )

    return errors, warnings


def validate_speed_values(values, errors):
    uhs = values.get(
        "minimum_uhs_speed_class"
    )

    if uhs and uhs not in \
            ALLOWED_UHS_SPEED_CLASSES:

        errors.append(
            "Unknown UHS speed class: {}".format(
                uhs
            )
        )

    video = values.get(
        "minimum_video_speed_class"
    )

    if video and video not in \
            ALLOWED_VIDEO_SPEED_CLASSES:

        errors.append(
            "Unknown video speed class: "
            "{}".format(video)
        )

    recommended_uhs = values.get(
        "uhs_speed_class"
    )

    if recommended_uhs \
            and recommended_uhs not in \
            ALLOWED_UHS_SPEED_CLASSES:

        errors.append(
            "Unknown recommended UHS class: "
            "{}".format(recommended_uhs)
        )

    recommended_video = values.get(
        "video_speed_class"
    )

    if recommended_video \
            and recommended_video not in \
            ALLOWED_VIDEO_SPEED_CLASSES:

        errors.append(
            "Unknown recommended video class: "
            "{}".format(recommended_video)
        )

    application = values.get(
        "application_class"
    )

    if application \
            and application not in \
            ALLOWED_APPLICATION_CLASSES:

        errors.append(
            "Unknown application class: "
            "{}".format(application)
        )


def factual_fields(device):
    fields = set()

    def add_nested_fields(base, value):
        if isinstance(value, dict):
            for key, nested_value in value.items():
                add_nested_fields(
                    base + "." + key,
                    nested_value
                )
        else:
            fields.add(base)

    slots = (
        device
        .get("storage", {})
        .get("slots", [])
    )

    for index, slot in enumerate(slots):
        base = "storage.slots.{}".format(
            index
        )

        fields.add(
            base + ".accepted_formats"
        )

        if slot.get("bus_support"):
            fields.add(
                base + ".bus_support"
            )

        if slot.get(
            "explicitly_incompatible_buses"
        ):
            fields.add(
                base
                + ".explicitly_incompatible_buses"
            )

        if slot.get(
            "min_capacity_gb"
        ) is not None:
            fields.add(
                base + ".min_capacity_gb"
            )

        if slot.get(
            "max_capacity_gb"
        ) is not None:
            fields.add(
                base + ".max_capacity_gb"
            )

        for key, value in slot.get(
            "requirements",
            {}
        ).items():
            add_nested_fields(
                base
                + ".requirements."
                + key,
                value
            )

        for key, value in slot.get(
            "recommendations",
            {}
        ).items():
            add_nested_fields(
                base
                + ".recommendations."
                + key,
                value
            )

        for key, value in slot.get(
            "setup_requirements",
            {}
        ).items():
            add_nested_fields(
                base
                + ".setup_requirements."
                + key,
                value
            )

    profiles = device.get(
        "usage_profiles",
        []
    )

    for index, profile in enumerate(profiles):
        base = "usage_profiles.{}".format(
            index
        )

        for key, value in profile.get(
            "requirements",
            {}
        ).items():
            add_nested_fields(
                base
                + ".requirements."
                + key,
                value
            )

        for key, value in profile.get(
            "recommendations",
            {}
        ).items():
            add_nested_fields(
                base
                + ".recommendations."
                + key,
                value
            )

    return fields

def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python scripts\\validate_device.py "
            "<device-id>"
        )
        return 1

    device_id = sys.argv[1]

    errors, warnings = validate(
        device_id
    )

    for warning in warnings:
        print(
            "WARNING: {}".format(warning)
        )

    for error in errors:
        print(
            "ERROR: {}".format(error)
        )

    if errors:
        print()
        print(
            "FAIL: {} error(s)".format(
                len(errors)
            )
        )

        return 1

    print(
        "PASS: {}".format(device_id)
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())