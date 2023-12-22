def is_apex(tier: str) -> bool:
    return tier in ["MASTER", "GRANDMASTER", "CHALLENGER"]


def short_tier(tier: str) -> str:
    return tier[0] if tier != "GRANDMASTER" else "GM"
