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

    if not card_meets_requirements(
        card,
        slot.get("requirements", {})
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

def select_featured_cards(device, matches):
    profile = CAPACITY_PROFILES.get(
        device["category"]
    )

    if not profile:
        return []

    featured = []

    tiers = [
        (
            "Smallest option",
            profile["smallest"]
        ),
        (
            "Balanced Capacity",
            profile["recommended"]
        ),
        (
            "More storage",
            profile["more_storage"]
        ),
    ]

    for label, capacity in tiers:
        candidates = [
            item
            for item in matches
            if item["card"]["capacity_gb"] == capacity
        ]
        
        match = min(
            candidates,
            key=featured_card_sort_key,
            default=None
        )

        if match:
            featured.append({
                "label": label,
                "match": match
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

    output = ""

    if featured:
        output += """
        <div class="featured-recommendations">
        """

        for item in featured:
            output += render_recommendation_card(
                item["match"],
                item["label"]
            )

        output += """
        </div>
        """

    if other_matches:
        output += """
        <div class="other-compatible">
            <h3>Other compatible cards</h3>

            <div class="other-compatible-grid">
        """

        for match in other_matches:
            output += render_recommendation_card(
                match
            )

        output += """
            </div>
        </div>
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
        for profile in device.get("usage_profiles", [])
        if profile.get("requirements")
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

            if card_meets_requirements(
                card,
                profile.get("requirements", {})
            ):
                profile_matches.append(match)

        if not profile_matches:
            continue

        output += f"""
        <div class="usage-recommendation-group">
            <h3>
                {html.escape(profile["label"])}
            </h3>

            <div class="usage-recommendation-grid">
        """

        for match in profile_matches:
            output += render_recommendation_card(
                match
            )

        output += """
            </div>
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

    output = ""

    if preferred:
        output += """
        <div class="usage-recommendation-group">
            <h3>Recommended for best responsiveness</h3>

            <div class="usage-recommendation-grid">
        """

        for match in preferred:
            output += render_recommendation_card(
                match
            )

        output += """
            </div>
        </div>
        """

    if others:
        output += """
        <div class="other-compatible">
            <h3>Other compatible cards</h3>

            <div class="other-compatible-grid">
        """

        for match in others:
            output += render_recommendation_card(
                match
            )

        output += """
            </div>
        </div>
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
    
    if not recommendations:
        output = """
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
            preferred.append(match)
        else:
            others.append(match)

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

    output = ""

    if preferred:
        output += """
        <div class="usage-recommendation-group">
            <h3>Matches manufacturer recommendations</h3>

            <div class="usage-recommendation-grid">
        """

        for match in preferred:
            output += render_recommendation_card(
                match,
                badge_text="Recommended",
                recommendation_reason=recommendation_reason,
            )

        output += """
            </div>
        </div>
        """

    if endurance_others:
        output += """
        <div class="other-compatible">
            <h3>High-endurance alternatives</h3>

            <div class="other-compatible-grid">
        """

        for match in endurance_others:
            output += render_recommendation_card(
                match
            )

        output += """
            </div>
        </div>
        """

    if standard_others:
        output += """
        <div class="other-compatible">
            <h3>Other compatible cards</h3>

            <div class="other-compatible-grid">
        """

        for match in standard_others:
            output += render_recommendation_card(
                match
            )

        output += """
            </div>
        </div>
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

def generate_requirements_summary(device):
    slot = device["storage"]["slots"][0]
    
    setup_html = generate_setup_requirements(
        slot
    )

    formats = format_list(
        slot.get("accepted_formats", [])
    )

    buses = format_list(
        slot.get("bus_support", [])
    )

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
                Interface
            </span>

            <strong>
                {html.escape(buses)}
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

        if requirements:
            useful_profiles.append(profile)

    if not useful_profiles:
        return ""

    rows = ""

    for profile in useful_profiles:
        requirements = profile[
            "requirements"
        ]

        values = []

        video = requirements.get(
            "minimum_video_speed_class"
        )

        uhs = requirements.get(
            "minimum_uhs_speed_class"
        )

        if uhs:
            values.append(f"{uhs} or better")

        if video:
            values.append(f"{video} or better")

        rows += f"""
        <div class="usage-row">
            <span>
                {html.escape(profile["label"])}
            </span>

            <strong>
                {html.escape(", ".join(values))}
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

        buses = format_list(
            slot.get(
                "bus_support",
                []
            )
        )

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

                <dt>Interface</dt>
                <dd>
                    {html.escape(buses)}
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
        content="Find compatible SD cards for the {manufacturer} {model}, including supported formats, speeds and capacities."
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
            Here's what to look for when choosing
            an SD card for your device.
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