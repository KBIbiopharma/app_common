from traits.api import Bool, Callable, Dict, Float, HasStrictTraits, Str
from traitsui.api import Item, OKCancelButtons, View

from app_common.std_lib.str_utils import sanitize_string
from app_common.traitsui.common_traitsui_groups import make_window_title_group


class DictValueEditor(HasStrictTraits):
    """ Embeddable class to edit a dictionary's values.

    Usage
    -----
    - Listen to changes to the target_dict's values to be notified of changes.
    - Control the trait to use to store (and display) dict values by overriding
    the value_to_trait callable (by default, values are stored in a Float
    trait.)
    - Override item_kwargs to set additional arguments on the view's Item,
    returning Item attributes such as `label`, `readonly`, `editor`, ... By
    default, only the label is set to the dictionary key.
    """
    target_dict = Dict

    _trait_map = Dict

    _key_map = Dict

    view_klass = Callable

    key_to_trait = Callable

    value_to_trait = Callable(Float)

    item_kwargs = Callable(lambda key: {"label": key})

    title = Str

    show_title_in_view = Bool

    def __init__(self, *args, **traits):
        if args:
            if len(args) != 1:
                msg = "A DictValueEditor should be created with 1 " \
                      "positional argument at the most, providing the " \
                      "target_dict."
                raise ValueError(msg)
            else:
                traits["target_dict"] = args[0]

        super(DictValueEditor, self).__init__(**traits)
        if not self.target_dict:
            msg = "A target dict to edit is needed to be able to edit it."
            raise ValueError(msg)

        for key, value in self.target_dict.items():
            trait_name = self.key_to_trait(key)
            self.add_trait(trait_name, self.value_to_trait(value))
            self._key_map[key] = trait_name
            self._trait_map[trait_name] = key
            self.observe(self.update_target_dict, trait_name)

    def traits_view(self):
        item_list = []
        if self.title and self.show_title_in_view:
            item_list.append(make_window_title_group(self.title))

        item_list += [Item(trait_name, **self.item_kwargs(key))
                      for trait_name, key in self._trait_map.items()]
        view = self.view_klass(
            *item_list,
            buttons=OKCancelButtons,
            title=self.title
        )
        return view

    def update_target_dict(self, event):
        """ A trait was changed: update the dictionary.
        """
        self.target_dict[self._trait_map[event.name]] = event.new

    def set_values(self, **kwargs):
        """ Set dictionary values and update the corresponding traits.
        """
        trait_changes = {self._key_map[key]: value
                         for key, value in kwargs.items()}
        self.trait_set(**trait_changes)

    def _key_to_trait_default(self):
        return sanitize_string

    def _view_klass_default(self):
        return View


if __name__ == "__main__":
    from traits.api import Range

    value_to_trait = lambda value: Range(low=0, high=1, value=value)
    editor = DictValueEditor(target_dict={"a": 1, "b c": 0.5},
                             value_to_trait=value_to_trait,
                             title="Dict editor", show_title_in_view=True)
    editor.configure_traits()
