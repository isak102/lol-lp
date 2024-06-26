import datetime
import logging
from collections import deque

import matplotlib.pyplot as plt
import numpy as np
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
            lower_bound, upper_bound, facecolor=config.RANK_COLORS[tier], alpha=0.8
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
                "result": item["result"],
                "lp_diff": item["lp"]["lpDiff"],
            }
            points.append(point)

    return points


def insert_roll_avg_lpdiff(points: list[dict]) -> None:
    win_lp_diffs = deque(maxlen=config.LPDIFF_WINDOW)
    loss_lp_diffs = deque(maxlen=config.LPDIFF_WINDOW)

    logger.info("Calculating rolling average LP diff...")
    for point in points:
        if point["lp_diff"] is not None:
            lp_diff = abs(point["lp_diff"])
            if lp_diff > 10 and lp_diff < 100:
                if point["result"] == "WON":
                    win_lp_diffs.append(lp_diff)
                elif point["result"] == "LOST":
                    loss_lp_diffs.append(lp_diff)

        # Calculate rolling average for wins if we have enough data points
        if (
            len(win_lp_diffs) == config.LPDIFF_WINDOW
            and len(loss_lp_diffs) == config.LPDIFF_WINDOW
        ):
            avg_win = sum(win_lp_diffs) / config.LPDIFF_WINDOW
            avg_loss = sum(loss_lp_diffs) / config.LPDIFF_WINDOW
            point["roll_avg_lpdiff"] = avg_win - avg_loss
        else:
            point["roll_avg_lpdiff"] = None


def insert_roll_avg_wr(points: list[dict]) -> None:
    winrates = deque(maxlen=config.WR_WINDOW)

    logger.info("Calculating rolling average winrate...")
    for point in points:
        if point["result"] is not None:
            if point["result"] == "WON":
                winrates.append(1)
            elif point["result"] == "LOST":
                winrates.append(0)

        # Calculate rolling average for wins if we have enough data points
        if len(winrates) == config.WR_WINDOW:
            avg_winrate = sum(winrates) / config.WR_WINDOW
            point["roll_avg_wr"] = avg_winrate
        else:
            point["roll_avg_wr"] = None


def on_key(event, r_avg_lpdiff, r_avg_wr):
    if event.key == "l":  # Replace 't' with the key you want to use
        line_visibility = r_avg_lpdiff.get_lines()[0].get_visible()
        axis_visibility = r_avg_lpdiff.axes.get_visible()
        r_avg_lpdiff.get_lines()[0].set_visible(not line_visibility)
        r_avg_lpdiff.axes.set_visible(not axis_visibility)
        plt.draw()
    elif event.key == "w":
        axis_visibility = r_avg_wr.axes.get_visible()
        line_visibility = r_avg_wr.get_lines()[0].get_visible()
        r_avg_wr.get_lines()[0].set_visible(not line_visibility)
        r_avg_wr.axes.set_visible(not axis_visibility)
        plt.draw()


def plot(
    summoner_name: str, region: str, pages: list[dict], thresholds: list[dict]
) -> str:
    """
    Plots the data. Returns a message to display after plotting.
    """
    logger.info("Extracting points...")
    points = extract_points(pages)
    logger.info(f"Found {len(points)} points")

    if len(points) == 0:
        msg = "No games found."
        logger.info(msg)
        return msg

    logger.info("Filling in x values...")
    for i, point in enumerate(reversed(points)):
        point["x"] = i

    x_values = [point["x"] for point in points]
    y_values = [point["y"] for point in points]

    plt.rcParams["keymap.yscale"].remove("l")

    fig, ax = plt.subplots(constrained_layout=True)
    (line,) = ax.plot(x_values, y_values, color="#E8E8E8", linewidth=0.7)
    ax.set_facecolor("#343541")
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

    # Calculate the rolling averages
    insert_roll_avg_lpdiff(points)
    insert_roll_avg_wr(points)

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

    r_avg_lpdiff = [point["roll_avg_lpdiff"] for point in points]
    r_avg_wr = [point["roll_avg_wr"] for point in points if point["roll_avg_wr"]]

    # Create secondary y-axis for the rolling average difference
    ax2 = ax.twinx()
    ax2.plot(x_values, r_avg_lpdiff, "black", linewidth=0.5, visible=False)
    ax2.set_ylabel(
        f"Rolling Average LP Difference [window={config.LPDIFF_WINDOW}]", color="white"
    )
    ax2.tick_params(axis="y", labelcolor="white")
    ax2.axhline(y=0, color="black", linewidth=2)
    ax2.set_visible(False)

    OFFSET = 2  # Offset for the y-axis limits
    filtered_diff = [val for val in r_avg_lpdiff if val is not None]
    max_diff = max(abs(min(filtered_diff)), max(filtered_diff)) if filtered_diff else 0
    ax2.set_ylim(-max_diff - OFFSET, max_diff + OFFSET)

    window_size = 3  # Adjust this as needed
    smoothed_r_avg_wr = (
        np.convolve(r_avg_wr, np.ones(window_size) / window_size, mode="valid")
        if len(r_avg_wr) > 0
        else r_avg_wr
    )
    adjusted_x_values = x_values[len(x_values) - len(smoothed_r_avg_wr) :]

    ax3 = ax.twinx()
    ax3.spines["right"].set_position(("outward", 60))  # Offset the right spine of ax3
    ax3.spines["right"].set_color("white")
    ax3.tick_params(axis="y", labelcolor="white")
    ax3.plot(
        adjusted_x_values, smoothed_r_avg_wr, "black", linewidth=0.5, visible=False
    )
    ax3.set_ylabel(
        f"Rolling average winrate [window={config.WR_WINDOW}]", color="white"
    )
    ax3.set_ylim(0, 1)
    ax3.axhline(y=0.5, color="black", linewidth=2)
    ax3.set_visible(False)

    fig.canvas.mpl_connect("key_press_event", lambda event: on_key(event, ax2, ax3))

    # Set the title and x-axis label
    ax.set_xlabel("Games Ago", color="white")
    ax.set_ylabel("Rank", color="white")
    ax.set_title(title, color="white")

    plt.show()

    return ""
