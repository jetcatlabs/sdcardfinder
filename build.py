from pathlib import Path
import json
import shutil
import html


ROOT = Path(__file__).parent
SRC = ROOT / "src"
DIST = ROOT / "dist"

DEVICES_FILE = SRC / "data" / "devices.json"
CARDS_FILE = SRC / "data" / "cards.json"

SITE_URL = "https://sdcardfinder.com"

APPLICATION_CLASS_RANK = {
    "A1": 1,
    "A2": 2,
}

VIDEO_SPEED_RANK = {
    "V6": 6,
    "V10": 10,
    "V30": 30,
    "V60": 60,
    "V90": 90,
}

UHS_SPEED_RANK = {
    "U1": 1,
    "U3": 3,
}

UHS_BUS_RANK = {
    "UHS-I": 1,
    "UHS-II": 2,
    "UHS-III": 3,
}

SD_SPEED_RANK = {
    "C2": 2,
    "C4": 4,
    "C6": 6,
    "C10": 10,
}

SD_EXPRESS_SPEED_RANK = {
    "E150": 150,
    "E300": 300,
    "E450": 450,
    "E600": 600,
}

DEVICE_RECOMMENDATION_OVERRIDES = {
    "dji-osmo-action-4": "recommended-spec",
    "dji-osmo-action-5-pro": "recommended-spec",
    "dji-osmo-action-6": "recommended-spec",
    "dji-osmo-360": "recommended-spec",
    "nikon-z6iii": "recommended-spec",
}

RECOMMENDATION_STRATEGIES = {
    "gaming-handheld": "capacity",
    "action-camera": "usage",
    "camera": "usage",
    "single-board-computer": "application",
    "dash-camera": "recommended-spec",
}

CAPACITY_PROFILES = {
    "gaming-handheld": {
        "smallest": 128,
        "recommended": 512,
        "more_storage": 1024,
    }
}


def load_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def clean_dist():
    if DIST.exists():
        shutil.rmtree(DIST)

    DIST.mkdir()


def copy_static_files():
    shutil.copy2(
        SRC / "index.html",
        DIST / "index.html"
    )

    for directory in ["css", "js", "data", "assets"]:
        shutil.copytree(
            SRC / directory,
            DIST / directory
        )


def format_list(values):
    if not values:
        return "Not documented"

    return ", ".join(values)


def card_meets_requirements(card, requirements):
    requirements = requirements or {}
    
    required_bus = requirements.get(
        "required_bus"
    )

    if required_bus:
        card_bus = card.get(
            "bus"
        )

        if card_bus != required_bus:
            return False
    
    minimum_uhs_bus = requirements.get(
        "minimum_uhs_bus"
    )

    if minimum_uhs_bus:
        card_bus = card.get(
            "bus"
        )

        if card_bus not in UHS_BUS_RANK:
            return False

        if (
            UHS_BUS_RANK.get(card_bus, 0)
            < UHS_BUS_RANK.get(
                minimum_uhs_bus,
                0
            )
        ):
            return False
    
    minimum_application = requirements.get(
        "minimum_application_class"
    )

    if minimum_application:
        card_application = card.get(
            "speed_classes",
            {}
        ).get("application")

        if not card_application:
            return False

        if (
            APPLICATION_CLASS_RANK.get(
                card_application,
                0
            )
            < APPLICATION_CLASS_RANK.get(
                minimum_application,
                0
            )
        ):
            return False

    minimum_video = requirements.get(
        "minimum_video_speed_class"
    )

    if minimum_video:
        card_video = card.get(
            "speed_classes", {}
        ).get("video")

        if not card_video:
            return False

        if VIDEO_SPEED_RANK.get(card_video, 0) < \
                VIDEO_SPEED_RANK.get(minimum_video, 0):
            return False

    minimum_uhs = requirements.get(
        "minimum_uhs_speed_class"
    )

    if minimum_uhs:
        card_uhs = card.get(
            "speed_classes", {}
        ).get("uhs")

        if not card_uhs:
            return False

        if UHS_SPEED_RANK.get(card_uhs, 0) < \
                UHS_SPEED_RANK.get(minimum_uhs, 0):
            return False

    required_sd = requirements.get(
        "minimum_sd_speed_class"
    )

    if required_sd:
        card_sd = card.get(
            "speed_classes",
            {}
        ).get("sd")

        if not card_sd:
            return False

        if SD_SPEED_RANK.get(card_sd, 0) < \
                SD_SPEED_RANK.get(required_sd, 0):
            return False

    required_express = requirements.get(
        "minimum_sd_express_speed_class"
    )

    if required_express:
        card_express = card.get(
            "speed_classes",
            {}
        ).get("express")

        if not card_express:
            return False

        if SD_EXPRESS_SPEED_RANK.get(card_express, 0) < \
                SD_EXPRESS_SPEED_RANK.get(
                    required_express,
                    0
                ):
            return False

    return True

def card_meets_requirement_set(
    card,
    requirements=None,
    requirements_any_of=None,
):
    if not card_meets_requirements(
        card,
        requirements or {}
    ):
        return False

    requirements_any_of = (
        requirements_any_of or []
    )

    if requirements_any_of:
        if not any(
            card_meets_requirements(
                card,
                option
            )
            for option in requirements_any_of
        ):
            return False

    return True

def card_fits_slot(card, slot):
    if not form_factor_matches(
        slot.get(
            "accepted_formats",
            []
        ),
        card.get(
            "form_factor"
        ),
    ):
        return False

    incompatible_buses = slot.get(
        "explicitly_incompatible_buses",
        []
    )

    if card.get("bus") in incompatible_buses:
        return False

    min_capacity = slot.get(
        "min_capacity_gb"
    )
    
    if (
        min_capacity is not None
        and card.get("capacity_gb", 0) < min_capacity
    ):
        return False    

    max_capacity = slot.get("max_capacity_gb")

    if (
        max_capacity is not None
        and card.get("capacity_gb", 0) > max_capacity
    ):
        return False

    if not card_meets_requirement_set(
        card,
        slot.get(
            "requirements",
            {}
        ),
        slot.get(
            "requirements_any_of",
            []
        ),
    ):
        return False

    return True

def form_factor_matches(
    accepted_formats,
    card_form_factor,
):
    if card_form_factor in accepted_formats:
        return True

    format_families = {
        "microSD": {
            "microSD",
            "microSDHC",
            "microSDXC",
        },
        "SD": {
            "SD",
            "SDHC",
            "SDXC",
        },
    }

    for accepted_format in accepted_formats:
        family = format_families.get(
            accepted_format
        )

        if (
            family
            and card_form_factor in family
        ):
            return True

    return False

def compatible_cards(device, cards):
    matches = []

    for card in cards:
        matching_slots = []

        for slot in device["storage"]["slots"]:
            if card_fits_slot(card, slot):
                matching_slots.append(slot["slot"])

        if matching_slots:
            matches.append({
                "card": card,
                "slots": matching_slots
            })

    matches.sort(
        key=lambda item: item["card"]["capacity_gb"]
    )

    return matches


def build_speed_text(card):
    values = []

    speed_classes = card.get(
        "speed_classes",
        {}
    )

    for key in [
        "sd",
        "uhs",
        "video",
        "application",
        "express",
    ]:
        value = speed_classes.get(key)

        if value:
            values.append(value)

    return " · ".join(values)

def build_recommendation_reason(recommendations):
    reasons = []

    recommended_uhs = recommendations.get(
        "uhs_speed_class"
    )

    if recommended_uhs:
        reasons.append(
            recommended_uhs
        )

    recommended_video = recommendations.get(
        "video_speed_class"
    )

    if recommended_video:
        reasons.append(
            recommended_video
        )

    recommended_application = recommendations.get(
        "application_class"
    )

    if recommended_application:
        reasons.append(
            recommended_application
        )

    if not reasons:
        return None

    return "Matches recommended specs: " + " · ".join(
        reasons
    )

def generate_endurance_badge(card):
    endurance = card.get(
        "endurance",
        {}
    )

    if not endurance.get(
        "continuous_recording"
    ):
        return ""

    details = []

    recording_hours = endurance.get(
        "recording_hours"
    )

    if recording_hours:
        details.append(
            "{:,} hrs documented recording".format(
                recording_hours
            )
        )

    pe_cycles = endurance.get(
        "pe_cycles"
    )

    if pe_cycles:
        details.append(
            "{:,} P/E cycles".format(
                pe_cycles
            )
        )

    detail_html = ""

    if details:
        detail_html = (
            '<div class="card-endurance-detail">'
            + " · ".join(details)
            + "</div>"
        )

    return (
        '<div class="card-endurance">'
        '<span class="card-endurance-badge">'
        'High endurance'
        '</span>'
        '{}'
        '</div>'
    ).format(
        detail_html
    )

def is_specialty_card(card):
    endurance = card.get(
        "endurance",
        {}
    )

    if endurance.get(
        "continuous_recording"
    ) is True:
        return True

    return False

def featured_card_sort_key(item):
    card = item["card"]

    speed_classes = card.get(
        "speed_classes",
        {}
    )

    application_rank = {
        None: 0,
        "A1": 1,
        "A2": 2,
    }

    application = speed_classes.get(
        "application"
    )

    uhs = speed_classes.get(
        "uhs"
    )

    video = speed_classes.get(
        "video"
    )

    return (
        is_specialty_card(card),
        -application_rank.get(
            application,
            0
        ),
        -UHS_SPEED_RANK.get(
            uhs,
            0
        ),
        -VIDEO_SPEED_RANK.get(
            video,
            0
        ),
    )

def capacity_featured_sort_key(device, item):
    card = item["card"]

    speed_classes = card.get(
        "speed_classes",
        {}
    )

    application_rank = {
        None: 0,
        "A1": 1,
        "A2": 2,
    }

    application = speed_classes.get(
        "application"
    )

    uhs = speed_classes.get(
        "uhs"
    )

    video = speed_classes.get(
        "video"
    )

    bus = card.get(
        "bus"
    )

    # For ordinary gaming-handheld compatibility,
    # prefer UHS-I when it works instead of rewarding
    # more expensive interfaces the host may not use.
    if device.get("category") == "gaming-handheld":
        bus_rank = {
            "UHS-I": 0,
            "UHS-II": 1,
            "SD Express": 2,
            None: 3,
        }.get(
            bus,
            4,
        )
    else:
        bus_rank = 0

    return (
        is_specialty_card(card),
        bus_rank,
        -application_rank.get(
            application,
            0
        ),
        -UHS_SPEED_RANK.get(
            uhs,
            0
        ),
        -VIDEO_SPEED_RANK.get(
            video,
            0
        ),
        card.get(
            "manufacturer",
            ""
        ),
        card.get(
            "product_family",
            ""
        ),
    )

def select_featured_cards(device, matches):
    profile = CAPACITY_PROFILES.get(
        device["category"]
    )

    if not profile:
        return []

    featured = []
    used_families = set()

    tiers = [
        (
            "Smaller capacity",
            profile["smallest"],
            "A smaller compatible capacity for lighter storage needs."
        ),
        (
            "Balanced capacity",
            profile["recommended"],
            "A practical middle-ground capacity for most users."
        ),
        (
            "More storage",
            profile["more_storage"],
            "More room when you want to keep a larger library installed."
        ),
    ]

    for label, capacity, reason in tiers:
        candidates = [
            item
            for item in matches
            if item["card"]["capacity_gb"] == capacity
        ]

        candidates.sort(
            key=lambda item:
                capacity_featured_sort_key(
                    device,
                    item,
                )
        )

        match = None

        # Prefer some recommendation diversity when
        # there is another similarly suitable family.
        for candidate in candidates:
            card = candidate["card"]

            family_key = (
                card.get("manufacturer"),
                card.get("product_family"),
            )

            if family_key not in used_families:
                match = candidate
                break

        if match is None and candidates:
            match = candidates[0]

        if match:
            card = match["card"]

            used_families.add(
                (
                    card.get("manufacturer"),
                    card.get("product_family"),
                )
            )

            featured.append({
                "label": label,
                "match": match,
                "reason": reason,
            })

    return featured

def format_capacity(capacity_gb):
    if capacity_gb == 1024:
        return "1 TB"

    if capacity_gb > 1024 and capacity_gb % 1024 == 0:
        return f"{capacity_gb // 1024} TB"

    return f"{capacity_gb} GB"

def render_recommendation_card(
        match,
        label=None,
        badge_text="Compatible",
        recommendation_reason=None,
    ):

    card = match["card"]

    badge_text = html.escape(
        badge_text
    )

    manufacturer = html.escape(
        card["manufacturer"]
    )

    family = html.escape(
        card["product_family"]
    )

    form_factor = html.escape(
        card["form_factor"]
    )

    bus_value = card.get(
        "bus"
    )

    bus = (
        html.escape(bus_value)
        if bus_value
        else "BUS Unspecified"
    )

    speed = html.escape(
        build_speed_text(card)
    )

    speed_html = ""

    if speed:
        speed_html = f"""
            <span>{speed}</span>
        """

    endurance_badge = generate_endurance_badge(
        card
    )

    label_html = ""

    if label:
        label_html = f"""
            <p class="recommendation-label">
                {html.escape(label)}
            </p>
        """

    reason_html = ""

    if recommendation_reason:
        reason_html = f"""
            <div class="recommendation-reason">
                {html.escape(recommendation_reason)}
            </div>
        """

    return f"""
    <article class="recommendation-card">
        {label_html}

        <div class="recommendation-top">
            <div>
                <p class="card-capacity">
                    {format_capacity(card["capacity_gb"])}
                </p>

                <h3>
                    {manufacturer} {family}
                </h3>
            </div>

            <span class="compatible-badge">
                {badge_text}
            </span>
        </div>

        <div class="card-specs">
            <span>{form_factor}</span>
            <span>{bus}</span>
            {speed_html}
        </div>

        {reason_html}
        {endurance_badge}

    </article>
    """

def usage_priority(match):
    card = match["card"]

    endurance = card.get(
        "endurance",
        {}
    )

    is_endurance = endurance.get(
        "continuous_recording"
    ) is True

    bus_unspecified = (
        card.get("bus") is None
    )

    return (
        1 if is_endurance else 0,
        1 if bus_unspecified else 0,
        card.get("capacity_gb", 0),
        card.get("manufacturer", ""),
        card.get("product_family", "")
    )

def alternate_priority(match):
    card = match["card"]

    endurance = card.get(
        "endurance",
        {}
    )

    is_endurance = endurance.get(
        "continuous_recording"
    ) is True

    bus = card.get("bus")

    if bus == "UHS-I":
        bus_rank = 0
    elif bus == "UHS-II":
        bus_rank = 1
    elif bus == "SD Express":
        bus_rank = 2
    elif bus is None:
        bus_rank = 4
    else:
        bus_rank = 3

    endurance_rank = 1 if is_endurance else 0

    return (
        endurance_rank,
        bus_rank,
        card.get("capacity_gb", 0),
        card.get("manufacturer", ""),
        card.get("product_family", "")
    )

def generate_capacity_recommendations(device, cards):
    matches = compatible_cards(
        device,
        cards
    )

    if not matches:
        return """
        <div class="empty-state">
            We don't have a verified matching card in
            our catalog yet.
        </div>
        """

    featured = select_featured_cards(
        device,
        matches
    )

    featured_ids = {
        item["match"]["card"]["id"]
        for item in featured
    }

    other_matches = [
        match
        for match in matches
        if match["card"]["id"] not in featured_ids
    ]

    other_matches.sort(
        key=alternate_priority
    )

    profile = CAPACITY_PROFILES.get(
        device["category"],
        {}
    )
    
    minimum_visible_capacity = profile.get(
        "smallest",
        0,
    )
    
    visible_pool = [
        match
        for match in other_matches
        if match["card"].get(
            "capacity_gb",
            0,
        ) >= minimum_visible_capacity
    ]
    
    visible_other_matches = visible_pool[:3]
    
    visible_ids = {
        match["card"]["id"]
        for match in visible_other_matches
    }
    
    hidden_other_matches = [
        match
        for match in other_matches
        if match["card"]["id"] not in visible_ids
    ]

    output = ""

    if featured:
        output += """
        <div class="featured-recommendations">
        """

        for item in featured:
            output += render_recommendation_card(
                item["match"],
                item["label"],
                recommendation_reason=item[
                    "reason"
                ],
            )

        output += """
        </div>
        """

    if visible_other_matches:
        output += """
        <div class="other-compatible">
            <h3>Other compatible cards</h3>

            <div class="other-compatible-grid">
        """

        for match in visible_other_matches:
            output += render_recommendation_card(
                match
            )

        output += """
            </div>
        </div>
        """

    if hidden_other_matches:
        output += f"""
        <details class="all-compatible-cards">
            <summary>
                Show {len(hidden_other_matches)}
                more compatible cards
            </summary>

            <div class="other-compatible-grid">
        """

        for match in hidden_other_matches:
            output += render_recommendation_card(
                match
            )

        output += """
            </div>
        </details>
        """

    return output

def generate_usage_recommendations(device, cards):
    matches = compatible_cards(
        device,
        cards
    )

    if not matches:
        return """
        <div class="empty-state">
            We don't have a verified matching card in
            our catalog yet.
        </div>
        """

    profiles = [
        profile
        for profile in device.get(
            "usage_profiles",
            []
        )
        if (
            profile.get("requirements")
            or profile.get(
                "requirements_any_of"
            )
        )
    ]

    output = ""

    if not profiles:
        output += """
        <div class="other-compatible">
            <h3>Compatible cards</h3>
            <div class="other-compatible-grid">
        """

        for match in matches:
            output += render_recommendation_card(
                match
            )

        output += """
            </div>
        </div>
        """

        return output

    for profile in profiles:
        profile_matches = []

        for match in matches:
            card = match["card"]

            if card_meets_requirement_set(
                card,
                profile.get(
                    "requirements",
                    {}
                ),
                profile.get(
                    "requirements_any_of",
                    []
                ),
            ):
                profile_matches.append(match)

        if not profile_matches:
            continue
            
        profile_matches.sort(
            key=usage_priority
        )

        visible_profile_matches = profile_matches[:6]
        hidden_profile_matches = profile_matches[6:]

        output += f"""
        <div class="usage-recommendation-group">
            <h3>
                {html.escape(profile["label"])}
            </h3>

            <div class="usage-recommendation-grid">
        """

        for match in visible_profile_matches:
            output += render_recommendation_card(
                match
            )

        output += """
            </div>
        """

        if hidden_profile_matches:
            output += f"""
            <details class="all-compatible-cards">
                <summary>
                    Show {len(hidden_profile_matches)}
                    more cards for this mode
                </summary>

                <div class="usage-recommendation-grid">
            """

            for match in hidden_profile_matches:
                output += render_recommendation_card(
                    match
                )

            output += """
                </div>
            </details>
            """

        output += """
        </div>
        """
  
    return output
  

def generate_application_recommendations(device, cards):
    matches = compatible_cards(
        device,
        cards
    )

    if not matches:
        return """
        <div class="empty-state">
            We don't have a verified matching card in
            our catalog yet.
        </div>
        """

    preferred = []
    others = []

    for match in matches:
        application_class = match["card"].get(
            "speed_classes",
            {}
        ).get("application")

        if application_class == "A2":
            preferred.append(match)
        else:
            others.append(match)

    preferred.sort(
        key=usage_priority
    )

    others.sort(
        key=usage_priority
    )

    visible_preferred = preferred[:6]
    hidden_preferred = preferred[6:]

    visible_others = others[:6]
    hidden_others = others[6:]

    output = ""

    if visible_preferred:
        output += """
        <div class="usage-recommendation-group">
            <h3>Recommended for best responsiveness</h3>

            <div class="usage-recommendation-grid">
        """

        for match in visible_preferred:
            output += render_recommendation_card(
                match
            )

        output += """
            </div>
        </div>
        """

    if hidden_preferred:
        output += f"""
        <details class="all-compatible-cards">
            <summary>
                Show {len(hidden_preferred)}
                more A2 cards
            </summary>

            <div class="usage-recommendation-grid">
        """

        for match in hidden_preferred:
            output += render_recommendation_card(
                match
            )

        output += """
            </div>
        </details>
        """

    if visible_others:
        output += """
        <div class="other-compatible">
            <h3>Other compatible cards</h3>

            <div class="other-compatible-grid">
        """

        for match in visible_others:
            output += render_recommendation_card(
                match
            )

        output += """
            </div>
        </div>
        """

    if hidden_others:
        output += f"""
        <details class="all-compatible-cards">
            <summary>
                Show {len(hidden_others)}
                more compatible cards
            </summary>

            <div class="other-compatible-grid">
        """

        for match in hidden_others:
            output += render_recommendation_card(
                match
            )

        output += """
            </div>
        </details>
        """

    return output

def generate_recommended_spec_recommendations(device, cards):
    matches = compatible_cards(
        device,
        cards
    )

    if not matches:
        return """
        <div class="empty-state">
            We don't have a verified matching card in
            our catalog yet.
        </div>
        """

    slot = device["storage"]["slots"][0]

    recommendations = slot.get(
        "recommendations",
        {}
    )

    # Devices such as Garmin may document hard
    # requirements but no separate recommended spec.
    # For dash-camera use, surface endurance cards
    # separately without calling them manufacturer
    # recommendations.
    if not recommendations:
        endurance_matches = []
        standard_matches = []

        for match in matches:
            endurance = match["card"].get(
                "endurance",
                {}
            )

            if endurance.get(
                "continuous_recording"
            ) is True:
                endurance_matches.append(
                    match
                )
            else:
                standard_matches.append(
                    match
                )

        visible_endurance = endurance_matches[:6]
        hidden_endurance = endurance_matches[6:]

        visible_standard = standard_matches[:6]
        hidden_standard = standard_matches[6:]

        output = ""

        if visible_endurance:
            output += """
            <div class="other-compatible">
                <h3>High-endurance options</h3>

                <div class="other-compatible-grid">
            """

            for match in visible_endurance:
                output += render_recommendation_card(
                    match
                )

            output += """
                </div>
            </div>
            """

        if hidden_endurance:
            output += f"""
            <details class="all-compatible-cards">
                <summary>
                    Show {len(hidden_endurance)}
                    more high-endurance cards
                </summary>

                <div class="other-compatible-grid">
            """

            for match in hidden_endurance:
                output += render_recommendation_card(
                    match
                )

            output += """
                </div>
            </details>
            """

        if visible_standard:
            output += """
            <div class="other-compatible">
                <h3>Other compatible cards</h3>

                <div class="other-compatible-grid">
            """

            for match in visible_standard:
                output += render_recommendation_card(
                    match
                )

            output += """
                </div>
            </div>
            """

        if hidden_standard:
            output += f"""
            <details class="all-compatible-cards">
                <summary>
                    Show {len(hidden_standard)}
                    more compatible cards
                </summary>

                <div class="other-compatible-grid">
            """

            for match in hidden_standard:
                output += render_recommendation_card(
                    match
                )

            output += """
                </div>
            </details>
            """

        return output

    recommendation_reason = build_recommendation_reason(
        recommendations
    )

    preferred = []
    others = []

    for match in matches:
        card = match["card"]

        if card_meets_recommendations(
            card,
            recommendations
        ):
            preferred.append(
                match
            )
        else:
            others.append(
                match
            )

    others.sort(
        key=lambda match: other_recommendation_sort_key(
            match,
            recommendations
        )
    )

    endurance_recommended = bool(
        recommendations.get(
            "endurance"
        )
    )

    endurance_others = []
    standard_others = []

    for match in others:
        card = match["card"]

        endurance = card.get(
            "endurance",
            {}
        )

        if (
            endurance_recommended
            and endurance.get(
                "continuous_recording"
            ) is True
        ):
            endurance_others.append(
                match
            )
        else:
            standard_others.append(
                match
            )

    visible_preferred = preferred[:6]
    hidden_preferred = preferred[6:]

    visible_endurance = endurance_others[:6]
    hidden_endurance = endurance_others[6:]

    visible_standard = standard_others[:6]
    hidden_standard = standard_others[6:]

    output = ""

    if visible_preferred:
        output += """
        <div class="usage-recommendation-group">
            <h3>Matches manufacturer recommendations</h3>

            <div class="usage-recommendation-grid">
        """

        for match in visible_preferred:
            output += render_recommendation_card(
                match,
                badge_text="Recommended",
                recommendation_reason=recommendation_reason,
            )

        output += """
            </div>
        </div>
        """

    if hidden_preferred:
        output += f"""
        <details class="all-compatible-cards">
            <summary>
                Show {len(hidden_preferred)}
                more recommended cards
            </summary>

            <div class="usage-recommendation-grid">
        """

        for match in hidden_preferred:
            output += render_recommendation_card(
                match,
                badge_text="Recommended",
                recommendation_reason=recommendation_reason,
            )

        output += """
            </div>
        </details>
        """

    if visible_endurance:
        output += """
        <div class="other-compatible">
            <h3>High-endurance alternatives</h3>

            <div class="other-compatible-grid">
        """

        for match in visible_endurance:
            output += render_recommendation_card(
                match
            )

        output += """
            </div>
        </div>
        """

    if hidden_endurance:
        output += f"""
        <details class="all-compatible-cards">
            <summary>
                Show {len(hidden_endurance)}
                more high-endurance alternatives
            </summary>

            <div class="other-compatible-grid">
        """

        for match in hidden_endurance:
            output += render_recommendation_card(
                match
            )

        output += """
            </div>
        </details>
        """

    if visible_standard:
        output += """
        <div class="other-compatible">
            <h3>Other compatible cards</h3>

            <div class="other-compatible-grid">
        """

        for match in visible_standard:
            output += render_recommendation_card(
                match
            )

        output += """
            </div>
        </div>
        """

    if hidden_standard:
        output += f"""
        <details class="all-compatible-cards">
            <summary>
                Show {len(hidden_standard)}
                more compatible cards
            </summary>

            <div class="other-compatible-grid">
        """

        for match in hidden_standard:
            output += render_recommendation_card(
                match
            )

        output += """
            </div>
        </details>
        """

    return output

def other_recommendation_sort_key(
    match,
    recommendations,
):
    card = match["card"]

    match_count = 0
    non_endurance_matches = 0
    non_endurance_total = 0

    recommended_uhs = recommendations.get(
        "uhs_speed_class"
    )

    if recommended_uhs:
        non_endurance_total += 1

        card_uhs = card.get(
            "speed_classes",
            {}
        ).get("uhs")

        if (
            card_uhs
            and UHS_SPEED_RANK.get(card_uhs, 0)
            >= UHS_SPEED_RANK.get(
                recommended_uhs,
                0
            )
        ):
            match_count += 1
            non_endurance_matches += 1

    recommended_video = recommendations.get(
        "video_speed_class"
    )

    if recommended_video:
        non_endurance_total += 1

        card_video = card.get(
            "speed_classes",
            {}
        ).get("video")

        if (
            card_video
            and VIDEO_SPEED_RANK.get(card_video, 0)
            >= VIDEO_SPEED_RANK.get(
                recommended_video,
                0
            )
        ):
            match_count += 1
            non_endurance_matches += 1

    recommended_application = recommendations.get(
        "application_class"
    )

    if recommended_application:
        non_endurance_total += 1

        card_application = card.get(
            "speed_classes",
            {}
        ).get("application")

        if card_application == recommended_application:
            match_count += 1
            non_endurance_matches += 1

    endurance_match = False

    if recommendations.get(
        "endurance"
    ):
        endurance_match = (
            card_matches_endurance_recommendation(
                card,
                recommendations
            )
        )

        if endurance_match:
            match_count += 1

    all_non_endurance_match = (
        non_endurance_total > 0
        and non_endurance_matches
        == non_endurance_total
    )

    if endurance_match:
        tier = 0
    elif all_non_endurance_match:
        tier = 1
    else:
        tier = 2

    return (
        tier,
        -match_count,
        card.get(
            "capacity_gb",
            0
        ),
        card.get(
            "manufacturer",
            ""
        ),
        card.get(
            "product_family",
            ""
        ),
    )

def card_meets_recommendations(card, recommendations):
    recommendations = recommendations or {}

    recommended_uhs = recommendations.get(
        "uhs_speed_class"
    )

    if recommended_uhs:
        card_uhs = card.get(
            "speed_classes",
            {}
        ).get("uhs")

        if not card_uhs:
            return False

        if UHS_SPEED_RANK.get(card_uhs, 0) < \
                UHS_SPEED_RANK.get(recommended_uhs, 0):
            return False

    recommended_video = recommendations.get(
        "video_speed_class"
    )

    if recommended_video:
        card_video = card.get(
            "speed_classes",
            {}
        ).get("video")

        if not card_video:
            return False

        if VIDEO_SPEED_RANK.get(card_video, 0) < \
                VIDEO_SPEED_RANK.get(recommended_video, 0):
            return False

    recommended_application = recommendations.get(
        "application_class"
    )

    if recommended_application:
        card_application = card.get(
            "speed_classes",
            {}
        ).get("application")

        if card_application != recommended_application:
            return False

    recommended_endurance = recommendations.get(
        "endurance"
    )

    if recommended_endurance:
        if not card_matches_endurance_recommendation(
            card,
            recommendations
        ):
            return False

    recommended_sd = recommendations.get(
        "minimum_sd_speed_class"
    )

    if recommended_sd:
        card_sd = card.get(
            "speed_classes",
            {}
        ).get("sd")

        if not card_sd:
            return False

        if SD_SPEED_RANK.get(card_sd, 0) < \
                SD_SPEED_RANK.get(recommended_sd, 0):
            return False

    recommended_express = recommendations.get(
        "minimum_sd_express_speed_class"
    )

    if recommended_express:
        card_express = card.get(
            "speed_classes",
            {}
        ).get("express")

        if not card_express:
            return False

        if SD_EXPRESS_SPEED_RANK.get(card_express, 0) < \
                SD_EXPRESS_SPEED_RANK.get(
                    recommended_express,
                    0
                ):
            return False

    return True

def card_matches_endurance_recommendation(
    card,
    recommendations,
):
    endurance_rec = recommendations.get(
        "endurance",
        {}
    )

    if not endurance_rec:
        return False

    card_endurance = card.get(
        "endurance",
        {}
    )

    if endurance_rec.get(
        "continuous_recording"
    ) is True:
        return (
            card_endurance.get(
                "continuous_recording"
            ) is True
        )

    return False

def generate_card_recommendations(device, cards):
    strategy = DEVICE_RECOMMENDATION_OVERRIDES.get(
        device["id"],
        RECOMMENDATION_STRATEGIES.get(
            device["category"],
            "usage"
        )
    )

    if strategy == "capacity":
        return generate_capacity_recommendations(
            device,
            cards
        )

    if strategy == "application":
        return generate_application_recommendations(
            device,
            cards
        )

    if strategy == "recommended-spec":
        return generate_recommended_spec_recommendations(
            device,
            cards
        )

    return generate_usage_recommendations(
        device,
        cards
    )
    
def generate_setup_requirements(slot):
    setup = slot.get(
        "setup_requirements",
        {}
    )

    filesystem = setup.get(
        "filesystem"
    )

    if not filesystem:
        return ""

    return """
    <div class="requirement">
        <span class="requirement-label">
            Formatting
        </span>

        <strong>
            {} required
        </strong>
    </div>
    """.format(
        html.escape(filesystem)
    )

def get_interface_display(slot):
    required_bus = slot.get(
        "requirements",
        {}
    ).get(
        "required_bus"
    )

    if required_bus:
        return (
            "Required interface",
            required_bus
        )

    buses = slot.get(
        "bus_support",
        []
    )

    if buses:
        return (
            "Host interface",
            format_list(buses)
        )

    return (
        "Interface",
        "Not specified by manufacturer"
    )

def generate_requirements_summary(device):
    slot = device["storage"]["slots"][0]
    
    setup_html = generate_setup_requirements(
        slot
    )

    formats = format_list(
        slot.get("accepted_formats", [])
    )

    interface_label, interface_value = \
        get_interface_display(slot)

    min_capacity = slot.get(
        "min_capacity_gb"
    )

    max_capacity = slot.get(
        "max_capacity_gb"
    )
    
    if (
        min_capacity is not None
        and max_capacity is not None
    ):
        capacity = "{} to {}".format(
            format_capacity(min_capacity),
            format_capacity(max_capacity)
        )
    
    elif max_capacity is not None:
        capacity = "Up to {}".format(
            format_capacity(max_capacity)
        )
    
    elif min_capacity is not None:
        capacity = "At least {}".format(
            format_capacity(min_capacity)
        )
    
    else:
        capacity = "Not specified by manufacturer"

    return f"""
    <div class="requirement-grid">
        <div class="requirement">
            <span class="requirement-label">
                Card type
            </span>

            <strong>
                {html.escape(formats)}
            </strong>
        </div>

        <div class="requirement">
            <span class="requirement-label">
                {html.escape(interface_label)}
            </span>

            <strong>
               {html.escape(interface_value)}
            </strong>
        </div>

        <div class="requirement">
            <span class="requirement-label">
                Capacity
            </span>

            <strong>
                {html.escape(capacity)}
            </strong>
        </div>
        
        {setup_html}
    </div>
    """

def requirement_text(requirements):
    requirements = requirements or {}

    values = []

    required_bus = requirements.get(
        "required_bus"
    )

    minimum_uhs_bus = requirements.get(
        "minimum_uhs_bus"
    )

    sd = requirements.get(
        "minimum_sd_speed_class"
    )

    uhs = requirements.get(
        "minimum_uhs_speed_class"
    )

    video = requirements.get(
        "minimum_video_speed_class"
    )

    application = requirements.get(
        "minimum_application_class"
    )

    express = requirements.get(
        "minimum_sd_express_speed_class"
    )

    if required_bus:
        values.append(
            "{} required".format(
                required_bus
            )
        )

    if minimum_uhs_bus:
        values.append(
            "{} or newer UHS interface".format(
                minimum_uhs_bus
            )
        )

    if sd:
        values.append(
            "{} or better".format(
                sd
            )
        )

    if uhs:
        values.append(
            "{} or better".format(
                uhs
            )
        )

    if video:
        values.append(
            "{} or better".format(
                video
            )
        )

    if application:
        values.append(
            "{} or better".format(
                application
            )
        )

    if express:
        values.append(
            "{} or better".format(
                express
            )
        )

    return " AND ".join(values)

def generate_usage_profiles(device):
    profiles = device.get(
        "usage_profiles",
        []
    )

    useful_profiles = []

    for profile in profiles:
        requirements = profile.get(
            "requirements",
            {}
        )

        requirements_any_of = profile.get(
            "requirements_any_of",
            []
        )

        if requirements or requirements_any_of:
            useful_profiles.append(profile)

    if not useful_profiles:
        return ""

    rows = ""

    for profile in useful_profiles:
        requirements = profile[
            "requirements"
        ]

        requirement_parts = []

        base_requirement_text = requirement_text(
            requirements
        )

        if base_requirement_text:
            requirement_parts.append(
                base_requirement_text
            )

        requirements_any_of = profile.get(
            "requirements_any_of",
            []
        )

        if requirements_any_of:
            option_texts = []

            for option in requirements_any_of:
                text = requirement_text(
                    option
                )

                if text:
                    option_texts.append(
                        text
                    )

            if option_texts:
                option_display = " OR ".join(
                    option_texts
                )

                if base_requirement_text:
                    option_display = (
                        "("
                        + option_display
                        + ")"
                    )

                requirement_parts.append(
                    option_display
                )

        requirement_display = " AND ".join(
            requirement_parts
        )

        rows += f"""
        <div class="usage-row">
            <span>
                {html.escape(profile["label"])}
            </span>

            <strong>
                {html.escape(requirement_display)}
            </strong>
        </div>
        """

    return f"""
    <section class="device-section">
        <div class="section-heading">
            <p class="eyebrow">
                PERFORMANCE
            </p>

            <h2>
                Requirements by use
            </h2>

            <p>
                Some activities require faster cards
                than basic device compatibility alone.
            </p>
        </div>

        <div class="usage-list">
            {rows}
        </div>
    </section>
    """


def generate_technical_details(device):
    slots_html = ""

    for slot in device["storage"]["slots"]:
        formats = format_list(
            slot.get(
                "accepted_formats",
                []
            )
        )

        interface_label, interface_value = \
            get_interface_display(slot)

        max_capacity = slot.get(
            "max_capacity_gb"
        )

        if max_capacity is None:
            capacity = \
                "Not specified by manufacturer"
        else:
            capacity = f"{max_capacity} GB"

        slots_html += f"""
        <article class="technical-slot">
            <h3>
                Slot {slot["slot"]}
            </h3>

            <dl>
                <dt>Accepted formats</dt>
                <dd>
                    {html.escape(formats)}
                </dd>

                <dt>
                    {html.escape(interface_label)}
                </dt>
                <dd>
                    {html.escape(interface_value)}
                </dd>

                <dt>Maximum capacity</dt>
                <dd>
                    {html.escape(capacity)}
                </dd>
            </dl>
        </article>
        """

    return slots_html


def generate_sources(device):
    output = ""

    for source in device.get(
        "sources",
        []
    ):
        title = html.escape(
            source["title"]
        )

        publisher = html.escape(
            source["publisher"]
        )

        url = html.escape(
            source["url"],
            quote=True
        )

        output += f"""
        <li>
            <a
                href="{url}"
                rel="nofollow"
            >
                {title}
            </a>

            <span>
                {publisher}
            </span>
        </li>
        """

    return output

def format_category(category):
    return category.replace(
        "-",
        " "
    ).title()

def generate_related_devices(device, devices):
    related_ids = device.get(
        "related_devices",
        []
    )

    if not related_ids:
        return ""

    device_lookup = {
        item["id"]: item
        for item in devices
    }

    related = []

    for related_id in related_ids:
        related_device = device_lookup.get(
            related_id
        )

        if related_device:
            related.append(
                related_device
            )

    if not related:
        return ""

    cards = ""

    for related_device in related:
        manufacturer = html.escape(
            related_device["manufacturer"]
        )

        model = html.escape(
            related_device["model"]
        )

        category = html.escape(
            format_category(
                related_device["category"]
            )
        )

        cards += f"""
        <a
            class="related-device-card"
            href="/device/{related_device["id"]}/"
        >
            <span class="related-device-category">
                {category}
            </span>

            <strong>
                {manufacturer} {model}
            </strong>

            <span class="related-device-link">
                View compatibility →
            </span>
        </a>
        """

    return f"""
    <section class="device-section related-devices">
        <div class="section-heading">
            <p class="eyebrow">
                RELATED DEVICES
            </p>

            <h2>
                Similar devices
            </h2>

            <p>
                Compare SD card compatibility with
                related models.
            </p>
        </div>

        <div class="related-device-grid">
            {cards}
        </div>
    </section>
    """

def generate_device_page(device, cards, devices):
    strategy = DEVICE_RECOMMENDATION_OVERRIDES.get(
        device["id"],
        RECOMMENDATION_STRATEGIES.get(
            device["category"],
            "usage"
        )
    )

    if strategy == "capacity":
        recommendation_intro = (
            "A few sensible choices depending on "
            "how much storage you want."
        )

    elif strategy == "application":
        recommendation_intro = (
            "Compatible cards, with faster application-class "
            "options highlighted for better responsiveness."
        )

    elif strategy == "recommended-spec":
        slot = device["storage"]["slots"][0]
    
        recommendations = slot.get(
            "recommendations",
            {}
        )

        if recommendations:
            recommendation_intro = (
                "Compatible cards, with options that match the "
                "manufacturer's recommended specifications highlighted."
            )
        else:
            recommendation_intro = (
                "Compatible cards that meet the manufacturer's "
                "documented requirements."
            )

    elif strategy == "usage":
        recommendation_intro = (
            "Cards that meet the requirements for "
            "different ways you use this device."
        )

    else:
        recommendation_intro = (
            "Compatible SD card options for this device."
        )

    device_dir = (
        DIST
        / "device"
        / device["id"]
    )

    device_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    manufacturer = html.escape(
        device["manufacturer"]
    )

    model = html.escape(
        device["model"]
    )

    category = html.escape(
        device["category"]
        .replace("-", " ")
        .title()
    )

    recommendations = \
        generate_card_recommendations(
            device,
            cards
        )

    requirements = \
        generate_requirements_summary(
            device
        )

    usage_profiles = \
        generate_usage_profiles(
            device
        )

    technical = \
        generate_technical_details(
            device
        )

    sources = \
        generate_sources(
            device
        )

    related_devices = generate_related_devices(
        device,
        devices
        )

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>
        {manufacturer} {model} SD Card Compatibility |
        SD Card Finder
    </title>

    <meta
        name="description"
        content="Compatible SD cards for the {manufacturer} {model}: supported formats, speed requirements, capacity limits, and sensible card recommendations."
    >
    <link
        rel="icon"
        href="/assets/favicon.svg"
        type="image/svg+xml"
    >

    <link
        rel="canonical"
        href="{SITE_URL}/device/{device["id"]}/"
    >

    <link
        rel="stylesheet"
        href="/css/style.css"
    >
</head>

<body>

<header class="site-header">
    <a class="brand" href="/">
        SD Card Finder
    </a>
</header>

<main class="device-page">

    <nav class="breadcrumb">
        <a href="/">
            SD Card Finder
        </a>

        <span>›</span>

        <span>
            {manufacturer} {model}
        </span>
    </nav>

    <section class="device-hero">
        <p class="eyebrow">
            <a
                class="category-link"
                href="/devices/#{html.escape(device['category'])}"
            >
                {category}
            </a>
        </p>
    
        <h1>
            {manufacturer} {model}
        </h1>

        <p class="device-intro">
            Use the verified requirements below to choose
            an SD card for the {manufacturer} {model}, then
            compare sensible capacity and performance options.
        </p>
    </section>

    <section class="answer-panel">

        <div class="answer-heading">
            <span class="answer-check">
                ✓
            </span>

            <div>
                <p class="answer-label">
                    WHAT YOU NEED
                </p>

                <h2>
                    Compatible SD card specifications
                </h2>
            </div>
        </div>

        {requirements}

    </section>

    <section class="device-section">

        <div class="section-heading">
            <p class="eyebrow">
                COMPATIBLE CARDS
            </p>

            <h2>
                Cards that fit
            </h2>

            <p>
                {recommendation_intro}
            </p>
        </div>

        <div class="recommendation-grid">
            {recommendations}
        </div>

        <p class="recommendation-note">
            Compatibility does not necessarily mean
            every card is the best value or supports
            every specialized recording mode.
        </p>

    </section>

    {usage_profiles}

    <section class="device-section">

        <details class="technical-details">
            <summary>
                Technical compatibility
            </summary>

            <div class="technical-grid">
                {technical}
            </div>
        </details>

    {related_devices}

    <section class="device-section sources-section">

        <div class="section-heading">
            <p class="eyebrow">
                VERIFIED SOURCES
            </p>

            <h2>
                Manufacturer documentation
            </h2>
        </div>

        <ul class="source-list">
            {sources}
        </ul>

    </section>

</main>

<footer class="site-footer">
    <p>
        <a href="/devices/">
			Devices
		</a>
		·
		<a href="/about/">
			About & Methodology
		</a>
		·
		<a href="/privacy/">
			Privacy
		</a>
    </p>
    <p>
        Compatibility information is based on
        manufacturer documentation and published
        SD card specifications.
    </p>
</footer>

</body>
</html>
"""

    output_file = \
        device_dir / "index.html"

    output_file.write_text(
        page,
        encoding="utf-8"
    )

    print(
        f"Generated: device/{device['id']}/"
    )

def generate_robots_txt():
    content = f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""

    (DIST / "robots.txt").write_text(
        content,
        encoding="utf-8"
    )

    print("Generated: robots.txt")


def generate_sitemap(devices):
    urls = [
        f"{SITE_URL}/",
        f"{SITE_URL}/devices/",
        f"{SITE_URL}/about/",
        f"{SITE_URL}/privacy/",
    ]

    for device in devices:
        urls.append(
            f"{SITE_URL}/device/{device['id']}/"
        )

    url_entries = ""

    for url in urls:
        url_entries += f"""
    <url>
        <loc>{html.escape(url)}</loc>
    </url>
"""

    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset
    xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
>
{url_entries}
</urlset>
"""

    (DIST / "sitemap.xml").write_text(
        sitemap,
        encoding="utf-8"
    )

    print("Generated: sitemap.xml")

def generate_about_page():
    about_dir = DIST / "about"
    about_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    canonical_url = f"{SITE_URL}/about/"

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>
        About & Methodology | SD Card Finder
    </title>

    <meta
        name="description"
        content="Learn how SD Card Finder researches device compatibility, evaluates SD card specifications, and generates recommendations."
    >

    <link
        rel="canonical"
        href="{canonical_url}"
    >

    <link
        rel="stylesheet"
        href="/css/style.css"
    >
</head>

<body>

<header class="site-header">
    <a class="brand" href="/">
        SD Card Finder
    </a>
</header>

<main class="content-page">

    <nav class="breadcrumb">
        <a href="/">
            SD Card Finder
        </a>

        <span>›</span>

        <span>
            About & Methodology
        </span>
    </nav>

    <section class="content-hero">
        <p class="eyebrow">
            ABOUT
        </p>

        <h1>
            How SD Card Finder works
        </h1>

        <p class="content-intro">
            SD Card Finder is built to answer a simple
            question: what SD card will actually work
            with a specific device?
        </p>
    </section>

    <section class="content-section">
        <h2>
            The basic idea
        </h2>

        <p>
            Device compatibility can be surprisingly
            confusing. Card format, capacity, bus
            interface, speed class, video speed class,
            and application rating can all matter,
            depending on the device.
        </p>

        <p>
            SD Card Finder collects those requirements
            into structured data and compares them
            against documented SD card specifications.
        </p>
    </section>

    <section class="method-grid">

        <article class="method-card">
            <span class="method-step">
                1
            </span>

            <h2>
                Manufacturer facts
            </h2>

            <p>
                Device compatibility information is
                based primarily on documentation from
                the device manufacturer.
            </p>

            <p>
                Card specifications are taken from card
                manufacturer documentation whenever
                possible.
            </p>
        </article>

        <article class="method-card">
            <span class="method-step">
                2
            </span>

            <h2>
                Compatibility rules
            </h2>

            <p>
                SD Card Finder compares device
                requirements with card specifications
                such as format, capacity, interface,
                and speed class.
            </p>

            <p>
                Compatibility logic is kept separate
                from the underlying source data.
            </p>
        </article>

        <article class="method-card">
            <span class="method-step">
                3
            </span>

            <h2>
                Recommendations
            </h2>

            <p>
                Recommendations are derived from
                compatibility and device use cases.
            </p>

            <p>
                For example, a gaming handheld may be
                organized primarily around storage
                capacity, while a camera may require
                different speed classes for different
                recording modes.
            </p>
        </article>

        <article class="method-card">
            <span class="method-step">
                4
            </span>

            <h2>
                Commercial links
            </h2>

            <p>
                SD Card Finder may eventually use
                affiliate links or other commercial
                relationships.
            </p>

            <p>
                Those relationships do not determine
                whether a card is marked compatible.
                Compatibility is based on the technical
                data and rules described above.
            </p>
        </article>

    </section>

    <section class="content-section">
        <h2>
            We leave unknowns unknown
        </h2>

        <p>
            If a manufacturer does not document a
            maximum capacity or other limitation,
            SD Card Finder reports that information
            as unspecified rather than inventing a
            value.
        </p>

        <p>
            Some compatibility conclusions may rely on
            established SD standards or backward
            compatibility rules. When possible, those
            inferences are kept distinct from direct
            manufacturer claims.
        </p>
    </section>

    <section class="content-section">
        <h2>
            Requirements and recommendations are not
            the same thing
        </h2>

        <p>
            A device may accept many cards while only
            requiring a subset of their performance.
            A faster or more expensive card is not
            automatically a better recommendation.
        </p>

        <p>
            SD Card Finder tries to distinguish between
            what a device requires, what it supports,
            and what is practically useful for a
            particular use case.
        </p>
    </section>

    <section class="content-section">
        <h2>
            Sources and verification
        </h2>

        <p>
            Device pages include links to the
            manufacturer documentation used to support
            compatibility information.
        </p>

        <p>
            Records also carry verification dates so
            specifications can be reviewed again as
            manufacturers update products and
            documentation.
        </p>
    </section>

    <section class="content-section">
        <h2>
            Still a growing catalog
        </h2>

        <p>
            SD Card Finder is starting with a small
            number of carefully verified devices and
            cards rather than a large automatically
            generated catalog.
        </p>

        <p>
            Coverage will expand over time while
            keeping the same source-backed approach.
        </p>
    </section>

</main>

<footer class="site-footer">
    <p>
        <a href="/devices/">
			Devices
		</a>
		·
		<a href="/about/">
			About & Methodology
		</a>
		·
		<a href="/privacy/">
			Privacy
		</a>
    </p>
    <p>
        Compatibility information is based on
        manufacturer documentation and published
        SD card specifications.
    </p>
</footer>

</body>
</html>
"""

    output_file = about_dir / "index.html"

    output_file.write_text(
        page,
        encoding="utf-8"
    )

    print("Generated: about/")

def generate_privacy_page():
    privacy_dir = DIST / "privacy"
    privacy_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    canonical_url = f"{SITE_URL}/privacy/"

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>
        Privacy Policy | SD Card Finder
    </title>

    <meta
        name="description"
        content="Privacy information for SD Card Finder."
    >

    <link
        rel="canonical"
        href="{canonical_url}"
    >

    <link
        rel="stylesheet"
        href="/css/style.css"
    >
</head>

<body>

<header class="site-header">
    <a class="brand" href="/">
        SD Card Finder
    </a>
</header>

<main class="content-page">

    <nav class="breadcrumb">
        <a href="/">
            SD Card Finder
        </a>

        <span>›</span>

        <span>
            Privacy Policy
        </span>
    </nav>

    <section class="content-hero">
        <p class="eyebrow">
            PRIVACY
        </p>

        <h1>
            Privacy Policy
        </h1>

        <p class="content-intro">
            SD Card Finder is a simple informational
            website. We do not currently offer user
            accounts, comments, or forms that collect
            personal information directly from visitors.
        </p>
    </section>

    <section class="content-section">
        <h2>
            Information collected automatically
        </h2>

        <p>
            Like most websites, SD Card Finder is served
            through infrastructure that may automatically
            process technical information such as IP
            address, browser type, device type, request
            information, and approximate location.
        </p>

        <p>
            This information may be used for security,
            reliability, traffic measurement, and site
            performance analysis.
        </p>
    </section>

    <section class="content-section">
        <h2>
            Cloudflare
        </h2>

        <p>
            SD Card Finder uses Cloudflare for hosting,
            content delivery, security, and website
            analytics.
        </p>

        <p>
            Cloudflare may process limited technical and
            usage information in connection with these
            services.
        </p>
    </section>

    <section class="content-section">
        <h2>
            Cookies and local storage
        </h2>

        <p>
            SD Card Finder does not currently set its own
            advertising or account-related cookies.
        </p>

        <p>
            Infrastructure providers may use limited
            technical storage or similar mechanisms where
            necessary to provide security, analytics, or
            site functionality.
        </p>
    </section>

    <section class="content-section">
        <h2>
            Affiliate links
        </h2>

        <p>
            SD Card Finder may add affiliate links in the
            future. If affiliate links are used, a retailer
            or affiliate network may receive information
            about a referral when a visitor follows one of
            those links.
        </p>

        <p>
            This policy will be updated if the site's
            tracking or commercial practices materially
            change.
        </p>
    </section>

    <section class="content-section">
        <h2>
            Information we do not currently collect
        </h2>

        <p>
            SD Card Finder does not currently provide user
            accounts, accept payments, or operate a
            newsletter or contact form.
        </p>

        <p>
            We therefore do not intentionally collect
            names, email addresses, payment information,
            or account credentials through the site.
        </p>
    </section>

    <section class="content-section">
        <h2>
            Changes to this policy
        </h2>

        <p>
            This privacy policy may be updated as SD Card
            Finder adds new features, analytics tools, or
            commercial relationships.
        </p>
    </section>

    <section class="content-section">
        <h2>
            Contact
        </h2>

        <p>
            Questions about this privacy policy can be
            sent to:
        </p>

        <p>
            <a href="mailto:jetcatlabs@gmail.com">
                jetcatlabs@gmail.com
            </a>
        </p>
    </section>

</main>

<footer class="site-footer">
    <p>
        <a href="/devices/">
			Devices
		</a>
		·
		<a href="/about/">
			About & Methodology
		</a>
		·
		<a href="/privacy/">
			Privacy
		</a>
    </p>
    <p>
        Compatibility information is based on
        manufacturer documentation and published
        SD card specifications.
    </p>
</footer>

</body>
</html>
"""

    output_file = privacy_dir / "index.html"

    output_file.write_text(
        page,
        encoding="utf-8"
    )

    print("Generated: privacy/")

def generate_404_page():
    page = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>Page Not Found | SD Card Finder</title>

    <meta
        name="robots"
        content="noindex"
    >

    <link
        rel="icon"
        href="/assets/favicon.svg"
        type="image/svg+xml"
    >

    <link
        rel="stylesheet"
        href="/css/style.css"
    >
</head>

<body>

<header class="site-header">
    <a class="brand" href="/">
        SD Card Finder
    </a>
</header>

<main class="not-found-page">

    <section class="not-found-content">
        <p class="eyebrow">
            404
        </p>

        <h1>
            Couldn't find that page.
        </h1>

        <p>
            The device or page you're looking for may
            not exist yet, or the address may have changed.
        </p>

        <a
            class="primary-link"
            href="/"
        >
            Search SD Card Finder
        </a>
    </section>

</main>

<footer class="site-footer">
    <p>
        <a href="/devices/">
			Devices
		</a>
		·
		<a href="/about/">
			About & Methodology
		</a>
		·
		<a href="/privacy/">
			Privacy
		</a>
    </p>
    <p>
        Compatibility information is based on
        manufacturer documentation and published
        SD card specifications.
    </p>
</footer>

</body>
</html>
"""

    (DIST / "404.html").write_text(
        page,
        encoding="utf-8"
    )

    print("Generated: 404.html")

def generate_devices_page(devices):
    devices_dir = DIST / "devices"
    devices_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    canonical_url = f"{SITE_URL}/devices/"

    category_labels = {
        "gaming-handheld": "Gaming handhelds",
        "action-camera": "Action cameras",
        "camera": "Cameras",
        "single-board-computer": "Single-board computers",
        "dash-camera": "Dash cameras"
    }
 
    grouped = {}

    for device in devices:
        grouped.setdefault(
            device["category"],
            []
        ).append(device)

    category_sections = ""

    for category, label in category_labels.items():
        category_devices = grouped.get(
            category,
            []
        )

        if not category_devices:
            continue

        cards = ""

        for device in sorted(
            category_devices,
            key=lambda item: (
                item["manufacturer"].lower(),
                item["model"].lower()
            )
        ):
            name = html.escape(
                f'{device["manufacturer"]} {device["model"]}'
            )

            cards += f"""
            <a
                class="catalog-device-card"
                href="/device/{device["id"]}/"
            >
                <span class="catalog-device-name">
                    {name}
                </span>

                <span class="catalog-device-link">
                    View compatibility →
                </span>
            </a>
            """

        category_sections += f"""
        <section
            class="catalog-category"
            id="{category}"
        >
            <div class="section-heading">
                <p class="eyebrow">
                    {html.escape(label)}
                </p>

                <h2>
                    {html.escape(label)}
                </h2>

                <p>
                    {len(category_devices)}
                    {"device" if len(category_devices) == 1 else "devices"}
                </p>
            </div>

            <div class="catalog-device-grid">
                {cards}
            </div>
        </section>
        """

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>
        Supported Devices | SD Card Finder
    </title>

    <meta
        name="description"
        content="Browse devices with verified SD card compatibility information, grouped by category."
    >

    <link
        rel="canonical"
        href="{canonical_url}"
    >

    <link
        rel="icon"
        href="/assets/favicon.svg"
        type="image/svg+xml"
    >

    <link
        rel="stylesheet"
        href="/css/style.css"
    >
</head>

<body>

<header class="site-header">
    <a class="brand" href="/">
        SD Card Finder
    </a>
</header>

<main class="content-page catalog-page">

    <nav class="breadcrumb">
        <a href="/">
            SD Card Finder
        </a>

        <span>›</span>

        <span>
            Devices
        </span>
    </nav>

    <section class="content-hero">
        <p class="eyebrow">
            DEVICE CATALOG
        </p>

        <h1>
            Browse supported devices
        </h1>

        <p class="content-intro">
            Explore devices with compatibility information
            verified against manufacturer documentation.
        </p>
    </section>

    <nav class="category-nav">
        <a href="#gaming-handheld">
            Gaming handhelds
        </a>

        <a href="#action-camera">
            Action cameras
        </a>

        <a href="#camera">
            Cameras
        </a>

        <a href="#single-board-computer">
            Single-board computers
        </a>
        
        <a href="#dash-camera">
            Dash cameras
        </a>
    </nav>

    {category_sections}

</main>

<footer class="site-footer">
    <p>
        <a href="/devices/">
            Devices
        </a>
        ·
        <a href="/about/">
            About & Methodology
        </a>
        ·
        <a href="/privacy/">
            Privacy
        </a>
    </p>

    <p>
        Compatibility information is based on
        manufacturer documentation and published
        SD card specifications.
    </p>
</footer>

</body>
</html>
"""

    (devices_dir / "index.html").write_text(
        page,
        encoding="utf-8"
    )

    print("Generated: devices/")

def build():
    print("Building SD Card Finder...")

    devices = load_json(
        DEVICES_FILE
    )

    cards = load_json(
        CARDS_FILE
    )

    clean_dist()
    copy_static_files()

    generate_devices_page(devices)

    generate_robots_txt()
    generate_sitemap(devices)
    generate_about_page()
    generate_privacy_page()
    generate_404_page()

    for device in devices:
        generate_device_page(
            device,
            cards,
            devices
        )

    print()
    print("Build complete: dist")

if __name__ == "__main__":
    build()