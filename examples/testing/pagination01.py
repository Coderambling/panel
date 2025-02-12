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
    pagination_position = param.Selector(default='Top', objects=['Top', 'Bottom', 'Both'], doc="Position of the pagination controls.")

    def __init__(self, items, page_size=5, **params):
        super().__init__(**params)

        self.items = items
        self.page_size = page_size

        # Create navigation buttons and a status label
        self._first_button = pn.widgets.Button(name="<<", button_type="primary")
        self._prev_button = pn.widgets.Button(name="<", button_type="primary")
        self._next_button = pn.widgets.Button(name=">", button_type="primary")
        self._last_button = pn.widgets.Button(name=">>", button_type="primary")
        self._page_dropdown = pn.widgets.Select(
            name="Page", options=self._get_page_options(), value=self.page, width=75
        )
        self._page_size_select = pn.widgets.Select(
            name="", options=self.page_size_options, value=self.page_size, width=50
        )
        self._page_label = pn.pane.Markdown()
        self._position_select = pn.widgets.Select(name='Position', options=['Top', 'Bottom', 'Both'], value=self.pagination_position)

        # Register callbacks
        self._first_button.on_click(self._first_page)
        self._prev_button.on_click(self._previous_page)
        self._next_button.on_click(self._next_page)
        self._last_button.on_click(self._last_page)
        self._page_dropdown.param.watch(self._select_page, 'value')
        self._page_size_select.param.watch(self._update_page_size, 'value')
        self._position_select.param.watch(self._update_position, 'value')  # change 004: debugging / logging

        # Initialize the displayed page label
        self._update_page_dropdown()
        self._update_page_label()

        # Initialize the layout
        self.layout = self._create_layout()
        self.param.watch(self._update_layout, 'pagination_position')

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

    def _select_page(self, event):
        """Select a page from the dropdown."""
        self.page = event.new

    @param.depends('page', watch=True)
    def _update_page_dropdown(self):
        """Update the dropdown options that show the page number."""
        self._page_dropdown.options = self._get_page_options()
        self._page_dropdown.value = self.page

    @param.depends('page', watch=True)
    def _update_page_label(self):
        """Update the Markdown label that shows the page number."""
        self._page_label.object = f"**of {self.num_pages}**"

    def _get_page_options(self):
        """Get the list of page options for the dropdown."""
        return {f"Page {i}": i for i in range(1, self.num_pages + 1)}

    def _update_page_size(self, event):
        """Update page_size when the dropdown value changes."""
        self.page_size = event.new
        self.page = 1  # Reset to page 1
        self._update_page_dropdown()
        self._update_page_label()

    def _update_position(self, event):  # change 004: debugging / logging
        """Update pagination_position when the dropdown value changes."""
        self.pagination_position = event.new
        print(f"Updated pagination_position to: {self.pagination_position}")  # change 004: debugging / logging
        self._update_layout()

    @param.depends('page', 'page_size', 'pagination_position')
    def page_view(self):
        """Returns a Panel layout displaying just the items for the current page."""
        start = (self.page - 1) * self.page_size
        end = start + self.page_size
        page_items = self.items[start:end]
        return pn.Column(*page_items, sizing_mode="stretch_width")

    @param.depends('pagination_position')
    def _update_layout(self, event=None):  # change 004: debugging / logging
        print(f"Updating layout with pagination_position: {self.pagination_position}")  # change 004: debugging / logging
        self.layout = self._create_layout()

    def _create_layout(self):  # change 004: debugging / logging
        print(f"Creating layout with pagination_position: {self.pagination_position}")  # change 004: debugging / logging
        pagination_controls = pn.Row(
            self._first_button,
            self._prev_button,
            self._page_dropdown,
            self._page_label,
            self._next_button,
            self._last_button,
            self._page_size_select,
            self._position_select,
            sizing_mode="stretch_width",
            align="center",
        )

        elements = []
        if self.pagination_position in ['Top', 'Both']:
            elements.append(pagination_controls)
        elements.append(self.page_view())
        if self.pagination_position in ['Bottom', 'Both']:
            elements.append(pagination_controls)

        print(f"Elements in layout: {elements}")  # change 004: debugging / logging
        return pn.Column(*elements, sizing_mode="stretch_width")

    def view(self):  # change 004: debugging / logging
        """
        Returns the complete view with navigation buttons,
        page dropdown, page size select, and the current page items.
        """
        print("Calling view method and creating layout")  # change 004: debugging / logging
        self.layout = self._create_layout()
        print(f"View layout: {self.layout}")  # change 004: debugging / logging
        return pn.Column(self.layout)
