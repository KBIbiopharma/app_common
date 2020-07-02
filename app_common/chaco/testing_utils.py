from chaco.api import OverlayPlotContainer
from traits.api import HasTraits, Instance
from traitsui.api import HGroup, UItem, View
from enable.api import ComponentEditor


def embed_renderer_in_traits(rend):
    """Embed a renderer into a viewable traits UI.
    """
    class Test(HasTraits):
        plot = Instance(OverlayPlotContainer)

        view = View(
            HGroup(
                UItem("plot", editor=ComponentEditor(), style="custom"),
            )
        )

        def _plot_default(self):
            container = OverlayPlotContainer(padding=20)
            container.add(rend)
            return container

    return Test()
