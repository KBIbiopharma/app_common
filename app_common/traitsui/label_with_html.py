""" Fancier Label editor that supports wrapping text around and html code
"""
from traits.api import Bool
from traitsui.api import ColorTrait
from traitsui.api import Label as BaseLabel, TextEditor as TextEditorFactory
from traitsui.qt4.text_editor import ReadonlyEditor as BaseTextEditorReadOnly


class Label(BaseLabel):
    """ Expanded Label with traits based styling
    """
    color = ColorTrait("black")

    bold = Bool

    italic = Bool

    def __init__(self, label, **traits):
        label = '<p style="color:{color}">{label}</p>'.format(
            color=traits["color"], label=label
        )
        if "bold" in traits:
            traits.pop("bold")
            if traits["bold"]:
                label = "<b>{label}</b>".format(label=label)

        if "italic" in traits:
            traits.pop("italic")
            if traits["italic"]:
                label = "<i>{label}</i>".format(label=label)

        super(Label, self).__init__(label=label, **traits)


class LabelWithHyperlinks(TextEditorFactory):
    """ Custom factory for TextEditorReadOnly that supports opening hyperlinks.
    """
    def _get_readonly_editor_class(self):
        return TextEditorReadOnlyWithExternalLinks


class TextEditorReadOnlyWithExternalLinks(BaseTextEditorReadOnly):
    """ Readonly text widget (similar to Label) where hyperlinks do open.

    FIXME: THis needs to be used with an Item for which resizable=True. From
    Robert Kern: you can also override set_size_policy() in this class to get
    this effect by default.
    https://github.com/enthought/traitsui/blob/master/traitsui/qt4/editor.py#L396-L398  # noqa
    """
    def init(self, parent):
        super(BaseTextEditorReadOnly, self).init(parent)
        self.control.setOpenExternalLinks(True)
        # For this to be useful, the Item that uses that editor must have
        # resizable=True
        self.control.setWordWrap(True)

    def set_size_policy(self, direction, resizable, springy, stretch):
        """ Set the size policy of the editor's controller.

        <snip> See parent class for docstring.
        """
        if not resizable:
            import warnings
            msg = "For the text wrapping to behave, the item should have " \
                  "resizable=True"
            warnings.warn(msg)

        super(TextEditorReadOnlyWithExternalLinks, self).set_size_policy(
            direction, resizable, springy, stretch
        )


if __name__ == "__main__":
    from traits.api import HasTraits, Str
    from traitsui.api import View, Item

    class Test(HasTraits):
        view = View(
            Label("blah"),
            Label("blah", color="red", bold=True),
            Label("blah", color="#f133a0", bold=True, italic=True)
        )

    t = Test()
    t.configure_traits()

    class Test(HasTraits):
        text = Str(
            r'<span style=color:#f133a0>Some styled text</span> Jibberish: '
            r'lasjdfl jsadflk jsadfj lkasjdflkj lasjdfklj asfj yoi1243 8 '
            r'<a href=http://www.enthought.com>Enthought!</a> '
            r'and some bold text <b>asdfjlkasjdfei</b>'
        )

        view = View(
            Item(
                'text',
                style='readonly',
                editor=LabelWithHyperlinks(),
                resizable=True,  # THIS IS NECESSARY FOR CORRECT WRAPPING!!!!
            ),
            resizable=True, width=500
        )

    t = Test()
    t.configure_traits()
