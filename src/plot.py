import src.mobalytics_query as api
import src.cursor as cursor
import matplotlib.pyplot as plt
import datetime, pytz
from matplotlib.ticker import FuncFormatter

LOCAL_TIMEZONE = pytz.timezone("Europe/Stockholm")


def get_major_ticks(y_values: list, thresholds: dict) -> list:
    MASTER_VALUE = 2800
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
        "DIAMOND": "#716bf6",  # TODO: find a better color?
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


def value_to_rank(
    y, _, thresholds: dict, short=False, show_lp=False, minor_tick=False
) -> str:
    """
    Translates a value to a rank string. Set short=True to output a short string
    """

    def is_apex(tier: str) -> bool:
        return tier in ["MASTER", "GRANDMASTER", "CHALLENGER"]

    def is_highest(tier: str) -> bool:
        return tier == max(thresholds, key=lambda x: x["maxValue"])["tier"]

    def roman_to_int(s: str) -> int:
        return {"IV": 4, "III": 3, "II": 2, "I": 1}[s]

    def short_tier(tier: str) -> str:
        return tier[0] if tier != "GRANDMASTER" else "GM"

    for tier in thresholds:
        if y >= tier["minValue"] and y < (
            tier["maxValue"] + (1 if is_highest(tier["tier"]) else 0)
        ):
            lp = y - tier["minValue"] + tier["minLP"]
            if is_apex(tier["tier"]) and minor_tick:
                return f"{int(lp)} LP"
            lp_str = f" {int(lp)} LP" if show_lp else ""
            if short:
                return f"{short_tier(tier['tier'])}{roman_to_int(tier['division'])}{lp_str}"
            else:
                return f"{tier['tier']} {tier['division']}{lp_str}"
    return ""


def plot(summoner_name: str):
    data = api.get(summoner_name)
    print(f"Plotting {summoner_name}...")

    y_values = []
    for item in data["items"][::-1]:  # type: ignore
        # If the value is not None, use it
        if item["lp"]["after"] is not None:
            y_values.append(item["lp"]["after"]["value"])
        # If the value is None, use the previous value (if there is a previous value)
        elif y_values:
            y_values.append(y_values[-1])

    x_values = list(range(len(y_values) - 1, -1, -1))  # invert x axis
    x_dates = [
        datetime.datetime.fromtimestamp(item["startedAt"], LOCAL_TIMEZONE)
        for item in data["items"][::-1]  # type: ignore
    ]

    fig, ax = plt.subplots()
    (line,) = ax.plot(x_values, y_values, color="black")
    fig.patch.set_facecolor("#343541")

    Y_AXIS_PADDING = 10
    y_axis_min = min(y_values) - Y_AXIS_PADDING
    y_axis_max = max(y_values) + Y_AXIS_PADDING

    ax.set_ylim(y_axis_min, y_axis_max)
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda y, pos: value_to_rank(y, pos, data["thresholds"]))  # type: ignore
    )
    ax.yaxis.set_minor_formatter(
        FuncFormatter(
            lambda y, pos: value_to_rank(y, pos, data["thresholds"], minor_tick=True),  # type: ignore
        )
    )
    ax.invert_xaxis()

    TICK_LP_INTERVAL = 200
    major_ticks = get_major_ticks(y_values, data["thresholds"])  # type: ignore
    minor_ticks = [
        value
        for value in range(min(y_values), max(y_values))
        if value % TICK_LP_INTERVAL == 0
    ]

    ax.yaxis.set_ticks(minor_ticks, minor=True)  # Set minor ticks
    ax.yaxis.set_ticks(major_ticks)  # type: ignore
    ax.tick_params(which="both", color="white", labelcolor="white", length=0, width=0)

    plt.grid(which="major", linestyle="-", linewidth="0.35", color="black", axis="y")
    plt.grid(which="minor", linestyle="-", linewidth="0.35", color="black")

    crosshair = cursor.Cursor(
        ax,
        line,
        x_dates,
        lambda y: value_to_rank(
            y, None, data["thresholds"], short=True, show_lp=True  # type: ignore
        ),
    )
    fig.canvas.mpl_connect("motion_notify_event", crosshair.on_mouse_move)

    color_rank_intervals(data["thresholds"], y_axis_min, y_axis_max)  # type: ignore
    plt.title(f"Rank history - [{summoner_name}]", color="white")
    plt.xlabel("Games ago", color="white")
    plt.ylabel("Rank", color="white")
    plt.show()
