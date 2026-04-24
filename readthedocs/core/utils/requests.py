import structlog


log = structlog.get_logger(__name__)  # noqa


def is_suspicious_request(request) -> bool:
    """
    Returns True if the request is suspicious.

    This function is used to detect bots and spammers,
    we use Cloudflare to detect them.
    """
    # This header is set from Cloudflare,
    # it goes from 0 to 100, 0 being low risk,
    # and values above 10 are bots/spammers.
    # https://developers.cloudflare.com/ruleset-engine/rules-language/fields/#dynamic-fields.
    threat_score = int(request.headers.get("X-Cloudflare-Threat-Score", 0))
    if threat_score > 10:
        log.info(
            "Suspicious threat score",
            threat_score=threat_score,
        )
        return True
    return False
