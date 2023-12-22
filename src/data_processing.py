from src.config import MASTER_VALUE
import src.util as util
from sys import maxsize


def merge_thresholds(dicts) -> list[dict]:
    def adjust_apex_thresholds(thresholds: list):
        master = next((item for item in thresholds if item["tier"] == "MASTER"), None)
        grandmaster = next(
            (item for item in thresholds if item["tier"] == "GRANDMASTER"), None
        )
        challenger = next(
            (item for item in thresholds if item["tier"] == "CHALLENGER"), None
        )

        if master and grandmaster:
            lp_cutoff = int((master["maxLP"] + grandmaster["minLP"]) / 2)
            value = MASTER_VALUE + lp_cutoff
            master["maxValue"] = value
            grandmaster["minValue"] = value

        if grandmaster and challenger:
            lp_cutoff = int((grandmaster["maxLP"] + challenger["minLP"]) / 2)
            value = MASTER_VALUE + lp_cutoff
            grandmaster["maxValue"] = value
            challenger["minValue"] = value
            challenger["maxValue"] = maxsize

    merged = []
    for lst in dicts:
        to_add = []
        for threshold in lst:
            predicate = (
                lambda x: x["tier"] == threshold["tier"]
                and x["division"] == threshold["division"]
            )
            matching = next((item for item in merged if predicate(item)), None)
            if matching is not None:
                if util.is_apex(threshold["tier"]):
                    # Dont merge apex thresholds, only keep the latest one
                    continue
                matching["minValue"] = min(matching["minValue"], threshold["minValue"])
                matching["maxValue"] = max(matching["maxValue"], threshold["maxValue"])
            else:
                to_add.append(threshold)
        merged.extend(to_add)
    adjust_apex_thresholds(merged)

    highest = max(merged[::-1], key=lambda x: (x["maxValue"]))
    highest["maxValue"] = maxsize

    return merged


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
