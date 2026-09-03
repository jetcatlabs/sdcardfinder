const ALLOWED_EVENTS = new Set([
    "device_selected",
    "show_more_cards",
    "technical_details_open",
    "source_click",
    "merchant_click"
]);

function clean(value, maxLength = 160) {
    if (typeof value !== "string") {
        return "";
    }

    return value
        .trim()
        .slice(0, maxLength);
}

async function handleEvent(request, env) {
    if (request.method !== "POST") {
        return new Response(null, {
            status: 405,
            headers: {
                "Allow": "POST"
            }
        });
    }

    const origin =
        request.headers.get("Origin");

    if (origin) {
        try {
            if (
                new URL(origin).origin !==
                new URL(request.url).origin
            ) {
                return new Response(null, {
                    status: 403
                });
            }
        } catch {
            return new Response(null, {
                status: 403
            });
        }
    }

    let body;

    try {
        body = await request.json();
    } catch {
        return new Response(null, {
            status: 400
        });
    }

    const event = clean(
        body.event,
        64
    );

    if (!ALLOWED_EVENTS.has(event)) {
        return new Response(null, {
            status: 400
        });
    }

    env.EVENTS.writeDataPoint({
        indexes: [
            event
        ],
        blobs: [
            clean(body.page, 200),
            clean(body.device_id, 100),
            clean(body.detail, 160)
        ],
        doubles: [
            1
        ]
    });

    return new Response(null, {
        status: 204,
        headers: {
            "Cache-Control": "no-store"
        }
    });
}

export default {
    async fetch(request, env) {
        const url =
            new URL(request.url);

        if (
            url.pathname === "/api/event"
        ) {
            return handleEvent(
                request,
                env
            );
        }

        if (
            url.pathname.startsWith(
                "/api/"
            )
        ) {
            return new Response(null, {
                status: 404
            });
        }

        return env.ASSETS.fetch(
            request
        );
    }
};