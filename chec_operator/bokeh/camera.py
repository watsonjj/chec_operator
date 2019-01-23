import numpy as np
from bokeh.models import ColumnDataSource, TapTool, palettes, ColorBar, \
    LinearColorMapper
from bokeh.plotting import figure
# from matplotlib.cm import viridis
from chec_operator.geometry.modules import get_module_corner_coords, \
    get_module_corner_triangle_coords
from chec_operator.utils.plotting import intensity_to_hex

PLOTARGS = dict(tools="", toolbar_location=None, outline_line_color='#595959')


class ModuleDisplay:
    def __init__(self, image=None, fig=None):
        self._image = None
        self._colors = None
        self._image_min = None
        self._image_max = None
        self._fig = None

        self.cm = None
        self.cb = None

        self.active_patches = []

        x, y = self._get_patch_coordinates()
        n = len(x)
        self.n_patches = n

        palette = palettes.Set1[9]
        palette.remove('#ffff33')
        styles = ['solid', 'dashed', 'dotted', 'dotdash']
        color = [palette[i % (len(palette))] for i in range(n)]
        style = [styles[i // (len(styles)) % (len(styles))] for i in range(n)]

        cdsource_d = dict(x=list(x),
                          y=list(y),
                          image=[None]*n,
                          outline_color=color,
                          outline_style=style,
                          outline_alpha=[0]*n)
        self.cdsource = ColumnDataSource(data=cdsource_d)

        self.image = image
        self.fig = fig

        # self.add_colorbar()
        self.layout = self.fig

    @property
    def fig(self):
        return self._fig

    @fig.setter
    def fig(self, val):
        if val is None:
            val = figure(plot_width=440, plot_height=400, **PLOTARGS)
            val.axis.visible = False
        val.grid.grid_line_color = None
        self._fig = val

        self._draw_camera()

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, val):
        if val is None:
            val = np.zeros(self.n_patches)

        image_min = np.nanmin(val)
        image_max = np.nanmax(val)
        if image_max == image_min:
            image_min -= 1
            image_max += 1
        colors = intensity_to_hex(val, image_min, image_max)

        self._image = val
        self._colors = colors
        self.image_min = image_min
        self.image_max = image_max

        if len(colors) == self.n_patches:
            self.cdsource.data['image'] = colors
        else:
            raise ValueError("Image has a different size {} than the current "
                             "n_patches {}"
                             .format(len(colors), self.n_patches))

    @property
    def image_min(self):
        return self._image_min

    @image_min.setter
    def image_min(self, val):
        self._image_min = val
        if self.cb:
            self.cm.low = np.asscalar(val)

    @property
    def image_max(self):
        return self._image_max

    @image_max.setter
    def image_max(self, val):
        self._image_max = val
        if self.cb:
            self.cm.high = np.asscalar(val)

    def _get_patch_coordinates(self):
        return get_module_corner_coords()

    def _draw_camera(self):
        p = self.fig.patches('x', 'y', color='image',
                             line_color='outline_color',
                             line_alpha='outline_alpha',
                             line_dash='dashed',
                             line_width=3,
                             nonselection_fill_color='image',
                             nonselection_fill_alpha=1,
                             nonselection_line_color='outline_color',
                             nonselection_line_alpha='outline_alpha',
                             source=self.cdsource)

    def enable_pixel_picker(self):
        self.fig.add_tools(TapTool())

        def source_change_response(attr, old, new):
            val = self.cdsource.selected['1d']['indices']
            if val:
                patch = val[0]
                alphas = self.cdsource.data['outline_alpha']
                alphas[patch] = not alphas[patch]

                if patch in self.active_patches:
                    self.active_patches.remove(patch)
                    self.cdsource.data['outline_alpha'] = alphas
                    self.cdsource.trigger('data', None, None)
                else:
                    self.active_patches.append(patch)
                    self.cdsource.data['outline_alpha'] = alphas
                    self.cdsource.trigger('data', None, None)

                self._on_patch_click(patch)

        self.cdsource.on_change('selected', source_change_response)

    def _on_patch_click(self, patch):
        print("Clicked patch: {}".format(patch))
        print("Active Patches: {}".format(self.active_patches))

    def add_colorbar(self):
        self.cm = LinearColorMapper(palette="Viridis256", low=0, high=100,
                                    low_color='white', high_color='red')
        self.cb = ColorBar(color_mapper=self.cm, #label_standoff=6,
                           border_line_color=None, location=(0, 0))
        self.fig.add_layout(self.cb, 'right')
        self.cm.low = np.asscalar(self.image_min)
        self.cm.high = np.asscalar(self.image_max)


class ModuleTriangleDisplay(ModuleDisplay):
    def _get_patch_coordinates(self):
        return get_module_corner_triangle_coords()
