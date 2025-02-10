import math
import panel as pn
import param

pn.extension()

class Paginator(param.Parameterized):
    """
    A simple Paginator that displays a subset of items (page) at a time.
    """
    items = param.List(doc="List of items to display.")
    page = param.Integer(default=1, bounds=(1, None), doc="Current page number.")
    page_size = param.Integer(default=5, bounds=(1, None), doc="Number of items per page.")
    page_size_options = param.List(default=[5, 10, 20, 50], doc="Available page size options.")

    def __init__(self, items, page_size=5, **params):
        super().__init__(**params)

        self.items = items
        self.page_size = page_size

        # Create navigation buttons and a status label
        self._first_button = pn.widgets.Button(name="<<", button_type="primary")
        self._prev_button = pn.widgets.Button(name=" <    ", button_type="primary")
        self._next_button = pn.widgets.Button(name="    > ", button_type="primary")
        self._last_button = pn.widgets.Button(name=">>", button_type="primary")
        self._page_label = pn.pane.Markdown()
        self._page_size_select = pn.widgets.Select(
            name="", options=self.page_size_options, value=self.page_size, width=50
        # Name was "Page Size". Removed to prevent Text label from showing
        # above the widget.
        # Use AutcompleteInput instead as an editable widget? https://panel.holoviz.org/reference/widgets/AutocompleteInput.html
        )

        # Register callbacks
        self._first_button.on_click(self._first_page)
        self._prev_button.on_click(self._previous_page)
        self._next_button.on_click(self._next_page)
        self._last_button.on_click(self._last_page)
        self._page_size_select.param.watch(self._update_page_size, 'value')

        # Initialize the displayed page label
        self._update_page_label()

    @property
    def num_pages(self):
        """
        Returns the total number of pages based on items and page_size.
        """
        if not self.items:
            return 1
        return math.ceil(len(self.items) / self.page_size)

    def _previous_page(self, event):
        """Go to the previous page."""
        if self.page > 1:
            self.page -= 1

    def _next_page(self, event):
        """Go to the next page."""
        if self.page < self.num_pages:
            self.page += 1

    def _first_page(self, event):
        """Go to the first page."""
        self.page = 1

    def _last_page(self, event):
        """Go to the last page."""
        self.page = self.num_pages

    @param.depends('page', watch=True)
    def _update_page_label(self):
        """Update the Markdown label that shows the page number."""
        self._page_label.object = f"**Page {self.page} of {self.num_pages}**"

    def _update_page_size(self, event):
        """Update page_size when the dropdown value changes."""
        self.page_size = event.new
        self.page = 1  # Reset to page 1

    @param.depends('page', 'page_size')  # Watch both page and page_size
    def page_view(self):
        """Returns a Panel layout displaying just the items for the current page."""
        start = (self.page - 1) * self.page_size
        end = start + self.page_size
        page_items = self.items[start:end]
        return pn.Column(*page_items, sizing_mode="stretch_width")

    def view(self):
        """
        Returns the complete view with navigation buttons,
        page label, page size select, and the current page items.
        """
        return pn.Column(
            pn.Row(
                self._first_button,
                self._prev_button,
                self._page_label,
                self._next_button,
                self._last_button,
                self._page_size_select,
                sizing_mode="stretch_width",
                align="center",
            ),
            self.page_view,
            sizing_mode="stretch_width",
        )
