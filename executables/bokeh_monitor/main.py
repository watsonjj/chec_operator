import numpy as np
from bokeh.models import ColumnDataSource, Button, TapTool, Range1d
from bokeh.plotting import figure, curdoc
from bokeh.layouts import layout
from chec_operator.threads import monitor as monitor_thread
from chec_operator.bokeh.camera import ModuleTriangleDisplay
from chec_operator.geometry.modules import get_module_corner_triangle_coords

PLOTARGS = dict(tools="", toolbar_location=None,
                outline_line_color='#595959', webgl=True)


class InteractiveModuleTriangleDisplay(ModuleTriangleDisplay):
    def __init__(self, parent, image=None, fig=None):
        super().__init__(image=image, fig=fig)
        self.parent = parent
        self.add_colorbar()
        self.enable_pixel_picker()

    def _on_patch_click(self, patch):
        super()._on_patch_click(patch)

        visible = self.parent.lines[patch].visible
        color = self.cdsource.data['outline_color'][patch]
        style = self.cdsource.data['outline_style'][patch]
        self.parent.lines[patch].visible = not visible
        self.parent.lines[patch].glyph.line_color = color
        self.parent.lines[patch].glyph.line_dash = style
        self.parent.texts[patch].visible = not visible
        self.parent.texts[patch].glyph.text_color = color


class TemperatureDisplay(InteractiveModuleTriangleDisplay):
    def __init__(self, parent, image=None, fig=None):
        cdsource_text_d = dict(x=[], y=[], text=[])
        self.cdsource_text = ColumnDataSource(data=cdsource_text_d)
        super().__init__(parent, image=image, fig=fig)

        self.fig.text(source=self.cdsource_text, x='x', y='y', text='text',
                      text_color='white', text_align='center',
                      text_font_size="6pt")

        self.current_mc = None
        self.mask_counts = np.zeros(self.n_patches)
        self.last_image = np.ma.zeros(self.n_patches)

    def _get_patch_coordinates(self):
        x, y = get_module_corner_triangle_coords()
        x = list(x)
        y = list(y)
        cdsource_text_d = dict(x=[], y=[], text=[])

        # Add extra components
        components = ['EX1', 'EX2', 'EX3', 'EX4', 'EX5',
                      'DACQ1', 'DACQ2', 'chiller_ambient', 'chiller_water']
        bins = [5, 2]
        range_ = [[-0.2, 0.2], [0.2, 0.3]]
        _, x_edges, y_edges = np.histogram2d([], [], bins=bins, range=range_)
        for i, comp in enumerate(components):
            c = i % bins[0]
            r = i // bins[0]
            x.append([x_edges[c], x_edges[c+1], x_edges[c+1], x_edges[c]])
            y.append([y_edges[r], y_edges[r], y_edges[r+1], y_edges[r+1]])
            cdsource_text_d['x'].append((x_edges[c] + x_edges[c+1]) / 2)
            cdsource_text_d['y'].append((y_edges[r] + y_edges[r+1]) / 2)
            cdsource_text_d['text'].append(comp)
        self.cdsource_text.data = cdsource_text_d

        return x, y

    def update(self):
        mc = monitor_thread.MONITOR_CONTAINER
        if not mc == self.current_mc and mc is not None:
            self.current_mc = mc
            self.mask_counts += 1
            df = mc.df
            try:
                subdf = df.loc[['temperature']].set_index(['component'])
            except KeyError:
                return

            image = self.last_image
            for i in range(2):
                for j in range(32):
                    component = "TM{}_{}".format(j, i)
                    try:
                        patch = i+(2*j)
                        image[patch] = (subdf.loc[component]['value'])
                        self.mask_counts[patch] = 0
                    except KeyError:
                        pass

            for i in range(5):
                component = "EX{}".format(i+1)
                try:
                    image[64+i] = subdf.loc[component]['value']
                    self.mask_counts[64+i] = 0
                except KeyError:
                    pass
            try:
                image[64+5] = subdf.loc['DACQ1']['value']
                self.mask_counts[64 + 5] = 0
            except KeyError:
                pass
            try:
                image[64+6] = subdf.loc['DACQ2']['value']
                self.mask_counts[64 + 6] = 0
            except KeyError:
                pass
            try:
                image[64+7] = subdf.loc['chiller_ambient']['value']
                self.mask_counts[64 + 7] = 0
            except KeyError:
                pass
            try:
                image[64+8] = subdf.loc['chiller_water']['value']
                self.mask_counts[64 + 8] = 0
            except KeyError:
                pass

            self.image = image
            self.image.mask = self.mask_counts//10


class CategoryPlotter:
    def __init__(self, component_list, title='', y_range=(-5, 50)):

        self.component_list = component_list

        self.lines = []
        self.texts = []
        self.gap = False

        tools = "xpan,xwheel_zoom,xbox_zoom,reset"
        self.fig = figure(plot_width=400, plot_height=400, title=title,
                          x_axis_type="datetime", y_axis_location="right",
                          toolbar_location="left", tools=tools)
        self.fig.x_range.follow = "end"
        # self.fig.x_range.follow_interval = 100000
        self.fig.x_range.range_padding = 0.2
        self.fig.y_range.start = y_range[0]
        self.fig.y_range.end = y_range[1]
        self.fig.xaxis.major_label_text_font_size = "17pt"
        self.fig.yaxis.major_label_text_font_size = "17pt"

        cdsource_d = dict()
        for c in self.component_list:
            key_t = '{}_time'.format(c)
            key_v = '{}_value'.format(c)
            key_n = '{}_name'.format(c)
            cdsource_d[key_t] = []
            cdsource_d[key_v] = []
            cdsource_d[key_n] = []
        self.cdsource = ColumnDataSource(data=cdsource_d)
        self.cdsource_name = ColumnDataSource(data=cdsource_d)
        for c in self.component_list:
            key_t = '{}_time'.format(c)
            key_v = '{}_value'.format(c)
            key_n = '{}_name'.format(c)
            line = self.fig.line(key_t, key_v, source=self.cdsource)
            text = self.fig.text(key_t, key_v, text=key_n,
                                 source=self.cdsource_name,
                                 text_font_size="5pt", text_baseline="middle")
            line.visible = False
            text.visible = False
            self.lines.append(line)
            self.texts.append(text)

        # Range patch
        cdsource_d = dict(x=[], y=[])
        self.cdsource_range = ColumnDataSource(data=cdsource_d)
        self.fig.patches('x', 'y', source=self.cdsource_range,
                         color='red', alpha=0.1, line_alpha=0)

        self.layout = self.fig

    def _update(self, subdf):
        subdf = subdf.set_index(['component'])

        # Update TMs
        cdsource_d = dict()
        min_ = None
        max_ = None
        x_min = None
        x_max = None
        for c in self.component_list:
            key_t = '{}_time'.format(c)
            key_v = '{}_value'.format(c)
            key_n = '{}_name'.format(c)
            try:
                t = subdf.loc[c]['dt']
                v = subdf.loc[c]['value']
                if min_ is None or min_ > v:
                    min_ = v
                    x_min = t
                elif max_ is None or max_ < v:
                    max_ = v
                    x_max = t
            except KeyError:
                t = np.ma.zeros(1)
                t.mask = True
                v = np.ma.zeros(1)
                v.mask = True
                # t = self.cdsource.data[key_t][-1]
                # v = self.cdsource.data[key_v][-1]
            cdsource_d[key_t] = [t]
            cdsource_d[key_v] = [v]
            cdsource_d[key_n] = [c]
        self.cdsource.stream(cdsource_d, rollover=1000)
        self.cdsource_name.stream(cdsource_d, rollover=1)

        # Update Range
        if min_ is None or max_ is None:
            self.gap = True
            return
        elif len(self.cdsource_range.data['x']) > 0 and not self.gap:
            last_x = self.cdsource_range.data['x'][-1]
            last_y = self.cdsource_range.data['y'][-1]
            last_min = last_y[-2]
            last_max = last_y[-1]
            last_x_min = last_x[-2]
            last_x_max = last_x[-1]
        else:
            self.gap = False
            last_min = min_
            last_max = max_
            last_x_min = x_min
            last_x_max = x_max
        x = [last_x_max, last_x_min, x_min, x_max]
        y = [last_max, last_min, min_, max_]
        new = dict(x=[x], y=[y])
        self.cdsource_range.stream(new, rollover=1000)


class TemperaturePlotters(CategoryPlotter):
    def __init__(self):
        component_list = []
        for i in range(2):
            for j in range(32):
                component_list.append("TM{}_{}".format(j, i))
        component_list.extend(['EX1', 'EX2', 'EX3', 'EX4', 'EX5',
                      'DACQ1', 'DACQ2', 'chiller_ambient', 'chiller_water'])
        title = 'Temperature (degrees C)'
        super().__init__(component_list, title)

        self.current_mc = None

        self.camera = TemperatureDisplay(self)

    def update(self):
        mc = monitor_thread.MONITOR_CONTAINER
        if not mc == self.current_mc and mc is not None:
            self.current_mc = mc
            df = mc.df
            try:
                subdf = df.loc[['temperature']]
            except KeyError:
                return
            super()._update(subdf)


def main():
    p_temperature = TemperaturePlotters()

    l_temperature = p_temperature.layout
    l_temperature_display = p_temperature.camera.layout

    # Widgets

    # Setup layout
    l = layout([
        [l_temperature, l_temperature_display]
    ])

    def temperature_update():
        p_temperature.update()
        p_temperature.camera.update()

    curdoc().add_periodic_callback(temperature_update, 100)
    curdoc().add_root(l)
    curdoc().title = "Monitor"


# if __name__ == '__main__':
main()
