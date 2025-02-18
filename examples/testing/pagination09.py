import panel as pn
import param

# Enable notebook extension (if needed)
pn.extension()

CURRENT_TIME = "2025-02-15 21:30:19"  # UTC
CURRENT_USER = "Coderambling"

def ceiling_div(n, d):
    """Integer ceiling division"""
    return (n + d - 1) // d

class Paginator(param.Parameterized):
    """A simple Paginator that displays a subset of items (page) at a time."""
    items = param.List(doc="List of items to display.")
    page_number = param.Integer(default=1, bounds=(1, None), doc="Current page number.")
    page_size = param.Integer(default=5, bounds=(1, None), doc="Number of items per page.")
    page_size_options = param.List(default=[1, 5, 10, 20, 50], doc="Available page size options.")
    pagination_ui_position = param.Selector(default='Top', objects=['Top', 'Bottom', 'Both'],
                                              doc="Position of the pagination controls.")

    def __init__(self, items, page_size=5, **params):
        super().__init__(**params)
        self.items = items
        self.page_size = page_size

        # Create navigation buttons and controls for the base (will use _create_pagination_controls)
        self._first_button = pn.widgets.Button(name="<<", button_type="primary")
        self._prev_button = pn.widgets.Button(name="<", button_type="primary")
        self._next_button = pn.widgets.Button(name=">", button_type="primary")
        self._last_button = pn.widgets.Button(name=">>", button_type="primary")
        self._page_dropdown = pn.widgets.Select(name="Page", options=self._get_page_options(),
                                                  value=self.page_number, width=75)
        self._page_size_select = pn.widgets.Select(name="Items per page",
                                                     options=self.page_size_options,
                                                     value=self.page_size, width=60)
        self._page_label = pn.pane.Markdown("", sizing_mode="fixed")
        self._position_select = pn.widgets.Select(name='Position',
                                                   options=['Top', 'Bottom', 'Both'],
                                                   value=self.pagination_ui_position, width=85)

        # Register callbacks on controls created in __init__
        self._first_button.on_click(self._first_page)
        self._prev_button.on_click(self._previous_page)
        self._next_button.on_click(self._next_page)
        self._last_button.on_click(self._last_page)
        self._page_dropdown.param.watch(self._select_page, 'value')
        self._page_size_select.param.watch(self._update_page_size, 'value')
        self._position_select.param.watch(self._update_position, 'value')

        # Initialize display
        self._update_page_dropdown()
        self._update_page_label()

    @property
    def num_pages(self):
        """Returns the total number of pages based on items and page_size."""
        if not self.items:
            return 1
        return ceiling_div(len(self.items), self.page_size)

    def _previous_page(self, event):
        if self.page_number > 1:
            self.page_number -= 1
            self._update_page_dropdown()
            self._update_page_label()

    def _next_page(self, event):
        if self.page_number < self.num_pages:
            self.page_number += 1
            self._update_page_dropdown()
            self._update_page_label()

    def _first_page(self, event):
        self.page_number = 1
        self._update_page_dropdown()
        self._update_page_label()

    def _last_page(self, event):
        self.page_number = self.num_pages
        self._update_page_dropdown()
        self._update_page_label()

    def _select_page(self, event):
        self.page_number = event.new
        self._update_page_label()

    def _update_page_dropdown(self):
        current_options = self._get_page_options()
        self._page_dropdown.options = current_options
        self._page_dropdown.value = min(self.page_number, len(current_options))

    def _update_page_label(self):
        self._page_label.object = f"**of {self.num_pages}**"

    def _get_page_options(self):
        return {f"Page {i}": i for i in range(1, self.num_pages + 1)}

    def _update_page_size(self, event):
        old_page = self.page_number
        self.page_size = event.new
        new_num_pages = ceiling_div(len(self.items), self.page_size)
        self.page_number = min(old_page, new_num_pages)
        self._update_page_dropdown()
        self._update_page_label()

    def _update_position(self, event):
        self.pagination_ui_position = event.new

    def _create_pagination_controls(self):
        """Create a new set of pagination controls; these controls will be wrapped in a layout
        whose 'visible' property is then set reactively."""
        first_button = pn.widgets.Button(name="<<", button_type="primary")
        prev_button = pn.widgets.Button(name="<", button_type="primary")
        next_button = pn.widgets.Button(name=">", button_type="primary")
        last_button = pn.widgets.Button(name=">>", button_type="primary")
        page_dropdown = pn.widgets.Select(name="Page", options=self._get_page_options(),
                                          value=self.page_number, width=85)
        page_size_select = pn.widgets.Select(name="Items per page", options=self.page_size_options,
                                             value=self.page_size, width=50)
        page_label = pn.pane.Markdown(f"**of {self.num_pages}**", sizing_mode="fixed")
        position_select = pn.widgets.Select(name='Position',
                                            options=['Top', 'Bottom', 'Both'],
                                            value=self.pagination_ui_position, width=80)

        # Register callbacks for these controls
        first_button.on_click(self._first_page)
        prev_button.on_click(self._previous_page)
        next_button.on_click(self._next_page)
        last_button.on_click(self._last_page)
        page_dropdown.param.watch(self._select_page, 'value')
        page_size_select.param.watch(self._update_page_size, 'value')
        position_select.param.watch(self._update_position, 'value')

        return pn.Row(
            first_button, prev_button,
            page_dropdown, page_label,
            next_button, last_button,
            page_size_select, position_select,
            sizing_mode="stretch_width", align="center"
        )

    @param.depends('page_number', 'page_size', 'pagination_ui_position')
    def view(self):
        """Returns the complete view with navigation controls and paginated items.

        The visibility of the top and bottom controls is bound reactively using pn.bind.
        """
        # Get current page items
        start = (self.page_number - 1) * self.page_size
        end = start + self.page_size
        page_items = self.items[start:end]

        # Create content pane
        content = pn.Column(*page_items, sizing_mode="stretch_width")

        # Create top and bottom pagination controls
        top_controls = self._create_pagination_controls()
        bottom_controls = self._create_pagination_controls()

        # Bind the 'visible' property reactively:
        # When pagination_ui_position is "Top" or "Both", top_controls are visible.
        top_controls.visible = pn.bind(lambda pos: pos in ('Top', 'Both'), self.param.pagination_ui_position)
        # When pagination_ui_position is "Bottom" or "Both", bottom_controls are visible.
        bottom_controls.visible = pn.bind(lambda pos: pos in ('Bottom', 'Both'), self.param.pagination_ui_position)

        # Assemble the layout with both sets of controls always included
        layout = pn.Column(
            top_controls,
            content,
            bottom_controls,
            sizing_mode="stretch_width"
        )
        layout.controls(['visible'])[1]
        return layout

# Create demo items
sample_items = [
    pn.pane.Markdown(f"**Item {i}**: This is sample content for item {i}")
    for i in range(1, 33)
]

# Create paginator instance
paginator = Paginator(items=sample_items, page_size=5)

# Create and display the dashboard
dashboard = pn.Column(
    pn.pane.Markdown(f"### Sample Paginator (Created by {CURRENT_USER} at {CURRENT_TIME})"),
    pn.pane.Markdown("Try the pagination controls below:"),
    paginator.view,
    sizing_mode="stretch_width"
)

# Display in notebook
dashboard
