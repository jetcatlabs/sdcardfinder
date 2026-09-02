import json
import subprocess
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DEVICE_DIR = ROOT / "research" / "devices"
CARD_DIR = ROOT / "research" / "cards"

DEVICES_PATH = ROOT / "src" / "data" / "devices.json"
CARDS_PATH = ROOT / "src" / "data" / "cards.json"

DEVICE_CANDIDATES_PATH = (
    ROOT / "research" / "candidates.json"
)

CARD_CANDIDATES_PATH = (
    ROOT / "research" / "card_candidates.json"
)

PYTHON_FILES = [
    "build.py",
    "scripts/device_common.py",
    "scripts/card_common.py",
    "scripts/new_device.py",
    "scripts/new_card_family.py",
    "scripts/validate_device.py",
    "scripts/validate_card_family.py",
    "scripts/promote_device.py",
    "scripts/promote_card_family.py",
    "scripts/check_all.py",
    "scripts/review_device.py",
    "scripts/review_card_family.py",
    "scripts/add_candidate.py",
    "scripts/triage_device.py",
]

VERIFICATION_STALE_DAYS = 180

def run_command(args):
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def load_json(path):
    with path.open(
        "r",
        encoding="utf-8"
    ) as handle:
        return json.load(handle)


def validate_research_files(
    directory,
    validator_script,
    label,
):
    passed = 0
    failures = []

    files = sorted(
        directory.glob("*.json")
    )

    print()
    print(label)
    print("-" * len(label))

    for path in files:
        item_id = path.stem

        try:
            record = load_json(
                path
            )
        except Exception as exc:
            failures.append(
                (
                    item_id,
                    "Could not load research file: {}".format(
                        exc
                    ),
                    "",
                )
            )

            print(
                "FAIL  {}".format(
                    item_id
                )
            )

            continue

        research_status = record.get(
            "research_status"
        )

        # Work-in-progress records are allowed to be
        # incomplete. They will receive full validation
        # before review/promotion.
        if research_status in {
            "researching",
            "blocked",
        }:
            print(
                "SKIP  {} ({})".format(
                    item_id,
                    research_status,
                )
            )
            continue

        result = run_command([
            sys.executable,
            validator_script,
            item_id,
        ])

        if result.returncode == 0:
            passed += 1

            print(
                "PASS  {}".format(
                    item_id
                )
            )
        else:
            failures.append(
                (
                    item_id,
                    result.stdout,
                    result.stderr,
                )
            )

            print(
                "FAIL  {}".format(
                    item_id
                )
            )

    return passed, failures


def check_unique_ids(
    path,
    label,
):
    print()
    print(label)
    print("-" * len(label))

    try:
        records = load_json(path)
    except Exception as exc:
        print(
            "FAIL  Could not load {}: {}".format(
                path,
                exc,
            )
        )
        return [
            "Could not load {}".format(path)
        ]

    errors = []
    seen = set()

    for index, record in enumerate(records):
        record_id = record.get("id")

        if not record_id:
            message = (
                "{} record {} has no id."
                .format(
                    label,
                    index,
                )
            )

            errors.append(message)
            print(
                "FAIL  {}".format(
                    message
                )
            )
            continue

        if record_id in seen:
            message = (
                "Duplicate id: {}"
                .format(record_id)
            )

            errors.append(message)
            print(
                "FAIL  {}".format(
                    message
                )
            )
            continue

        seen.add(record_id)

    if not errors:
        print(
            "PASS  {} unique IDs".format(
                len(seen)
            )
        )

    return errors

def check_card_semantic_duplicates():
    print()
    print("Card semantic duplicates")
    print("------------------------")

    cards = load_json(
        CARDS_PATH
    )

    groups = {}

    for card in cards:
        key = (
            card.get("manufacturer"),
            card.get("product_family"),
            card.get("form_factor"),
            card.get("capacity_gb"),
        )

        groups.setdefault(
            key,
            []
        ).append(
            card.get("id")
        )

    errors = []

    for key, card_ids in groups.items():
        if len(card_ids) <= 1:
            continue

        manufacturer, family, form_factor, capacity = key

        message = (
            "Semantic duplicate: {} / {} / {} / {}GB -> {}"
            .format(
                manufacturer,
                family,
                form_factor,
                capacity,
                ", ".join(card_ids),
            )
        )

        errors.append(message)
        print(
            "FAIL  {}".format(
                message
            )
        )

    if not errors:
        print(
            "PASS  No semantic duplicates"
        )

    return errors

def check_research_maintenance():
    print()
    print("Research maintenance")
    print("--------------------")

    warnings = []
    errors = []

    research_files = (
        list(DEVICE_DIR.glob("*.json"))
        + list(CARD_DIR.glob("*.json"))
    )

    today = date.today()

    for path in sorted(research_files):
        record = load_json(path)

        if "device" in record:
            item = record.get("device", {})
        else:
            item = record.get("card_family", {})

        sources = item.get(
            "sources",
            []
        )

        claims = record.get(
            "claims",
            []
        )

        source_ids = {
            source.get("id")
            for source in sources
            if source.get("id")
        }

        claimed_source_ids = {
            claim.get("source_id")
            for claim in claims
            if claim.get("source_id")
        }

        # Claims pointing to nonexistent sources.
        for claim in claims:
            source_id = claim.get(
                "source_id"
            )

            if (
                source_id
                and source_id not in source_ids
            ):
                errors.append(
                    "{} claim {} references missing source {}"
                    .format(
                        path.name,
                        claim.get(
                            "field",
                            "<unknown field>"
                        ),
                        source_id,
                    )
                )

        # Sources that support no claims.
        for source in sources:
            source_id = source.get(
                "id"
            )

            if (
                source_id
                and source_id not in claimed_source_ids
            ):
                warnings.append(
                    "{} source has no claims: {}"
                    .format(
                        path.name,
                        source_id,
                    )
                )

            verified_at = source.get(
                "verified_at"
            )

            if not verified_at:
                continue

            try:
                verified_date = (
                    date.fromisoformat(
                        verified_at
                    )
                )
            except ValueError:
                errors.append(
                    "{} source {} has invalid verified_at: {}"
                    .format(
                        path.name,
                        source_id,
                        verified_at,
                    )
                )
                continue

            age_days = (
                today - verified_date
            ).days

            if age_days > VERIFICATION_STALE_DAYS:
                warnings.append(
                    "{} source {} verification is {} days old"
                    .format(
                        path.name,
                        source_id,
                        age_days,
                    )
                )

    if errors:
        for error in errors:
            print(
                "FAIL  {}".format(
                    error
                )
            )

    if warnings:
        for warning in warnings:
            print(
                "WARN  {}".format(
                    warning
                )
            )

    if not errors and not warnings:
        print(
            "PASS  No maintenance issues"
        )

    return errors, warnings

def check_candidate_consistency(
    candidate_path,
    research_dir,
    object_key,
    label,
):
    print()
    print(label)
    print("-" * len(label))

    candidates = load_json(
        candidate_path
    )

    errors = []

    valid_statuses = {
        "todo",
        "researching",
        "needs-review",
        "verified",
        "published",
        "needs-reverification",
        "blocked",
    }

    candidate_map = {}

    for candidate in candidates:
        candidate_id = candidate.get(
            "id"
        )

        if not candidate_id:
            errors.append(
                "Candidate missing id."
            )
            continue

        if candidate_id in candidate_map:
            errors.append(
                "Duplicate candidate id: {}".format(
                    candidate_id
                )
            )
            continue

        candidate_status = candidate.get(
            "status"
        )

        if candidate_status not in valid_statuses:
            errors.append(
                "Candidate {} has invalid status: {}"
                .format(
                    candidate_id,
                    candidate_status,
                )
            )

        candidate_map[
            candidate_id
        ] = candidate

    research_map = {}
    research_paths = {}

    for path in sorted(
        research_dir.glob("*.json")
    ):
        record = load_json(
            path
        )

        item = record.get(
            object_key,
            {}
        )

        item_id = item.get(
            "id"
        )

        if not item_id:
            errors.append(
                "{} missing {}.id".format(
                    path.name,
                    object_key,
                )
            )
            continue

        if path.stem != item_id:
            errors.append(
                "Research filename/id mismatch: {} contains {}"
                .format(
                    path.name,
                    item_id,
                )
            )

        if item_id in research_map:
            errors.append(
                "Duplicate research id {} in {} and {}"
                .format(
                    item_id,
                    research_paths[item_id],
                    path.name,
                )
            )
            continue

        research_map[
            item_id
        ] = record

        research_paths[
            item_id
        ] = path.name

        if item_id not in candidate_map:
            errors.append(
                "Research file has no candidate: {}".format(
                    item_id
                )
            )
            continue

        candidate = candidate_map[
            item_id
        ]

        if object_key == "device":
            identity_fields = (
                "manufacturer",
                "model",
                "category",
            )
        else:
            identity_fields = (
                "manufacturer",
                "product_family",
            )

        for field in identity_fields:
            candidate_value = candidate.get(
                field
            )

            research_value = item.get(
                field
            )

            if candidate_value != research_value:
                errors.append(
                    "{} {} mismatch for {}: candidate={!r}, research={!r}"
                    .format(
                        object_key,
                        field,
                        item_id,
                        candidate_value,
                        research_value,
                    )
                )

    for candidate_id, candidate in (
        candidate_map.items()
    ):
        candidate_status = candidate.get(
            "status"
        )

        research = research_map.get(
            candidate_id
        )

        # todo means the item has entered the pipeline
        # but research has not started yet.
        if candidate_status == "todo":
            if research is not None:
                errors.append(
                    "Candidate {} is todo but already has a research file"
                    .format(
                        candidate_id
                    )
                )

            continue

        # blocked items may be blocked either before or
        # after research begins.
        if (
            candidate_status == "blocked"
            and research is None
        ):
            continue

        if research is None:
            errors.append(
                "Candidate {} is {} but has no research file"
                .format(
                    candidate_id,
                    candidate_status,
                )
            )
            continue

        research_status = research.get(
            "research_status"
        )

        if research_status not in valid_statuses:
            errors.append(
                "Research {} has invalid status: {}"
                .format(
                    candidate_id,
                    research_status,
                )
            )
            continue

        if candidate_status != research_status:
            errors.append(
                "Candidate/research status mismatch for {}: {} != {}"
                .format(
                    candidate_id,
                    candidate_status,
                    research_status,
                )
            )

    if errors:
        for error in errors:
            print(
                "FAIL  {}".format(
                    error
                )
            )
    else:
        print(
            "PASS  Candidates and research agree"
        )

    return errors

def check_published_device_production():
    print()
    print("Published device production")
    print("---------------------------")

    candidates = load_json(
        DEVICE_CANDIDATES_PATH
    )

    devices = load_json(
        DEVICES_PATH
    )

    production_ids = {
        device.get("id")
        for device in devices
        if device.get("id")
    }

    published_candidate_ids = {
        candidate.get("id")
        for candidate in candidates
        if candidate.get("status") == "published"
        and candidate.get("id")
    }

    research_by_id = {}

    for path in sorted(
        DEVICE_DIR.glob("*.json")
    ):
        research = load_json(path)

        device_id = (
            research.get("device", {})
            .get("id")
        )

        if not device_id:
            continue

        research_by_id.setdefault(
            device_id,
            []
        ).append({
            "file": path.name,
            "status": research.get(
                "research_status"
            ),
        })

    errors = []

    # Exit-side check:
    # anything marked published as a candidate
    # must actually exist in production.
    for device_id in sorted(
        published_candidate_ids
    ):
        if device_id not in production_ids:
            errors.append(
                "Published device missing from production: {}"
                .format(device_id)
            )

    # Side-wall check:
    # every production device must trace back to
    # exactly one published research record.
    for device_id in sorted(
        production_ids
    ):
        records = research_by_id.get(
            device_id,
            []
        )

        if not records:
            errors.append(
                "Production device has no research record: {}"
                .format(device_id)
            )
            continue

        if len(records) != 1:
            errors.append(
                "Production device has {} research records: {}"
                .format(
                    len(records),
                    device_id,
                )
            )
            continue

        record = records[0]

        if record["status"] != "published":
            errors.append(
                "Production device research is not published: {} "
                "({}: {})"
                .format(
                    device_id,
                    record["file"],
                    record["status"],
                )
            )

    if errors:
        for error in errors:
            print(
                "FAIL  {}".format(
                    error
                )
            )
    else:
        print(
            "PASS  {} production devices have exactly one "
            "published research record"
            .format(
                len(production_ids)
            )
        )

    return errors

def check_published_card_production():
    print()
    print("Published card-family production")
    print("--------------------------------")

    cards = load_json(
        CARDS_PATH
    )

    production_by_key = {}

    for card in cards:
        key = (
            card.get("manufacturer"),
            card.get("product_family"),
            card.get("form_factor"),
            card.get("capacity_gb"),
        )

        production_by_key.setdefault(
            key,
            []
        ).append(
            card.get("id")
        )

    errors = []

    published_families = 0
    expected_variants = 0

    for path in sorted(
        CARD_DIR.glob("*.json")
    ):
        record = load_json(
            path
        )

        if record.get(
            "research_status"
        ) != "published":
            continue

        published_families += 1

        family = record.get(
            "card_family",
            {}
        )

        manufacturer = family.get(
            "manufacturer"
        )

        product_family = family.get(
            "product_family"
        )

        common = family.get(
            "common",
            {}
        )

        expected_keys = set()

        for index, variant in enumerate(
            family.get(
                "variants",
                []
            )
        ):
            expected_variants += 1

            overrides = variant.get(
                "overrides",
                {}
            )

            form_factor = overrides.get(
                "form_factor",
                common.get(
                    "form_factor"
                ),
            )

            capacity = variant.get(
                "capacity_gb"
            )

            key = (
                manufacturer,
                product_family,
                form_factor,
                capacity,
            )

            expected_keys.add(
                key
            )

            matches = production_by_key.get(
                key,
                []
            )

            if len(matches) == 0:
                errors.append(
                    (
                        "Published card variant missing from "
                        "production: {} variant {} "
                        "({} / {}GB)"
                    ).format(
                        family.get("id"),
                        index,
                        form_factor,
                        capacity,
                    )
                )

            elif len(matches) > 1:
                errors.append(
                    (
                        "Published card variant has multiple "
                        "production records: {} variant {} -> {}"
                    ).format(
                        family.get("id"),
                        index,
                        ", ".join(matches),
                    )
                )
                
        expected_form_factors = {
            key[2]
            for key in expected_keys
        }

        # Catch stale production variants belonging
        # to this published family.
        for card in cards:
            if (
                card.get("manufacturer")
                != manufacturer
            ):
                continue

            if (
                card.get("product_family")
                != product_family
            ):
                continue

            if (
                card.get("form_factor")
                not in expected_form_factors
            ):
                continue

            key = (
                card.get("manufacturer"),
                card.get("product_family"),
                card.get("form_factor"),
                card.get("capacity_gb"),
            )

            if key not in expected_keys:
                errors.append(
                    (
                        "Production card not represented "
                        "by published research family {}: {}"
                    ).format(
                        family.get("id"),
                        card.get("id"),
                    )
                )

    if errors:
        for error in errors:
            print(
                "FAIL  {}".format(
                    error
                )
            )
    else:
        print(
            "PASS  {} published families / "
            "{} variants covered".format(
                published_families,
                expected_variants,
            )
        )

    return errors
    
def normalize_value(value):
    if isinstance(value, dict):
        return {
            key: normalize_value(item)
            for key, item in value.items()
            if item is not None
        }

    if isinstance(value, list):
        return [
            normalize_value(item)
            for item in value
        ]

    return value


def merge_dicts(base, overrides):
    result = {}

    for key, value in base.items():
        if isinstance(value, dict):
            result[key] = merge_dicts(
                value,
                {}
            )
        else:
            result[key] = value

    for key, value in overrides.items():
        if (
            isinstance(value, dict)
            and isinstance(
                result.get(key),
                dict
            )
        ):
            result[key] = merge_dicts(
                result[key],
                value,
            )
        else:
            result[key] = value

    return result

def check_research_production_drift():
    print()
    print("Research / production drift")
    print("---------------------------")

    errors = []

    production_devices = {
        item.get("id"): item
        for item in load_json(
            DEVICES_PATH
        )
    }

    #
    # Devices
    #
    device_fields = [
        "manufacturer",
        "model",
        "aliases",
        "category",
        "related_devices",
        "storage",
        "usage_profiles",
        "notes",
        "status",
        "last_verified",
    ]

    for path in sorted(
        DEVICE_DIR.glob("*.json")
    ):
        record = load_json(path)

        if record.get(
            "research_status"
        ) != "published":
            continue

        research = record.get(
            "device",
            {}
        )

        device_id = research.get(
            "id"
        )

        production = production_devices.get(
            device_id
        )

        if not production:
            continue

        for field in device_fields:
            expected = normalize_value(
                research.get(field)
            )

            actual = normalize_value(
                production.get(field)
            )

            if expected != actual:
                errors.append(
                    (
                        "Device drift: {} field {}"
                    ).format(
                        device_id,
                        field,
                    )
                )

    #
    # Cards
    #
    production_cards = load_json(
        CARDS_PATH
    )

    production_card_map = {}

    for card in production_cards:
        key = (
            card.get("manufacturer"),
            card.get("product_family"),
            card.get("form_factor"),
            card.get("capacity_gb"),
        )

        production_card_map[key] = card

    card_fields = [
        "form_factor",
        "bus",
        "speed_classes",
        "performance",
        "endurance",
    ]

    for path in sorted(
        CARD_DIR.glob("*.json")
    ):
        record = load_json(path)

        if record.get(
            "research_status"
        ) != "published":
            continue

        family = record.get(
            "card_family",
            {}
        )

        manufacturer = family.get(
            "manufacturer"
        )

        product_family = family.get(
            "product_family"
        )

        common = family.get(
            "common",
            {}
        )

        for index, variant in enumerate(
            family.get(
                "variants",
                []
            )
        ):
            combined = merge_dicts(
                common,
                variant.get(
                    "overrides",
                    {}
                ),
            )

            capacity = variant.get(
                "capacity_gb"
            )

            form_factor = combined.get(
                "form_factor"
            )

            key = (
                manufacturer,
                product_family,
                form_factor,
                capacity,
            )

            production = (
                production_card_map.get(
                    key
                )
            )

            if not production:
                # Coverage checker reports this.
                continue

            for field in card_fields:
                expected = normalize_value(
                    combined.get(field)
                )

                actual = normalize_value(
                    production.get(field)
                )

                if expected != actual:
                    errors.append(
                        (
                            "Card drift: {} variant {} "
                            "field {}"
                        ).format(
                            family.get("id"),
                            index,
                            field,
                        )
                    )

            expected_part_number = (
                variant.get(
                    "part_number"
                )
            )

            actual_part_number = (
                production.get(
                    "part_number"
                )
            )

            if (
                normalize_value(
                    expected_part_number
                )
                != normalize_value(
                    actual_part_number
                )
            ):
                errors.append(
                    (
                        "Card drift: {} variant {} "
                        "field part_number"
                    ).format(
                        family.get("id"),
                        index,
                    )
                )

    if errors:
        for error in errors:
            print(
                "FAIL  {}".format(
                    error
                )
            )
    else:
        print(
            "PASS  Published research matches production"
        )

    return errors

def compile_python():
    print()
    print("Python")
    print("------")

    failures = []

    for relative_path in PYTHON_FILES:
        result = run_command([
            sys.executable,
            "-m",
            "py_compile",
            relative_path,
        ])

        if result.returncode == 0:
            print(
                "PASS  {}".format(
                    relative_path
                )
            )
        else:
            failures.append(
                (
                    relative_path,
                    result.stdout,
                    result.stderr,
                )
            )

            print(
                "FAIL  {}".format(
                    relative_path
                )
            )

    return failures


def run_build():
    print()
    print("Build")
    print("-----")

    result = run_command([
        sys.executable,
        "build.py",
    ])

    if result.returncode == 0:
        print("PASS  build.py")
        return None

    print("FAIL  build.py")

    return (
        result.stdout,
        result.stderr,
    )


def print_failure_details(
    heading,
    failures,
):
    if not failures:
        return

    print()
    print(heading)
    print("=" * len(heading))

    for failure in failures:
        item_id = failure[0]
        stdout = failure[1]
        stderr = failure[2]

        print()
        print(item_id)

        if stdout.strip():
            print(stdout.strip())

        if stderr.strip():
            print(stderr.strip())


def main():
    print(
        "SD Card Finder project check"
    )
    print(
        "=" * 28
    )

    device_passed, device_failures = (
        validate_research_files(
            DEVICE_DIR,
            "scripts/validate_device.py",
            "Devices",
        )
    )

    card_passed, card_failures = (
        validate_research_files(
            CARD_DIR,
            "scripts/validate_card_family.py",
            "Card families",
        )
    )

    production_device_errors = (
        check_unique_ids(
            DEVICES_PATH,
            "Production devices",
        )
    )

    production_card_errors = (
        check_unique_ids(
            CARDS_PATH,
            "Production cards",
        )
    )
    
    semantic_duplicate_errors = (
        check_card_semantic_duplicates()
    )
    
    device_candidate_errors = (
        check_candidate_consistency(
            DEVICE_CANDIDATES_PATH,
            DEVICE_DIR,
            "device",
            "Device candidate consistency",
        )
    )
    
    card_candidate_errors = (
        check_candidate_consistency(
            CARD_CANDIDATES_PATH,
            CARD_DIR,
            "card_family",
            "Card candidate consistency",
        )
    )
    
    published_device_errors = (
        check_published_device_production()
    )
    
    published_card_errors = (
        check_published_card_production()
    )
    
    maintenance_errors, maintenance_warnings = (
        check_research_maintenance()
    )
    
    drift_errors = (
        check_research_production_drift()
    )

    compile_failures = compile_python()

    prebuild_failed = any([
        device_failures,
        card_failures,
        production_device_errors,
        production_card_errors,
        semantic_duplicate_errors,
        device_candidate_errors,
        card_candidate_errors,
        published_device_errors,
        published_card_errors,
        maintenance_errors,
        drift_errors,
        compile_failures,
    ])

    build_failure = None

    if prebuild_failed:
        print()
        print("Build")
        print("-----")
        print(
            "SKIP  Earlier checks failed."
        )
    else:
        build_failure = run_build()

    print_failure_details(
        "Device validation failures",
        device_failures,
    )

    print_failure_details(
        "Card-family validation failures",
        card_failures,
    )

    print_failure_details(
        "Python compilation failures",
        compile_failures,
    )

    if build_failure:
        print()
        print("Build failure")
        print("=============")

        stdout, stderr = build_failure

        if stdout.strip():
            print(stdout.strip())

        if stderr.strip():
            print(stderr.strip())

    failed = any([
        device_failures,
        card_failures,
        production_device_errors,
        production_card_errors,
        semantic_duplicate_errors,
        device_candidate_errors,
        card_candidate_errors,
        published_device_errors,
        published_card_errors,
        compile_failures,
        maintenance_errors,
        drift_errors,
        build_failure,
    ])

    print()
    print("Summary")
    print("-------")

    print(
        "Devices:       {} PASS / {} FAIL".format(
            device_passed,
            len(device_failures),
        )
    )

    print(
        "Maintenance:   {}{}".format(
            "FAIL"
            if maintenance_errors
            else "PASS",
            (
                " / {} warning(s)"
                .format(
                    len(maintenance_warnings)
                )
                if maintenance_warnings
                else ""
            ),
        )
    )

    print(
        "Card families: {} PASS / {} FAIL".format(
            card_passed,
            len(card_failures),
        )
    )

    print(
        "Production:    {}".format(
            "FAIL"
            if (
                production_device_errors
                or production_card_errors
                or semantic_duplicate_errors
                or published_device_errors
                or published_card_errors
                or drift_errors
            )
            else "PASS"
        )
    )

    print(
        "Python:        {}".format(
            "FAIL"
            if compile_failures
            else "PASS"
        )
    )

    print(
        "Build:         {}".format(
            "SKIPPED"
            if prebuild_failed
            else (
                "FAIL"
                if build_failure
                else "PASS"
            )
        )
    )

    print()

    if failed:
        print("OVERALL: FAIL")
        return 1

    print("OVERALL: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())