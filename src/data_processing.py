from sys import maxsize

import src.util as util
from src.config import MASTER_VALUE


def merge_thresholds(all_tresholds: list[list[dict]], region: str) -> list[dict]:
    def set_apex_cutoffs(thresholds: list, region: str):
        master = next((item for item in thresholds if item["tier"] == "MASTER"), None)
        grandmaster = next(
            (item for item in thresholds if item["tier"] == "GRANDMASTER"), None
        )
        challenger = next(
            (item for item in thresholds if item["tier"] == "CHALLENGER"), None
        )

        if master or grandmaster or challenger:
            from src.api import get_apex_cutoffs

            cutoffs = get_apex_cutoffs(region)
            gm_cutoff = MASTER_VALUE + cutoffs["grandmaster"]
            chall_cutoff = MASTER_VALUE + cutoffs["challenger"]

            if master:
                master["minValue"] = MASTER_VALUE
                master["maxValue"] = gm_cutoff

            if master and grandmaster:
                grandmaster["minValue"] = gm_cutoff
                grandmaster["maxValue"] = chall_cutoff

            if master and grandmaster and challenger:
                challenger["minValue"] = chall_cutoff
                challenger["maxValue"] = maxsize

    thresholds = []
    seen = set()
    for lst in all_tresholds:
        for threshold in lst:
            # Create a unique key for each 'tier'-'division' combination
            key = (threshold["tier"], threshold["division"])

            # Add the threshold only if the key hasn't been seen before
            if key not in seen:
                thresholds.append(threshold)
                seen.add(key)

    set_apex_cutoffs(thresholds, region)

    highest = max(thresholds[::-1], key=lambda x: (x["maxValue"]))
    highest["maxValue"] = maxsize

    return thresholds


def value_to_rank(
    y, _, thresholds: list[dict], short=False, show_lp=False, minor_tick=False
) -> str:
    """
    Translates a value to a rank string. Set short=True to output a short string
    """

    def is_highest(tier: str) -> bool:
        return tier == max(thresholds, key=lambda x: x["maxValue"])["tier"]

    def roman_to_int(s: str) -> int:
        return {"IV": 4, "III": 3, "II": 2, "I": 1}[s]

    for tier in thresholds:
        if y >= tier["minValue"] and y < (
            tier["maxValue"]
            + (1 if is_highest(tier["tier"]) and util.is_apex(tier["tier"]) else 0)
        ):
            lp = (
                y - tier["minValue"]
                if not util.is_apex(tier["tier"])
                else y - MASTER_VALUE
            )
            if util.is_apex(tier["tier"]) and minor_tick:
                return f"{int(lp)} LP"
            lp_str = f" {int(lp)} LP" if show_lp else ""
            if short:
                return f"{util.short_tier(tier['tier'])}{roman_to_int(tier['division'])}{lp_str}"
            else:
                return f"{tier['tier']} {tier['division']}{lp_str}"
    return ""
