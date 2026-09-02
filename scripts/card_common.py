from device_common import (
    ROOT,
    load_json,
    write_json,
    manufacturer_domains,
    hostname_is_allowed,
)


CARD_CANDIDATES_PATH = (
    ROOT / "research" / "card_candidates.json"
)

RESEARCH_CARDS_DIR = (
    ROOT / "research" / "cards"
)

CARDS_PATH = (
    ROOT / "src" / "data" / "cards.json"
)


FORM_FACTORS = {
    "SD",
    "SDHC",
    "SDXC",
    "microSD",
    "microSDHC",
    "microSDXC",
}

BUSES = {
    "UHS-I",
    "UHS-II",
    "UHS-III",
    "SD Express",
}

UHS_SPEED_CLASSES = {
    "U1",
    "U3",
}

VIDEO_SPEED_CLASSES = {
    "V6",
    "V10",
    "V30",
    "V60",
    "V90",
}

APPLICATION_CLASSES = {
    "A1",
    "A2",
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

def find_card_candidate(card_id):
    candidates = load_json(
        CARD_CANDIDATES_PATH
    )

    for candidate in candidates:
        if candidate.get("id") == card_id:
            return candidate

    return None


def card_research_path(card_id):
    return (
        RESEARCH_CARDS_DIR
        / "{}.json".format(card_id)
    )