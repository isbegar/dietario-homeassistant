"""Constantes de la integración Dietario."""
from datetime import timedelta

DOMAIN = "dietario"
PLATFORMS = ["sensor", "calendar", "todo"]
SCAN_INTERVAL = timedelta(minutes=5)

CONF_URL = "url"
CONF_TOKEN = "token"

SLOT_LUNCH = "lunch"
SLOT_DINNER = "dinner"
SLOT_NAMES = {SLOT_LUNCH: "Comida", SLOT_DINNER: "Cena"}
# Horas a las que aparecen las comidas en el calendario (hora local de Home Assistant).
SLOT_TIMES = {SLOT_LUNCH: ((14, 0), (15, 30)), SLOT_DINNER: ((21, 0), (22, 0))}
