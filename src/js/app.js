let devices = [];
let cards = [];

const deviceSelect = document.getElementById("device-select");
const profileSelect = document.getElementById("profile-select");
const cardSelect = document.getElementById("card-select");
const checkButton = document.getElementById("check-button");
const resultElement = document.getElementById("result");

async function loadData() {
    const [deviceResponse, cardResponse] = await Promise.all([
        fetch("data/devices.json"),
        fetch("data/cards.json")
    ]);

    if (!deviceResponse.ok || !cardResponse.ok) {
        throw new Error("Could not load device/card data.");
    }

    devices = await deviceResponse.json();
    cards = await cardResponse.json();

    populateDevices();
    populateCards();
    populateProfiles();
}

function populateDevices() {
    deviceSelect.innerHTML = "";

    for (const device of devices) {
        const option = document.createElement("option");
        option.value = device.id;
        option.textContent = `${device.manufacturer} ${device.model}`;

        deviceSelect.appendChild(option);
    }
}

function populateCards() {
    cardSelect.innerHTML = "";

    for (const card of cards) {
        const option = document.createElement("option");
        option.value = card.id;
        option.textContent =
            `${card.manufacturer} ${card.product_family} - ${card.capacity_gb}GB`;

        cardSelect.appendChild(option);
    }
}

function populateProfiles() {
    const device = getSelectedDevice();

    profileSelect.innerHTML = "";

    const defaultOption = document.createElement("option");
    defaultOption.value = "";
    defaultOption.textContent = "General compatibility";

    profileSelect.appendChild(defaultOption);

    for (const profile of device.usage_profiles ?? []) {
        const option = document.createElement("option");
        option.value = profile.id;
        option.textContent = profile.label;

        profileSelect.appendChild(option);
    }
}

function getSelectedDevice() {
    return devices.find(
        device => device.id === deviceSelect.value
    );
}

function getSelectedCard() {
    return cards.find(
        card => card.id === cardSelect.value
    );
}

function displayResults(results) {
    resultElement.innerHTML = "";

    for (const result of results) {
        const container = document.createElement("div");
        container.className = result.compatible
            ? "result compatible"
            : "result incompatible";

        const heading = document.createElement("h2");

        heading.textContent = result.compatible
            ? `Compatible with slot ${result.slot}`
            : `Not compatible with slot ${result.slot}`;

        container.appendChild(heading);

        if (result.failures.length > 0) {
            const failureList = document.createElement("ul");

            for (const failure of result.failures) {
                const item = document.createElement("li");
                item.textContent = failure;
                failureList.appendChild(item);
            }

            container.appendChild(failureList);
        }

        if (result.notes.length > 0) {
            const notesList = document.createElement("ul");

            for (const note of result.notes) {
                const item = document.createElement("li");
                item.textContent = note;
                notesList.appendChild(item);
            }

            container.appendChild(notesList);
        }

        resultElement.appendChild(container);
    }
}

function runCompatibilityCheck() {
    const device = getSelectedDevice();
    const card = getSelectedCard();

    const profileId =
        profileSelect.value || null;

    const results = checkCompatibility(
        device,
        card,
        profileId
    );

    displayResults(results);
}

deviceSelect.addEventListener("change", () => {
    populateProfiles();
    resultElement.innerHTML = "";
});

checkButton.addEventListener(
    "click",
    runCompatibilityCheck
);

loadData().catch(error => {
    console.error(error);

    resultElement.textContent =
        "Failed to load SD Card Finder data.";
});