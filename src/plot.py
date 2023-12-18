import src.mobalytics_query as api
import src.cursor as cursor
import matplotlib.pyplot as plt
import datetime, pytz
from matplotlib.ticker import FuncFormatter

LOCAL_TIMEZONE = pytz.timezone("Europe/Stockholm")


def value_to_rank(y, _, thresholds: dict, short=False) -> str:
    """
    Translates a value to a rank string. Set short=True to output a short string
    """

    def roman_to_int(s: str) -> int:
        return {"IV": 4, "III": 3, "II": 2, "I": 1}[s]

    for tier in thresholds:
        if y >= tier["minValue"] and y < tier["maxValue"]:
            lp = y - tier["minValue"] + tier["minLP"]
            lp_str = f" {int(lp)} LP" if short else ""
            if short:
                return f"{tier['tier'][0]}{roman_to_int(tier['division'])}{lp_str}"
            else:
                return f"{tier['tier']} {tier['division']}{lp_str}"
    return ""


def plot(summoner_name: str):
    data = api.get(summoner_name)

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

    print(x_values)
    print(y_values)

    fig, ax = plt.subplots()
    (line,) = ax.plot(x_values, y_values)

    offset = 50  # offset amount of lp
    ax.set_ylim(min(y_values) - offset, max(y_values) + offset)
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda y, pos: value_to_rank(y, pos, data["thresholds"]))  # type: ignore
    )
    ax.invert_xaxis()

    crosshair = cursor.Cursor(
        ax,
        line,
        x_dates,
        lambda y: value_to_rank(
            y, None, data["thresholds"], short=True  # type: ignore
        ),
    )
    fig.canvas.mpl_connect("motion_notify_event", crosshair.on_mouse_move)

    plt.title(f"Rank history - [{summoner_name}]")
    plt.xlabel("Games ago")
    plt.ylabel("Rank")
    plt.show()
