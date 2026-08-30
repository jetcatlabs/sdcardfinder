let devices = [];

const searchInput = document.getElementById("device-search");
const resultsElement = document.getElementById("device-results");
const deviceGrid = document.getElementById("device-grid");

const DEFAULT_RESULT_COUNT = 5;

async function loadDevices() {
    const response = await fetch("/data/devices.json");

    if (!response.ok) {
        throw new Error("Could not load device data.");
    }

    devices = await response.json();

    renderDefaultResults();
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