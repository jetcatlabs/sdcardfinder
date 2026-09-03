(function () {
    const LOCAL_HOSTS = new Set([
        "localhost",
        "127.0.0.1"
    ]);

    function deviceIdFromPath(
        pathname = window.location.pathname
    ) {
        const match = pathname.match(
            /^\/device\/([^/]+)\/?$/
        );

        return match
            ? decodeURIComponent(match[1])
            : "";
    }

    function summaryText(details) {
        const summary =
            details.querySelector("summary");

        if (!summary) {
            return "";
        }

        return summary.textContent
            .replace(/\s+/g, " ")
            .trim();
    }

    function track(
        event,
        data = {}
    ) {
        if (
            LOCAL_HOSTS.has(
                window.location.hostname
            )
        ) {
            return;
        }

        const payload = {
            event,
            page: window.location.pathname,
            device_id:
                data.device_id || "",
            detail:
                data.detail || ""
        };

        fetch("/api/event", {
            method: "POST",
            headers: {
                "Content-Type":
                    "application/json"
            },
            body: JSON.stringify(payload),
            credentials: "omit",
            referrerPolicy: "no-referrer",
            keepalive: true
        }).catch(() => {
            /*
             * Analytics must never affect
             * normal site behavior.
             */
        });
    }

    document.addEventListener(
        "click",
        event => {
            const target = event.target;

            if (!(target instanceof Element)) {
                return;
            }

            const deviceLink = target.closest(
                "a.device-result, " +
                "a.featured-device-card"
            );

            if (deviceLink) {
                track(
                    "device_selected",
                    {
                        device_id:
                            deviceIdFromPath(
                                deviceLink.pathname
                            ),
                        detail:
                            deviceLink.classList.contains(
                                "device-result"
                            )
                                ? "search"
                                : "featured"
                    }
                );

                return;
            }

            const sourceLink = target.closest(
                ".source-list a"
            );

            if (sourceLink) {
                let hostname = "";

                try {
                    hostname = new URL(
                        sourceLink.href
                    ).hostname;
                } catch {
                    hostname = "";
                }

                track(
                    "source_click",
                    {
                        device_id:
                            deviceIdFromPath(),
                        detail: hostname
                    }
                );
            }
        }
    );

    document.addEventListener(
        "toggle",
        event => {
            const details = event.target;

            if (
                !(
                    details instanceof
                    HTMLDetailsElement
                )
                || !details.open
            ) {
                return;
            }

            if (
                details.classList.contains(
                    "all-compatible-cards"
                )
            ) {
                track(
                    "show_more_cards",
                    {
                        device_id:
                            deviceIdFromPath(),
                        detail:
                            summaryText(details)
                    }
                );

                return;
            }

            if (
                details.classList.contains(
                    "technical-details"
                )
            ) {
                track(
                    "technical_details_open",
                    {
                        device_id:
                            deviceIdFromPath()
                    }
                );
            }
        },
        true
    );

    window.SDCFAnalytics = {
        track
    };
})();