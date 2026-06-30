import os
import json
import asyncio
from datetime import datetime, timezone

import nats

NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")
SERVICE_NAME = os.getenv("SERVICE_NAME", "service")


async def _envoyer(sujet, contenu):
    # On ouvre une connexion, on publie le message, puis on referme.
    nc = await nats.connect(NATS_URL, connect_timeout=2, max_reconnect_attempts=1)
    await nc.publish(sujet, contenu)
    await nc.flush(timeout=2)
    await nc.close()


def publish_log(level, action, message):
    """Envoie un log sur NATS (sujet logs.<service>). Le log-service les collecte."""
    contenu = json.dumps({
        "service": SERVICE_NAME,
        "level": level,
        "action": action,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }).encode("utf-8")
    try:
        asyncio.run(_envoyer("logs." + SERVICE_NAME, contenu))
    except Exception:
        pass  # si NATS n'est pas disponible, on n'empeche pas l'operation
