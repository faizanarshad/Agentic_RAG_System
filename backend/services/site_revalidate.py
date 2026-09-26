"""Ask the Next.js site to refresh cached pages after content changes (fire-and-forget)."""

import json
import threading
import urllib.request

from core.config import settings
from utils.logger import logger


def revalidate_site(tags, paths=()) -> None:
    if not settings.REVALIDATE_SECRET or not settings.SITE_REVALIDATE_URL:
        return  # time-based revalidation (60 s) still applies

    def send():
        try:
            request = urllib.request.Request(
                settings.SITE_REVALIDATE_URL,
                data=json.dumps({"tags": list(tags), "paths": list(paths)}).encode(),
                headers={"Content-Type": "application/json", "x-revalidate-secret": settings.REVALIDATE_SECRET},
                method="POST",
            )
            urllib.request.urlopen(request, timeout=5).read()
        except Exception as e:
            logger.warning(f"Site revalidation failed: {str(e)}")

    threading.Thread(target=send, daemon=True).start()
