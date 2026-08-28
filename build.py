from pathlib import Path
import json
import shutil
import html


ROOT = Path(__file__).parent
SRC = ROOT / "src"
DIST = ROOT / "dist"

DEVICES_FILE = SRC / "data" / "devices.json"
CARDS_FILE = SRC / "data" / "cards.json"


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


def generate_card_recommendations(device, cards):
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

    output = ""

    for match in matches:
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

        output += f"""
        <article class="recommendation-card">
            <div class="recommendation-top">
                <div>
                    <p class="card-capacity">
                        {card["capacity_gb"]} GB
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

    return output


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
        capacity = f"Up to {max_capacity} GB"

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
                These cards match the documented
                device-level requirements in our
                current catalog.
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

    for device in devices:
        generate_device_page(
            device,
            cards
        )

    print()
    print("Build complete: dist")


if __name__ == "__main__":
    build()