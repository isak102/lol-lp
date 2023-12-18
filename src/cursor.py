import matplotlib.pyplot as plt
import numpy as np


class Cursor:
    """
    A cross-hair cursor that snaps to the data point of a line, which is
    closest to the *x* position of the cursor, using blitting for faster redraw.
    Credit to ChatGPT.
    """

    def __init__(self, ax, line, dates, y_converter):
        self.ax = ax
        self.line = line
        self.x, self.y = line.get_data()
        self.dates = dates
        self.y_converter = y_converter
        self._last_index = None
        self.background = None
        self.horizontal_line = ax.axhline(color="k", lw=0.8, ls="--")
        self.vertical_line = ax.axvline(color="k", lw=0.8, ls="--")
        self.text = ax.text(0.1, 0.9, "", transform=ax.transAxes)
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
        date = self.dates[index]
        # tranform date to local timezone like nov 13
        return date.strftime("%b %d")

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
            index = min(np.searchsorted(self.x, x), len(self.x) - 1)
            if index != self._last_index:
                self._last_index = index
                x = self.x[index]
                y = self.y[index]
                self.horizontal_line.set_ydata([y])
                self.vertical_line.set_xdata([x])
                self.text.set_text(f"{self.get_date_str(x)}: [{self.y_converter(y)}]")
                self.set_cross_hair_visible(True)
                self.ax.figure.canvas.restore_region(self.background)
                self.ax.draw_artist(self.horizontal_line)
                self.ax.draw_artist(self.vertical_line)
                self.ax.draw_artist(self.text)
                self.ax.figure.canvas.blit(self.ax.bbox)
