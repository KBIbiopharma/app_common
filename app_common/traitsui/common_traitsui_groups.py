from traitsui.api import HGroup, Label, Spring, VGroup


def make_window_title_group(title, title_size=2, align="center",
                            include_blank_spaces=True, blank_height=10):
    """ Return a TraitsUI group displaying an HTML based readonly title.

    Parameters
    ----------
    title : str
        Text to display.

    title_size : int, optional
        Size of the title. The number is inserted in HTML tag <h{i}></h{i}> to
        control the title size. Default is <h2>.

    align : str, optional
        How to align the title in the window: centered, aligned to the left or
        to the right. Valid values are 'center' (default), 'right' or 'left'.

    include_blank_spaces : bool [OPTIONAL, default=True]
        Whether to include a blank line before and after the title.

    blank_height : int [OPTIONAL, default=10]
        Height in pixels of the blank space to leave around the title.
        Ignored if ``include_blank_spaces=False``.
    """
    title = title.replace("\n", "<br>")

    title_item = Label(r"<h{1}>{0}</h{1}>".format(title, title_size))

    elements = []
    if align == "center":
        elements.append(
            HGroup(Spring(), title_item, Spring())
        )
    elif align == "right":
        elements.append(
            HGroup(Spring(), title_item)
        )
    else:
        elements = [VGroup(title_item)]

    if include_blank_spaces:
        elements.insert(0, str(blank_height))
        elements.insert(-1, str(blank_height))

    group = VGroup(*elements)
    return group
