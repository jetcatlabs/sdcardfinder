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

RECOMMENDATION_STRATEGIES = {
    "gaming-handheld": "capacity",
    "action-camera": "usage",
    "camera": "usage",
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

    for directory in ["css", "js", "data"]:
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

    return True


def card_fits_slot(card, slot):
    if card.get("form_factor") not in \
            slot.get("accepted_formats", []):
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

    for key in ["uhs", "video", "application"]:
        value = speed_classes.get(key)

        if value:
            values.append(value)

    return " · ".join(values)

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
            "Recommended",
            profile["recommended"]
        ),
        (
            "More storage",
            profile["more_storage"]
        ),
    ]

    for label, capacity in tiers:
        match = next(
            (
                item
                for item in matches
                if item["card"]["capacity_gb"] == capacity
            ),
            None
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

def render_recommendation_card(match, label=None):
    card = match["card"]

    manufacturer = html.escape(
        card["manufacturer"]
    )

    family = html.escape(
        card["product_family"]
    )

    form_factor = html.escape(
        card["form_factor"]
    )

    bus = html.escape(
        card["bus"]
    )

    speed = html.escape(
        build_speed_text(card)
    )

    speed_html = ""

    if speed:
        speed_html = f"""
            <span>{speed}</span>
        """

    label_html = ""

    if label:
        label_html = f"""
            <p class="recommendation-label">
                {html.escape(label)}
            </p>
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
                Compatible
            </span>
        </div>

        <div class="card-specs">
            <span>{form_factor}</span>
            <span>{bus}</span>
            {speed_html}
        </div>
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

def generate_card_recommendations(device, cards):
    strategy = RECOMMENDATION_STRATEGIES.get(
        device["category"],
        "usage"
    )

    if strategy == "capacity":
        return generate_capacity_recommendations(
            device,
            cards
        )

    return generate_usage_recommendations(
        device,
        cards
    )

def generate_requirements_summary(device):
    slot = device["storage"]["slots"][0]

    formats = format_list(
        slot.get("accepted_formats", [])
    )

    buses = format_list(
        slot.get("bus_support", [])
    )

    max_capacity = slot.get(
        "max_capacity_gb"
    )

    if max_capacity is None:
        capacity = "Not specified by manufacturer"
    else:
        capacity = f"Up to {format_capacity(max_capacity)}"

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


def generate_device_page(device, cards):
    strategy = RECOMMENDATION_STRATEGIES.get(
    device["category"],
    "usage"
    )

    if strategy == "capacity":
        recommendation_intro = (
        "A few sensible choices depending on "
        "how much storage you want."
    )
    else:
        recommendation_intro = (
        "Cards that meet the requirements for "
        "different ways you use this device."
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

    strategy = RECOMMENDATION_STRATEGIES.get(
        device["category"],
        "usage"
        )

    if strategy == "capacity":
        recommendation_intro = (
            "A few sensible choices depending on "
            "how much storage you want."
        )
    else:
        recommendation_intro = (
            "Cards that meet the requirements for "
            "different ways you use this device."
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
            {category}
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

    </section>

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
        f"{SITE_URL}/"
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
    
    generate_robots_txt()
    generate_sitemap(devices)

    for device in devices:
        generate_device_page(
            device,
            cards
        )

    print()
    print("Build complete: dist")

def select_featured_cards(device, matches):
    profile = CAPACITY_PROFILES.get(
        device["category"]
    )

    if not profile:
        return []

    by_capacity = {
        item["card"]["capacity_gb"]: item
        for item in matches
    }

    featured = []

    tiers = [
        (
            "Smallest option",
            profile["smallest"]
        ),
        (
            "Recommended",
            profile["recommended"]
        ),
        (
            "More storage",
            profile["more_storage"]
        ),
    ]

    for label, capacity in tiers:
        match = by_capacity.get(capacity)

        if match:
            featured.append({
                "label": label,
                "match": match
            })

    return featured

if __name__ == "__main__":
    build()