/**
 * SD Card Finder compatibility engine
 *
 * Device facts and card facts live in JSON.
 * This file contains the rules for comparing them.
 */

const VIDEO_SPEED_RANK = {
    V6: 6,
    V10: 10,
    V30: 30,
    V60: 60,
    V90: 90
};

const UHS_SPEED_RANK = {
    U1: 1,
    U3: 3
};


/**
 * Returns true when the physical/logical SD format is accepted.
 *
 * Example:
 * Device accepts microSDXC
 * Card is microSDXC
 * -> true
 */
function isFormatCompatible(slot, card) {
    return slot.accepted_formats.includes(card.form_factor);
}


/**
 * Checks a card against a device's documented maximum capacity.
 *
 * Unknown/documentation-missing maximums do NOT cause a failure.
 */
function isCapacityCompatible(slot, card) {
    if (slot.max_capacity_gb === null) {
        return true;
    }

    return card.capacity_gb <= slot.max_capacity_gb;
}


/**
 * Determine whether a card satisfies a minimum Video Speed Class.
 */
function meetsVideoSpeedRequirement(card, minimumClass) {
    if (!minimumClass) {
        return true;
    }

    const cardClass = card.speed_classes?.video;

    if (!cardClass) {
        return false;
    }

    return VIDEO_SPEED_RANK[cardClass] >= VIDEO_SPEED_RANK[minimumClass];
}


/**
 * Determine whether a card satisfies a minimum UHS Speed Class.
 */
function meetsUhsSpeedRequirement(card, minimumClass) {
    if (!minimumClass) {
        return true;
    }

    const cardClass = card.speed_classes?.uhs;

    if (!cardClass) {
        return false;
    }

    return UHS_SPEED_RANK[cardClass] >= UHS_SPEED_RANK[minimumClass];
}


/**
 * Check requirements belonging either to a slot or usage profile.
 */
function checkRequirements(card, requirements = {}) {
    const failures = [];

    if (
        requirements.minimum_video_speed_class &&
        !meetsVideoSpeedRequirement(
            card,
            requirements.minimum_video_speed_class
        )
    ) {
        failures.push(
            `Requires ${requirements.minimum_video_speed_class} or better`
        );
    }

    if (
        requirements.minimum_uhs_speed_class &&
        !meetsUhsSpeedRequirement(
            card,
            requirements.minimum_uhs_speed_class
        )
    ) {
        failures.push(
            `Requires ${requirements.minimum_uhs_speed_class} or better`
        );
    }

    return failures;
}


/**
 * Compare one card with one device slot.
 */
function checkSlotCompatibility(device, slot, card, usageProfile = null) {
    const failures = [];
    const notes = [];

    if (!isFormatCompatible(slot, card)) {
        failures.push(
            `${card.form_factor} is not accepted by this slot`
        );
    }

    if (!isCapacityCompatible(slot, card)) {
        failures.push(
            `${card.capacity_gb}GB exceeds the documented maximum of ${slot.max_capacity_gb}GB`
        );
    }

    failures.push(
        ...checkRequirements(card, slot.requirements)
    );

    if (usageProfile) {
        failures.push(
            ...checkRequirements(card, usageProfile.requirements)
        );
    }

    /*
     * UHS-II cards are backward compatible with UHS-I hosts.
     * They work, but cannot use their full bus performance.
     */
    if (
    failures.length === 0 &&
    card.bus === "UHS-II" &&
    slot.bus_support.includes("UHS-I") &&
    !slot.bus_support.includes("UHS-II")
) {
    notes.push(
        "Compatible, but UHS-II performance is limited by the device's UHS-I interface"
    );
}

    return {
        device_id: device.id,
        slot: slot.slot,
        card_id: card.id,
        usage_profile: usageProfile?.id ?? null,
        compatible: failures.length === 0,
        failures,
        notes
    };
}


/**
 * Check a card against every SD slot in a device.
 */
function checkCompatibility(device, card, usageProfileId = null) {
    let usageProfile = null;

    if (usageProfileId) {
        usageProfile = device.usage_profiles.find(
            profile => profile.id === usageProfileId
        );

        if (!usageProfile) {
            throw new Error(
                `Unknown usage profile: ${usageProfileId}`
            );
        }
    }

    return device.storage.slots.map(slot =>
        checkSlotCompatibility(
            device,
            slot,
            card,
            usageProfile
        )
    );
}