import logging

from traits.api import Instance
from traitsui.api import Item, ModelView, View

from app_common.traits.has_traits_utils import is_trait_property, trait_dict
from app_common.model_tools.data_element import DataElement

logger = logging.getLogger(__name__)


class DataElementModelView(ModelView):
    """ Generic model view for any DataElement.
    """
    model = Instance(DataElement)

    def traits_view(self):
        """ Build a view automatically which includes all attributes, including
        properties. Make properties read-only.
        """
        traits = trait_dict(self.model, include_properties=True)
        # Filter out the generic attributes of a DataElement to see the rest:
        trait_names = [attr for attr in traits.keys()
                       if attr not in {"name", "uuid", "editable"}]
        # and make the name be the first attribute:
        trait_names = ["name"] + trait_names
        is_prop = [is_trait_property(self.model, attr) for attr in trait_names]
        type_to_style = {True: "readonly", False: "simple"}
        styles = [type_to_style[attr_type] for attr_type in is_prop]
        items = [Item("model.{}".format(attr), style=style)
                 for attr, style in zip(trait_names, styles)]

        return View(
            *items
        )
