import os

import pytz

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_TIMEZONE = pytz.timezone("Europe/Stockholm")

MASTER_VALUE = 2800  # the value of 0LP master
RANK_COLORS = {
    "IRON": "#b5a58b",
    "BRONZE": "#8c523a",
    "SILVER": "#84969b",
    "GOLD": "#f0b753",
    "PLATINUM": "#4a927c",
    "EMERALD": "#48c750",
    "DIAMOND": "#716bf6",
    "MASTER": "#ed5eba",
    "GRANDMASTER": "#ce4039",
    "CHALLENGER": "#40c0de",
}
BOOKMARKS_FILE = os.path.join(
    os.environ.get("HOME") or exit("$HOME env variable not set"),
    ".config",
    "BraveSoftware",
    "Brave-Browser",
    "Default",
    "Bookmarks",
)
ICON_PATH = os.path.join(PROJECT_ROOT, "assets", "icon.png")
