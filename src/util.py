import subprocess


def is_apex(tier: str) -> bool:
    return tier in ["MASTER", "GRANDMASTER", "CHALLENGER"]


def short_tier(tier: str) -> str:
    return tier[0] if tier != "GRANDMASTER" else "GM"


def notif(message: str, duration: int = 999999999):
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
