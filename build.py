from pathlib import Path
import json
import shutil
import html


ROOT = Path(__file__).parent
SRC = ROOT / "src"
DIST = ROOT / "dist"

DEVICES_FILE = SRC / "data" / "devices.json"


def load_devices():
    with DEVICES_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def clean_dist():
    if DIST.exists():
        shutil.rmtree(DIST)

    DIST.mkdir()


def copy_static_files():
    # Main finder page
    shutil.copy2(
        SRC / "index.html",
        DIST / "index.html"
    )

    # Static directories
    for directory in ["css", "js", "data"]:
        shutil.copytree(
            SRC / directory,
            DIST / directory
        )


def format_list(values):
    if not values:
        return "Not documented"

    return ", ".join(values)


def generate_device_page(device):
    device_dir = DIST / "device" / device["id"]
    device_dir.mkdir(parents=True, exist_ok=True)

    manufacturer = html.escape(device["manufacturer"])
    model = html.escape(device["model"])

    slots_html = ""

    for slot in device["storage"]["slots"]:
        formats = format_list(slot.get("accepted_formats", []))
        buses = format_list(slot.get("bus_support", []))

        max_capacity = slot.get("max_capacity_gb")

        if max_capacity is None:
            max_capacity_text = "No manufacturer-documented maximum"
        else:
            max_capacity_text = f"{max_capacity} GB"

        slots_html += f"""
        <section class="device-slot">
            <h2>Slot {slot["slot"]}</h2>

            <dl>
                <dt>Accepted formats</dt>
                <dd>{html.escape(formats)}</dd>

                <dt>Interface</dt>
                <dd>{html.escape(buses)}</dd>

                <dt>Maximum capacity</dt>
                <dd>{html.escape(max_capacity_text)}</dd>
            </dl>
        </section>
        """

    source_html = ""

    for source in device.get("sources", []):
        title = html.escape(source["title"])
        url = html.escape(source["url"], quote=True)
        publisher = html.escape(source["publisher"])

        source_html += f"""
        <li>
            <a href="{url}">{title}</a>
            — {publisher}
        </li>
        """

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>{manufacturer} {model} SD Card Compatibility | SD Card Finder</title>

    <meta
        name="description"
        content="Find compatible SD cards for the {manufacturer} {model}, including supported formats, interface and capacity information."
    >

    <link rel="stylesheet" href="../../css/style.css">
</head>

<body>
    <main>
        <p>
            <a href="/">← SD Card Finder</a>
        </p>

        <h1>{manufacturer} {model} SD Card Compatibility</h1>

        <p>
            Manufacturer-documented SD card compatibility information
            for the {manufacturer} {model}.
        </p>

        {slots_html}

        <section>
            <h2>Sources</h2>

            <ul>
                {source_html}
            </ul>
        </section>
    </main>
</body>
</html>
"""

    output_file = device_dir / "index.html"

    output_file.write_text(
        page,
        encoding="utf-8"
    )

    print(f"Generated: device/{device['id']}/")


def build():
    print("Building SD Card Finder...")

    devices = load_devices()

    clean_dist()
    copy_static_files()

    for device in devices:
        generate_device_page(device)

    print()
    print(f"Build complete: {DIST}")


if __name__ == "__main__":
    build()