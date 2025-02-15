import math
import panel as pn
import param
from datetime import datetime

# Enable notebook extension
pn.extension('tabulator')

CURRENT_TIME = "2025-02-15 16:41:18"  # UTC
CURRENT_USER = "Coderambling"

class Paginator(param.Parameterized):
    """A simple Paginator that displays a subset of items (page) at a time."""
    items = param.List(doc="List of items to display.")
    page = param.Integer(default=1, bounds=(1, None), doc="Current page number.")
    page_size = param.Integer(default=5, bounds=(1, None), doc="Number of items per page.")
    page_size_options = param.List(default=[1, 5, 10, 20, 50], doc="Available page size options.")
    pagination_position = param.Selector(default='Top', objects=['Top', 'Bottom', 'Both'], 
                                      doc="Position of the pagination controls.")

    def __init__(self, items, page_size=5, **params):
        super().__init__(**params)
        self.items = items
        self.page_size = page_size
        
        # Create navigation buttons and controls
        self._first_button = pn.widgets.Button(name="<<", button_type="primary")
        self._prev_button = pn.widgets.Button(name="<", button_type="primary")
        self._next_button = pn.widgets.Button(name=">", button_type="primary")
        self._last_button = pn.widgets.Button(name=">>", button_type="primary")
        self._page_dropdown = pn.widgets.Select(name="Page", options=self._get_page_options(), 
                                              value=self.page, width=75)
        self._page_size_select = pn.widgets.Select(name="Items per page", 
                                                 options=self.page_size_options, 
                                                 value=self.page_size, width=60)
        self._page_label = pn.pane.Markdown("", sizing_mode="fixed")
        self._position_select = pn.widgets.Select(name='Position', 
                                                options=['Top', 'Bottom', 'Both'], 
                                                value=self.pagination_position, width=85)
        
        # Register callbacks
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
        if not self.items: return 1
        return math.ceil(len(self.items) / self.page_size)

    def _previous_page(self, event):
        if self.page > 1:
            self.page -= 1
            self._update_page_dropdown()
            self._update_page_label()

    def _next_page(self, event):
        if self.page < self.num_pages:
            self.page += 1
            self._update_page_dropdown()
            self._update_page_label()

    def _first_page(self, event):
        self.page = 1
        self._update_page_dropdown()
        self._update_page_label()

    def _last_page(self, event):
        self.page = self.num_pages
        self._update_page_dropdown()
        self._update_page_label()

    def _select_page(self, event):
        self.page = event.new
        self._update_page_label()

    def _update_page_dropdown(self):
        current_options = self._get_page_options()
        self._page_dropdown.options = current_options
        self._page_dropdown.value = min(self.page, len(current_options))

    def _update_page_label(self):
        self._page_label.object = f"**of {self.num_pages}**"

    def _get_page_options(self):
        return {f"Page {i}": i for i in range(1, self.num_pages + 1)}

    def _update_page_size(self, event):
        old_page = self.page
        self.page_size = event.new
        new_num_pages = math.ceil(len(self.items) / self.page_size)
        self.page = min(old_page, new_num_pages)
        self._update_page_dropdown()
        self._update_page_label()

    def _update_position(self, event):
        self.pagination_position = event.new

    def _create_pagination_controls(self):
        """Create a new set of pagination controls"""
        first_button = pn.widgets.Button(name="<<", button_type="primary")
        prev_button = pn.widgets.Button(name="<", button_type="primary")
        next_button = pn.widgets.Button(name=">", button_type="primary")
        last_button = pn.widgets.Button(name=">>", button_type="primary")
        page_dropdown = pn.widgets.Select(name="Page",
          options=self._get_page_options(), 
          value=self.page, width=85)
        page_size_select = pn.widgets.Select(name="Items per page", 
          options=self.page_size_options, 
          value=self.page_size, width=50)
        page_label = pn.pane.Markdown(f"**of {self.num_pages}**", sizing_mode="fixed")
        position_select = pn.widgets.Select(name='Position', 
          options=['Top', 'Bottom', 'Both'], 
          value=self.pagination_position, width=80)
        
        # Register callbacks for the new controls
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

    @param.depends('page', 'page_size', 'pagination_position')
    def view(self):
        """Returns the complete view with navigation buttons, page dropdown, 
        page size select, and current page items."""
        # Get current page items
        start = (self.page - 1) * self.page_size
        end = start + self.page_size
        page_items = self.items[start:end]
        
        # Create content pane
        content = pn.Column(*page_items, sizing_mode="stretch_width")
        
        # Create layout based on position
        if self.pagination_position == 'Bottom':
            layout = pn.Column(content, self._create_pagination_controls(), 
                             sizing_mode="stretch_width")
        elif self.pagination_position == 'Top':
            layout = pn.Column(self._create_pagination_controls(), content, 
                             sizing_mode="stretch_width")
        else:  # 'Both'
            layout = pn.Column(
                self._create_pagination_controls(),  # Top controls
                content,
                self._create_pagination_controls(),  # Bottom controls
                sizing_mode="stretch_width"
            )
            
        return layout

# Create demo items
sample_items = [pn.pane.Markdown(f"**Item {i}**: This is sample content for item {i}") 
               for i in range(1, 33)]

# Create paginator
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
