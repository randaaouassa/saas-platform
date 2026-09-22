import structlog

log = structlog.get_logger("notifications.providers")


def send_email(to: str, subject: str, body: str) -> dict:
    log.info("email_sent", to=to, subject=subject, body=body)
    return {"provider": "console", "msg_id": f"email-{to}-{subject[:20]}"}


def send_sms(to: str, body: str) -> dict:
    log.info("sms_sent", to=to, body=body)
    return {"provider": "console", "msg_id": f"sms-{to}"}


def send_push(user_id: str, subject: str, body: str) -> dict:
    log.info("push_sent", user_id=user_id, subject=subject, body=body)
    return {"provider": "console", "msg_id": f"push-{user_id}"}


def dispatch(channel: str, target: str | None, subject: str, body: str) -> dict:
    if channel == "email":
        return send_email(target or "unknown@example.com", subject, body)
    if channel == "sms":
        return send_sms(target or "+0000000000", body)
    if channel == "push":
        return send_push(target or "unknown", subject, body)
    return {"provider": "noop", "msg_id": None}