!pip install jupyter_bokeh -q
import math

import panel as pn
import param

pn.extension()

class ColumnController(param.Parameterized):
    order = param.Selector(objects=['Top', 'Bottom', 'Both'], default='Top')

    # Create some widgets
    w1 = pn.widgets.TextInput(name='Selection stuff:')
    w2 = pn.widgets.FloatSlider(name='Slider')

    # Create a Column layout
    column03 = pn.Column('# Column', w1, w2)

    @param.depends('order', watch=True)
    def update_column03(self):
        if self.order == 'Bottom':
            self.column03[:] = [self.w2, self.w1]
        elif self.order == 'Both':
            self.column03[:] = [self.w1, self.w2, self.w1]
        else:
            self.column03[:] = [self.w1, self.w2]

    def view(self):
        return pn.Column(self.column03, pn.Param(self.param, widgets={'order': {'type': pn.widgets.Select}}))

# Create an instance of the class
controller = ColumnController()

# Display the column03 and the dropdown
# JL: works.
controller.view()