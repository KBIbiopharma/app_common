""" Changes to the Chaco legend highlighter while we wait to push them
upstream.
"""
from chaco.api import Legend as BaseLegend
from chaco.tools.api import LegendHighlighter as BaseLegendHighlighter


class Legend(BaseLegend):
    def get_label_at(self, x, y):
        """ Returns the label object at (x,y).
        """
        for i, pos in enumerate(self._cached_label_positions):
            size = self._cached_label_sizes[i]
            corner = pos + size
            # No more testing of the x dimension since not needed: we can click
            # anywhere along the line of a label:
            if pos[1] <= y <= corner[1]:
                return self._cached_labels[i]
        else:
            return None


def get_hit_plots(legend, event):
    if legend is None or not legend.is_in(event.x, event.y):
        return []

    # Removed a bunch of useless try/except code and remove the +20 hack since
    # that doesn't always work.
    label = legend.get_label_at(legend.x, event.y)
    if label is None:
        return []
    try:
        ndx = legend._cached_labels.index(label)
        label_name = legend._cached_label_names[ndx]
        renderers = legend.plots[label_name]
        return renderers if isinstance(renderers, list) else [renderers]
    except (ValueError, KeyError):
        return []


class LegendHighlighter(BaseLegendHighlighter):
    """ A tool for legends that allows clicking on the legend to show
    or hide certain plots.
    """
    def normal_left_down(self, event):
        if not self.component.is_in(event.x, event.y):
            return

        plots = get_hit_plots(self.component, event)

        if len(plots) > 0:
            plot = plots[0]

            if event.shift_down:
                # User in multi-select mode by using [shift] key.
                if plot in self._selected_renderers:
                    self._selected_renderers.remove(plot)
                else:
                    self._selected_renderers.append(plot)

            else:
                # User in single-select mode.
                add_plot = plot not in self._selected_renderers
                self._selected_renderers = []
                if add_plot:
                    self._selected_renderers.append(plot)

            if self._selected_renderers:
                self._set_states(self.component.plots)
            else:
                self._reset_selects(self.component.plots)
            plot.request_redraw()

        event.handled = True
