import copy
import sys

from card_common import (
    CARD_CANDIDATES_PATH,
    CARDS_PATH,
    card_research_path,
    load_json,
    write_json,
)

from validate_card_family import validate


def capacity_slug(capacity_gb):
    if capacity_gb == 1024:
        return "1tb"

    return "{}gb".format(
        capacity_gb
    )


def capacity_label(capacity_gb):
    if capacity_gb == 1024:
        return "1TB"

    return "{}GB".format(
        capacity_gb
    )


def production_field_for_claim(
    claim_field,
    variant_index,
):
    if claim_field.startswith(
        "common."
    ):
        return claim_field[len("common."):]

    prefix = "variants.{}.".format(
        variant_index
    )

    if claim_field.startswith(
        prefix
    ):
        return claim_field[len(prefix):]

    return None


def build_production_sources(
    research_sources,
    claims,
    variant_index,
):
    production_sources = []

    for research_source in research_sources:
        source_id = research_source["id"]

        supports = []

        for claim in claims:
            if claim.get("source_id") != source_id:
                continue

            production_field = (
                production_field_for_claim(
                    claim.get(
                        "field",
                        ""
                    ),
                    variant_index,
                )
            )

            if production_field:
                supports.append(
                    production_field
                )

        production_source = {
            "type": "manufacturer",
            "publisher": research_source[
                "publisher"
            ],
            "title": research_source[
                "title"
            ],
            "url": research_source[
                "url"
            ],
            "verified_at": research_source[
                "verified_at"
            ],
            "supports": sorted(
                set(supports)
            ),
        }

        production_sources.append(
            production_source
        )

    return production_sources


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python scripts\\promote_card_family.py "
            "<card-family-id>"
        )
        return 1

    card_id = sys.argv[1]

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

    if record.get(
        "research_status"
    ) != "verified":
        print(
            "ERROR: research_status must be verified."
        )
        return 1

    if record.get(
        "reviewed_by_human"
    ) is not True:
        print(
            "ERROR: reviewed_by_human must be true."
        )
        return 1

    card_family = record.get(
        "card_family",
        {}
    )

    if card_family.get(
        "status"
    ) != "verified":
        print(
            "ERROR: card_family.status must be verified."
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
        print(
            "Promotion refused."
        )
        return 1

    common = copy.deepcopy(
        card_family["common"]
    )

    variants = card_family.get(
        "variants",
        []
    )

    research_sources = card_family.get(
        "sources",
        []
    )

    claims = record.get(
        "claims",
        []
    )

    cards = load_json(
        CARDS_PATH
    )

    existing_by_id = {
        card["id"]: index
        for index, card in enumerate(cards)
    }

    promoted_ids = []

    for variant_index, variant in enumerate(
        variants
    ):
        capacity_gb = variant[
            "capacity_gb"
        ]

        form_factor = common[
            "form_factor"
        ]

        production_id = (
            "{}-{}-{}".format(
                card_family["manufacturer"]
                    .lower()
                    .replace(" ", "-"),
                card_family["product_family"]
                    .lower()
                    .replace(" ", "-")
                    .replace("!", ""),
                "{}-{}".format(
                    form_factor.lower(),
                    capacity_slug(
                        capacity_gb
                    ),
                ),
            )
        )

        production_card = {
            "id": production_id,
            "manufacturer": card_family[
                "manufacturer"
            ],
            "product_family": card_family[
                "product_family"
            ],
            "model": "{} {}".format(
                capacity_label(
                    capacity_gb
                ),
                form_factor,
            ),
            "capacity_gb": capacity_gb,
            "form_factor": form_factor,
            "bus": common["bus"],
            "speed_classes": copy.deepcopy(
                common[
                    "speed_classes"
                ]
            ),
            "performance": copy.deepcopy(
                common[
                    "performance"
                ]
            ),
            "part_number": variant[
                "part_number"
            ],
            "sources": build_production_sources(
                research_sources,
                claims,
                variant_index,
            ),
            "status": "verified",
            "last_verified": card_family[
                "last_verified"
            ],
        }

        existing_index = existing_by_id.get(
            production_id
        )

        if existing_index is None:
            cards.append(
                production_card
            )

            existing_by_id[
                production_id
            ] = len(cards) - 1

            print(
                "Added production card: {}".format(
                    production_id
                )
            )
        else:
            cards[
                existing_index
            ] = production_card

            print(
                "Updated production card: {}".format(
                    production_id
                )
            )

        promoted_ids.append(
            production_id
        )

    write_json(
        CARDS_PATH,
        cards
    )

    candidates = load_json(
        CARD_CANDIDATES_PATH
    )

    for candidate in candidates:
        if candidate.get(
            "id"
        ) == card_id:
            candidate[
                "status"
            ] = "published"
            break

    write_json(
        CARD_CANDIDATES_PATH,
        candidates
    )

    record[
        "research_status"
    ] = "published"

    write_json(
        path,
        record
    )

    print()
    print(
        "Candidate marked published."
    )
    print(
        "Research record retained for audit."
    )
    print()
    print(
        "Promotion complete: {}".format(
            card_id
        )
    )
    print(
        "Generated {} production card(s).".format(
            len(promoted_ids)
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )