let devices = [];

const searchInput = document.getElementById("device-search");
const resultsElement = document.getElementById("device-results");
const deviceGrid = document.getElementById("device-grid");

const DEFAULT_RESULT_COUNT = 5;

const categoryGrid = document.getElementById(
    "category-grid"
);

const featuredGrid = document.getElementById(
    "featured-grid"
);
const CATEGORY_ORDER = [
    "gaming-handheld",
    "action-camera",
    "camera",
    "single-board-computer",
	"dash-camera"
];

const CATEGORY_LABELS = {
    "gaming-handheld": "Gaming handhelds",
    "action-camera": "Action cameras",
    "camera": "Cameras",
    "single-board-computer": "Single-board computers",
	"dash-camera": "Dash cameras"
};

const FEATURED_DEVICE_IDS = [
    "steam-deck-oled",
    "gopro-hero13-black",
    "sony-a7-iv",
    "raspberry-pi-5"
];

async function loadDevices() {
    const response = await fetch("/data/devices.json");

    if (!response.ok) {
        throw new Error("Could not load device data.");
    }

    devices = await response.json();

    renderDefaultResults();
	renderCategoryGrid();
	renderFeaturedDevices();
}


function deviceUrl(device) {
    return `/device/${device.id}/`;
}


function searchableText(device) {
    return [
        device.manufacturer,
        device.model,
        ...(device.aliases ?? [])
    ]
        .join(" ")
        .toLowerCase();
}


function renderSearchResults(matches) {
    resultsElement.innerHTML = "";

    if (matches.length === 0) {
        const empty = document.createElement("div");
        empty.className = "no-results";
        empty.textContent = "No supported devices found yet.";

        resultsElement.appendChild(empty);
        return;
    }

    for (const device of matches) {
        const link = document.createElement("a");

        link.className = "device-result";
        link.href = deviceUrl(device);

        link.innerHTML = `
            <span>
                <strong>${device.manufacturer} ${device.model}</strong>
                <small>${formatCategory(device.category)}</small>
            </span>

            <span class="chevron">›</span>
        `;

        resultsElement.appendChild(link);
    }
}


function renderDeviceGrid() {
    deviceGrid.innerHTML = "";

    for (const device of devices) {
        const link = document.createElement("a");

        link.className = "device-card";
        link.href = deviceUrl(device);

        link.innerHTML = `
            <small>${formatCategory(device.category)}</small>
            <strong>${device.manufacturer} ${device.model}</strong>
            <span>View compatibility →</span>
        `;

        deviceGrid.appendChild(link);
    }
}

function renderCategoryGrid() {
    if (!categoryGrid) {
        return;
    }

    categoryGrid.innerHTML = "";

    for (const category of CATEGORY_ORDER) {
        const matches = devices.filter(
            device => device.category === category
        );

        if (!matches.length) {
            continue;
        }

        const link = document.createElement("a");

        link.className = "category-card";

        link.href =
            `/devices/#${category}`;

        link.innerHTML = `
            <span class="category-card-name">
                ${CATEGORY_LABELS[category]}
            </span>

            <span class="category-card-count">
                ${matches.length}
                ${matches.length === 1 ? "device" : "devices"}
            </span>

            <span class="category-card-link">
                Browse →
            </span>
        `;

        categoryGrid.appendChild(link);
    }
}

function formatCategory(category) {
    return category
        .split("-")
        .map(word =>
            word.charAt(0).toUpperCase() + word.slice(1)
        )
        .join(" ");
}

function renderDefaultResults() {
    renderSearchResults(
        devices.slice(0, DEFAULT_RESULT_COUNT)
    );
}

function renderFeaturedDevices() {
    if (!featuredGrid) {
        return;
    }

    featuredGrid.innerHTML = "";

    for (const id of FEATURED_DEVICE_IDS) {
        const device = devices.find(
            item => item.id === id
        );

        if (!device) {
            continue;
        }

        const link = document.createElement("a");

        link.className = "featured-device-card";
        link.href = deviceUrl(device);

        link.innerHTML = `
            <span class="featured-category">
                ${formatCategory(device.category)}
            </span>

            <strong>
                ${device.manufacturer} ${device.model}
            </strong>

            <span class="featured-link">
                View guide →
            </span>
        `;

        featuredGrid.appendChild(link);
    }
}

searchInput.addEventListener("input", () => {
    const query = searchInput.value
        .trim()
        .toLowerCase();

	if (!query) {
		renderSearchResults(devices.slice(0, 5));
		return;
	}

    const matches = devices.filter(device =>
        searchableText(device).includes(query)
    );

    renderSearchResults(matches);
});


loadDevices().catch(error => {
    console.error(error);

    resultsElement.innerHTML =
        `<div class="no-results">Unable to load devices.</div>`;
});