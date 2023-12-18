import src.mobalytics_query as api
import src.cursor as cursor
import matplotlib.pyplot as plt
import datetime, pytz

LOCAL_TIMEZONE = pytz.timezone("Europe/Stockholm")


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

    x_values = list(range(len(y_values)))
    x_dates = [datetime.datetime.fromtimestamp(item["startedAt"], LOCAL_TIMEZONE) for item in data["items"][::-1]]  # type: ignore

    print(x_values)
    print(y_values)

    fig, ax = plt.subplots()
    (line,) = ax.plot(x_values, y_values)

    ax.set_ylim(min(y_values) - 100, max(y_values) + 100)

    crosshair = cursor.Cursor(ax, line, x_dates)
    fig.canvas.mpl_connect("motion_notify_event", crosshair.on_mouse_move)
    plt.show()
