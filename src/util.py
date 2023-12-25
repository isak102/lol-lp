def is_apex(tier: str) -> bool:
    return tier in ["MASTER", "GRANDMASTER", "CHALLENGER"]


def short_tier(tier: str) -> str:
    return tier[0] if tier != "GRANDMASTER" else "GM"


def notif(message: str, duration: int = 999999999):
    import subprocess

    ID = "938104"
    subprocess.Popen(
        [
            "notify-send",
            "-t",
            str(duration),
            "-u",
            "low",
            "-c",
            "no_title",
            " ",
            message,
            "-r",
            ID,
        ]
    )


def transform_riot_id(riot_id: str, region: str) -> str:
    import urllib.parse as urllib

    # TODO: append default tagline ?
    decoded = urllib.unquote(riot_id.replace("-", "#").replace("+", " "))
    return decoded
