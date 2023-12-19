import src.mobalytics_query as api
import src.cursor as cursor
import matplotlib.pyplot as plt
import datetime, pytz
import asyncio
from sys import maxsize
from matplotlib.ticker import FuncFormatter

LOCAL_TIMEZONE = pytz.timezone("Europe/Stockholm")
MASTER_VALUE = 2800  # the value of 0LP master


def get_major_ticks(y_values: list, thresholds: dict) -> list:
    ticks = [  # get all ticks up to master
        f
        for f in range(min(y_values), min(max(y_values), MASTER_VALUE) + 1)
        if f % 400 == 0
    ]

    TIERS = ["GRANDMASTER", "CHALLENGER"]
    for tier in TIERS:  # get ticks for grandmaster and challenger
        tick = next(
            (item["minValue"] for item in thresholds if item["tier"] == tier), None
        )
        if tick is not None:
            ticks.append(tick)

    return ticks


def color_rank_intervals(thresholds: dict, min_y, max_y):
    """
    Colors the graph with each rank's color
    """

    def is_highest(tier: str) -> bool:
        return tier == max(thresholds, key=lambda x: x["maxValue"])["tier"]

    def is_lowest(tier: str) -> bool:
        return tier == min(thresholds, key=lambda x: x["minValue"])["tier"]

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

    unique_tiers = {item["tier"] for item in thresholds}
    for tier in unique_tiers:
        upper_bound = max(
            item["maxValue"] for item in thresholds if item["tier"] == tier
        )
        lower_bound = min(
            item["minValue"] for item in thresholds if item["tier"] == tier
        )

        if is_highest(tier):
            upper_bound = max(max_y, upper_bound)
        if is_lowest(tier):
            lower_bound = min(min_y, lower_bound)

        plt.axhspan(lower_bound, upper_bound, facecolor=RANK_COLORS[tier], alpha=0.6)


def is_apex(tier: str) -> bool:
    return tier in ["MASTER", "GRANDMASTER", "CHALLENGER"]


def value_to_rank(
    y, _, thresholds: dict, short=False, show_lp=False, minor_tick=False
) -> str:
    """
    Translates a value to a rank string. Set short=True to output a short string
    """

    def is_highest(tier: str) -> bool:
        return tier == max(thresholds, key=lambda x: x["maxValue"])["tier"]

    def roman_to_int(s: str) -> int:
        return {"IV": 4, "III": 3, "II": 2, "I": 1}[s]

    def short_tier(tier: str) -> str:
        return tier[0] if tier != "GRANDMASTER" else "GM"

    for tier in thresholds:
        if y >= tier["minValue"] and y < (
            tier["maxValue"]
            + (1 if is_highest(tier["tier"]) and is_apex(tier["tier"]) else 0)
        ):
            lp = y - tier["minValue"] if not is_apex(tier["tier"]) else y - MASTER_VALUE
            if is_apex(tier["tier"]) and minor_tick:
                return f"{int(lp)} LP"
            lp_str = f" {int(lp)} LP" if show_lp else ""
            if tier["tier"] == "MASTER" and lp == 100:
                print(y, tier["minValue"], tier["maxValue"])
            if short:
                return f"{short_tier(tier['tier'])}{roman_to_int(tier['division'])}{lp_str}"
            else:
                return f"{tier['tier']} {tier['division']}{lp_str}"
    return ""


def merge_thresholds(dicts) -> list:
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
                if is_apex(threshold["tier"]):
                    # Dont merge apex thresholds, only keep the latest one
                    continue
                matching["minValue"] = min(matching["minValue"], threshold["minValue"])
                matching["maxValue"] = max(matching["maxValue"], threshold["maxValue"])
            else:
                to_add.append(threshold)
        merged.extend(to_add)
    adjust_apex_thresholds(merged)

    highest = max(merged, key=lambda x: x["maxValue"])
    highest["maxValue"] = maxsize

    return merged


def insert_patch_lines(points: list, ax, min_distance=4) -> list:
    """
    Finds the indices of the points where a new patch is introduced and inserts
    a vertical line at that point with a text label, only if they are not too close together.

    Labels are only added to the leftmost line if lines are closer than min_distance to each other.

    :param points: List of point dictionaries with a 'patch' key.
    :param ax: The axis object of the plot.
    :param min_distance: The minimum distance allowed between text labels.
    :return: List of tuples with the index and patch value where lines are inserted.
    """
    patch_lines = [
        (len(points) - (i + 1), points[i]["patch"])
        for i in range(1, len(points))
        if points[i]["patch"] != points[i - 1]["patch"]
    ]

    for i, (x_pos, patch) in enumerate(patch_lines):
        plt.axvline(
            x_pos,
            color="black",
            linestyle=":",
            linewidth=0.3,
        )

        # Check if this is the last patch line or if the next patch line is further away than min_distance
        if (i == len(patch_lines) - 1) or (
            (x_pos) - (patch_lines[i + 1][0] + 1) >= min_distance
        ):
            # Add text at the vertical line
            plt.text(
                x_pos - 0.05,  # Slight offset in x-direction for clarity
                ax.get_ylim()[1],  # Set y position at the top of the plot
                patch,  # The text label
                rotation=90,  # Vertical text
                verticalalignment="top",  # Align text to the top of plot
                fontsize=8,
            )

    return patch_lines


def extract_points(pages: list) -> list[dict]:
    def get_y(item):
        if item["lp"]["after"] is not None:
            value = item["lp"]["after"]["value"]
            lp = item["lp"]["after"]["lp"]
        elif item["lp"]["before"] is not None:
            value = item["lp"]["before"]["value"]
            lp = item["lp"]["before"]["lp"]
        else:
            # If there was no lp before and after then the game was a placement game
            return None

        if value > MASTER_VALUE:
            y = MASTER_VALUE + lp
        elif (
            value == MASTER_VALUE and lp == 100
        ):  # FIXME:  This is a hack to avoid D1 promos appearing as master 0LP
            y = MASTER_VALUE - 1
        else:
            y = value

        return y

    points = []
    for page in reversed(pages):
        for item in reversed(page["items"]):  # type: ignore
            y_value = get_y(item)
            if y_value is None:
                continue

            point = {
                "y": y_value,
                "date": datetime.datetime.fromtimestamp(
                    item["startedAt"], LOCAL_TIMEZONE
                ),
                "patch": item["patch"],
            }
            points.append(point)

    return points


def plot(summoner_name: str):
    pages = asyncio.run(api.get_lphistory(summoner_name))

    # Get all points from all pages
    print("Extracting points...")
    points = extract_points(pages)

    # Fill in the x values, starting from the end and going down to 0
    print("Filling in x values...")
    for i, point in enumerate(reversed(points)):
        point["x"] = i

    print("Merging thresholds...")
    thresholds = merge_thresholds([page["thresholds"] for page in pages])

    x_values = [point["x"] for point in points]
    y_values = [point["y"] for point in points]

    fig, ax = plt.subplots()
    (line,) = ax.plot(x_values, y_values, color="black")
    fig.patch.set_facecolor("#343541")

    Y_AXIS_PADDING = 10
    y_axis_min = min(y_values) - Y_AXIS_PADDING
    y_axis_max = max(y_values) + Y_AXIS_PADDING

    ax.set_ylim(y_axis_min, y_axis_max)
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda y, pos: value_to_rank(y, pos, thresholds))  # type: ignore
    )
    ax.yaxis.set_minor_formatter(
        FuncFormatter(
            lambda y, pos: value_to_rank(y, pos, thresholds, minor_tick=True),  # type: ignore
        )
    )
    ax.invert_xaxis()

    TICK_LP_INTERVAL = 200
    print("Setting ticks...")
    major_ticks = get_major_ticks(y_values, thresholds)  # type: ignore
    minor_ticks = [
        value
        for value in range(min(y_values), max(y_values))
        if value % TICK_LP_INTERVAL == 0
    ]

    ax.yaxis.set_ticks(minor_ticks, minor=True)  # Set minor ticks
    ax.yaxis.set_ticks(major_ticks)  # type: ignore
    ax.tick_params(which="both", color="white", labelcolor="white", length=0, width=0)

    print("Inserting patch lines...")
    insert_patch_lines(points, ax)

    plt.grid(which="major", linestyle="-", linewidth="0.35", color="black", axis="y")
    plt.grid(which="minor", linestyle="-", linewidth="0.35", color="black")

    crosshair = cursor.Cursor(
        ax,
        line,
        points,
        lambda y: value_to_rank(
            y, None, thresholds, short=True, show_lp=True  # type: ignore
        ),
    )
    fig.canvas.mpl_connect("motion_notify_event", crosshair.on_mouse_move)

    print("Coloring rank intervals...")
    color_rank_intervals(thresholds, y_axis_min, y_axis_max)  # type: ignore

    plt.title(f"Rank history - [{summoner_name}]", color="white")
    plt.xlabel("Games ago", color="white")
    plt.ylabel("Rank", color="white")
    plt.show()
