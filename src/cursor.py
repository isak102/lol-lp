import numpy as np


class Cursor:
    """
    A cross-hair cursor that snaps to the data point of a line, which is
    closest to the *x* position of the cursor, using blitting for faster redraw.
    Credit to ChatGPT.
    """

    def __init__(self, ax, line, points, y_converter):
        self.ax = ax
        self.line = line
        self.x, self.y = line.get_data()
        self.points = points
        self.y_converter = y_converter
        self._last_index = None
        self.background = None
        self.horizontal_line = ax.axhline(color="white", linestyle=":")
        self.vertical_line = ax.axvline(color="white", linestyle=":")
        props = dict(boxstyle="round", facecolor="black", alpha=0.5)
        self.text = ax.text(
            0.0125,
            0.975,
            "",
            color="white",
            transform=ax.transAxes,
            bbox=props,
            fontsize=12,
            verticalalignment="top",
            horizontalalignment="left",
        )
        self._creating_background = False
        ax.figure.canvas.mpl_connect("draw_event", self.on_draw)

    def on_draw(self, event):
        self.create_new_background()

    def set_cross_hair_visible(self, visible):
        need_redraw = self.horizontal_line.get_visible() != visible
        self.horizontal_line.set_visible(visible)
        self.vertical_line.set_visible(visible)
        self.text.set_visible(visible)
        return need_redraw

    def create_new_background(self):
        if self._creating_background:
            return
        self._creating_background = True
        self.set_cross_hair_visible(False)
        self.ax.figure.canvas.draw()
        self.background = self.ax.figure.canvas.copy_from_bbox(self.ax.bbox)
        self.set_cross_hair_visible(True)
        self._creating_background = False

    def get_date_str(self, index):
        date = self.points[index]["date"]
        return date.strftime("%a %b %d")

    def set_info_text(self, index):
        date_str = self.get_date_str(index)
        patch = self.points[index]["patch"]
        r_avg_lp_diff = self.points[index]["roll_avg_lpdiff"]
        r_avg_wr = self.points[index]["roll_avg_wr"]

        if r_avg_lp_diff is not None:
            avg_lp_diff_str = "{:.1f}".format(r_avg_lp_diff)
        else:
            avg_lp_diff_str = "N/A"

        if r_avg_wr is not None:
            avg_wr_str = "{:.1f}%".format(r_avg_wr * 100)
        else:
            avg_wr_str = "N/A"

        text = "({}): [{}]\nPatch: {}. ({} games ago)\nRolling avg WR: {}\nRolling avg LP +/-: {}".format(
            date_str,
            self.y_converter(self.y[index]),
            patch,
            len(self.points) - index - 1,
            avg_wr_str,
            avg_lp_diff_str,
        )

        self.text.set_text(text)

    def on_mouse_move(self, event):
        if self.background is None:
            self.create_new_background()
        if not event.inaxes:
            self._last_index = None
            need_redraw = self.set_cross_hair_visible(False)
            if need_redraw:
                self.ax.figure.canvas.restore_region(self.background)
                self.ax.figure.canvas.blit(self.ax.bbox)
        else:
            x, y = event.xdata, event.ydata
            # Since the x-axis is inverted, we need to invert the search.
            # Find the closest index to the inverted x position.
            inverted_index = (
                len(self.x) - np.searchsorted(self.x[::-1], x, side="left") - 1
            )
            index = np.clip(inverted_index, 0, len(self.x) - 1)
            if index != self._last_index:
                self._last_index = index
                x = self.x[index]
                y = self.y[index]
                self.horizontal_line.set_ydata([y])
                self.vertical_line.set_xdata([x])
                # Use the correct date string for the inverted index.
                self.set_info_text(index)
                self.set_cross_hair_visible(True)
                self.ax.figure.canvas.restore_region(self.background)
                self.ax.draw_artist(self.horizontal_line)
                self.ax.draw_artist(self.vertical_line)
                self.ax.draw_artist(self.text)
                self.ax.figure.canvas.blit(self.ax.bbox)
