import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DEVICES_PATH = (
    ROOT
    / "src"
    / "data"
    / "devices.json"
)

CANDIDATES_PATH = (
    ROOT
    / "research"
    / "candidates.json"
)

RESEARCH_DEVICES_DIR = (
    ROOT
    / "research"
    / "devices"
)


ALLOWED_CATEGORIES = {
    "gaming-handheld",
    "action-camera",
    "camera",
    "single-board-computer",
    "dash-camera",
}

ALLOWED_RESEARCH_STATUSES = {
    "todo",
    "researching",
    "needs-review",
    "verified",
    "published",
    "needs-reverification",
    "blocked",
}

ALLOWED_FORMATS = {
    "SD",
    "SDHC",
    "SDXC",
    "microSD",
    "microSDHC",
    "microSDXC",
}

FILESYSTEMS = {
    "FAT32",
    "exFAT",
}

SD_SPEED_CLASSES = {
    "C2",
    "C4",
    "C6",
    "C10",
}

SD_EXPRESS_SPEED_CLASSES = {
    "E150",
    "E300",
    "E450",
    "E600",
}

ALLOWED_BUSES = {
    "UHS-I",
    "UHS-II",
    "UHS-III",
}

ALLOWED_UHS_SPEED_CLASSES = {
    "U1",
    "U3",
}

ALLOWED_VIDEO_SPEED_CLASSES = {
    "V6",
    "V10",
    "V30",
    "V60",
    "V90",
}

ALLOWED_APPLICATION_CLASSES = {
    "A1",
    "A2",
}

MANUFACTURERS_PATH = (
    ROOT
    / "research"
    / "manufacturers.json"
)


def manufacturer_domains(manufacturer):
    manufacturers = load_json(
        MANUFACTURERS_PATH
    )

    return manufacturers.get(
        manufacturer,
        []
    )


def hostname_is_allowed(hostname, allowed_domains):
    hostname = (
        hostname
        .lower()
        .rstrip(".")
    )

    for allowed in allowed_domains:
        allowed = (
            allowed
            .lower()
            .rstrip(".")
        )

        if hostname == allowed:
            return True

        if hostname.endswith(
            "." + allowed
        ):
            return True

    return False


def load_json(path):
    with path.open(
        "r",
        encoding="utf-8"
    ) as handle:
        return json.load(handle)


def write_json(path, data):
    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    with temporary.open(
        "w",
        encoding="utf-8",
        newline="\n"
    ) as handle:
        json.dump(
            data,
            handle,
            indent=2,
            ensure_ascii=False
        )

        handle.write("\n")

    temporary.replace(path)


def find_candidate(candidate_id):
    candidates = load_json(
        CANDIDATES_PATH
    )

    for candidate in candidates:
        if candidate["id"] == candidate_id:
            return candidate

    return None


def research_path(device_id):
    return (
        RESEARCH_DEVICES_DIR
        / "{}.json".format(device_id)
    )