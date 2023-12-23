import datetime
import logging

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

import src.config as config
import src.cursor as cursor
import src.data_processing as data

logger = logging.getLogger(__name__)


def get_major_ticks(y_values: list, thresholds: list[dict]) -> list:
    ticks = [  # get all ticks up to master
        f
        for f in range(min(y_values), min(max(y_values), config.MASTER_VALUE) + 1)
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


def color_rank_intervals(thresholds: list[dict], min_y, max_y):
    """
    Colors the graph with each rank's color
    """

    def is_highest(tier: str) -> bool:
        return tier == max(thresholds, key=lambda x: x["maxValue"])["tier"]

    def is_lowest(tier: str) -> bool:
        return tier == min(thresholds, key=lambda x: x["minValue"])["tier"]

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

        plt.axhspan(
            lower_bound, upper_bound, facecolor=config.RANK_COLORS[tier], alpha=0.6
        )


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

        if value > config.MASTER_VALUE:
            y = config.MASTER_VALUE + lp
        elif value == config.MASTER_VALUE:
            if lp == 100:
                # FIXME: This is a hack to avoid D1 promos appearing as master 0LP. maybe introduces bugs?
                y = config.MASTER_VALUE - 1
            else:
                y = config.MASTER_VALUE + lp
        else:
            y = value

        return y

    points = []
    for page in reversed(pages):
        for item in reversed(page["items"]):
            y_value = get_y(item)
            if y_value is None:
                continue

            point = {
                "y": y_value,
                "date": datetime.datetime.fromtimestamp(
                    item["startedAt"], config.LOCAL_TIMEZONE
                ),
                "patch": item["patch"],
            }
            points.append(point)

    return points


def plot(summoner_name: str, region: str, pages: list[dict], thresholds: list[dict]):
    logger.info("Extracting points...")
    points = extract_points(pages)
    logger.info(f"Found {len(points)} points")

    logger.info("Filling in x values...")
    for i, point in enumerate(reversed(points)):
        point["x"] = i

    x_values = [point["x"] for point in points]
    y_values = [point["y"] for point in points]

    plt.rcParams['toolbar'] = "None"

    fig, ax = plt.subplots()
    (line,) = ax.plot(x_values, y_values, color="black", linewidth=0.7)
    fig.patch.set_facecolor("#343541")

    manager = plt.get_current_fig_manager()
    if manager is not None:
        # TODO: handle other backends
        from PyQt5 import QtGui

        logger.info(f"Manager {manager} found, setting window title and icon...")
        manager.set_window_title(f"LP History - {summoner_name} ({region})")
        manager.window.setWindowIcon(QtGui.QIcon(config.ICON_PATH))  # type: ignore

    Y_AXIS_PADDING = 10
    y_axis_min = min(y_values) - Y_AXIS_PADDING
    y_axis_max = max(y_values) + Y_AXIS_PADDING

    ax.set_ylim(y_axis_min, y_axis_max)
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda y, pos: data.value_to_rank(y, pos, thresholds))
    )
    ax.yaxis.set_minor_formatter(
        FuncFormatter(
            lambda y, pos: data.value_to_rank(y, pos, thresholds, minor_tick=True),
        )
    )
    ax.invert_xaxis()

    TICK_LP_INTERVAL = 200
    logger.info("Setting ticks...")
    major_ticks = get_major_ticks(y_values, thresholds)
    minor_ticks = [
        value
        for value in range(min(y_values), max(y_values))
        if value % TICK_LP_INTERVAL == 0
    ]

    ax.yaxis.set_ticks(minor_ticks, minor=True)  # Set minor ticks
    ax.yaxis.set_ticks(major_ticks)
    ax.tick_params(which="both", color="white", labelcolor="white", length=0, width=0)

    logger.info("Inserting patch lines...")
    insert_patch_lines(points, ax)

    plt.grid(which="major", linestyle="-", linewidth="0.35", color="black", axis="y")
    plt.grid(which="minor", linestyle="-", linewidth="0.35", color="black")

    crosshair = cursor.Cursor(
        ax,
        line,
        points,
        lambda y: data.value_to_rank(y, None, thresholds, short=True, show_lp=True),
    )
    fig.canvas.mpl_connect("motion_notify_event", crosshair.on_mouse_move)

    logger.info("Coloring rank intervals...")
    color_rank_intervals(thresholds, y_axis_min, y_axis_max)

    peak = max(points, key=lambda x: x["y"])

    title = "LP History - [{}] - [{}]\nPeak: {} at {} patch {} ({} games ago)".format(
        summoner_name,
        region,
        data.value_to_rank(peak["y"], None, thresholds, short=True, show_lp=True),
        peak["date"].strftime("%b %d"),
        peak["patch"],
        peak["x"],
    )

    plt.title(title, color="white")
    plt.xlabel("Games ago", color="white")
    plt.ylabel("Rank", color="white")
    plt.show()
