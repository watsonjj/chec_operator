from bokeh.models import Button, RadioButtonGroup, Div, Select, TextInput
from bokeh.plotting import curdoc
from bokeh.layouts import layout, widgetbox
from chec_operator.threads import server as server_thread
from chec_operator.utils.filepaths import shorten_path
from chec_operator.utils.enums import OnOffState, LowMedHighState, \
    GUITriggerSettings, CameraState
from chec_operator.runs.calibration import PedestalRun, TFRun
from functools import partial
import tkinter as tk
from tkinter import filedialog, messagebox
from os.path import dirname

PLOTARGS = dict(tools="", toolbar_location=None,
                outline_line_color='#595959', webgl=True)


class ConnectionButtons:
    def __init__(self, secondary):
        self.secondary = secondary

        self.handler = server_thread.SERVER_HANDLER

        self.b_connect = RadioButtonGroup(labels=['DISCONNECT', 'CONNECT'],
                                          active=0)
        self.b_connect.on_click(self.connect)

        self.layout = self.b_connect

    def connect(self, index):
        if self.b_connect.active == 0:
            self.handler.disconnect()
        elif self.b_connect.active == 1:
            self.handler.connect()
            self.secondary.update_time_input()


class StateButtons:
    def __init__(self):
        self.handler = server_thread.SERVER_HANDLER
        self.latest_status = None

        self.b_state_dict = {}
        self.b_state_list = []

        for state in self.handler.known_states:
            b = Button(label=state.name, width=150)
            f = partial(self.transition, state)
            b.on_click(f)

            self.b_state_dict[state] = b
            self.b_state_list.append(b)

        self.layout = widgetbox(self.b_state_list)

    def transition(self, new_state):
        for state, button in self.b_state_dict.items():
            button.disabled = True
            if state == self.latest_status.state:
                button.button_type = 'success'
            elif state == new_state:
                button.button_type = 'warning'
            else:
                button.button_type = 'default'
        self.handler.go_to_state(new_state)

    def update(self):
        new = self.handler.server_status
        if not self.latest_status == new:
            self.latest_status = new
            for state, button in self.b_state_dict.items():
                if state == new.state:
                    button.button_type = 'success'
                    button.disabled = True
                elif state in new.transitions:
                    button.button_type = 'primary'
                    button.disabled = False
                else:
                    button.button_type = 'default'
                    button.disabled = True


class SecondaryButtons:
    def __init__(self):
        self.handler = server_thread.SERVER_HANDLER
        self.latest_status = None

        self.hv_options = list(OnOffState.__members__.keys())
        self.b_hv_updating = False
        self.b_hv = RadioButtonGroup(labels=self.hv_options,
                                     active=self.hv_options.index("MAYBEON"))
        self.b_hv.on_click(self.hv_change)
        t_hv = Div(text="<h3>HV</h3>")

        self.b_hv_level = RadioButtonGroup(labels=['UNKNOWN', 'LOW', 'MED', 'HIGH'],
                                           active=0)
        self.b_hv_level.on_click(self.hv_level_change)
        self.t_hv_level = Div(text="<h3>HV LEVEL (requires ready)</h3>")

        options = list(GUITriggerSettings.__members__.keys())
        self.b_trigger = Select(title="", value=options[0], options=options)
        self.t_trigger = Div(text="<h3>TRIGGER (requires ready)</h3>")

        self.b_trigger_apply = Button(label="APPLY", width=100)
        self.b_trigger_apply.on_click(self.trigger_change)

        self.w_time_input = TextInput()
        self.w_time_input_apply = Button(label="APPLY", width=100)
        self.w_time_input_apply.on_click(self.time_input_change)
        self.w_time_input_refresh = Button(label="REFRESH", width=100)
        self.w_time_input_refresh.on_click(self.update_time_input)
        self.t_time_input = Div(text="<h3>Observation Time (requires ready):</h3>")

        self.tk = tk.Tk()
        self.tk.withdraw()
        self.tk.lift()
        self.tk.attributes('-topmost', True)

        wb_list = [
            [t_hv],
            [self.b_hv],
            [self.t_hv_level],
            [self.b_hv_level],
            [self.t_trigger],
            [self.b_trigger],
            [self.b_trigger_apply],
            [self.t_time_input],
            [self.w_time_input],
            [self.w_time_input_apply, self.w_time_input_refresh]
        ]
        self.layout = layout(wb_list)

    def hv_change(self, index):
        if not self.b_onoff_updating:
            state = OnOffState[self.hv_options[index]]
            if state == OnOffState['ON']:
                msg = "Are you sure it is safe to turn on HV? "
                result = messagebox.askquestion("TURNON", msg, icon='warning',
                                                parent=self.tk)
                if not result == 'yes':
                    return
            self.handler.set_hv_state(state)

    def hv_level_change(self, index):
        if not self.b_hv_level_updating:
            if not self.b_hv_level.disabled:
                state = LowMedHighState(index)
                self.handler.set_hv_level(state)

    def trigger_change(self):
        if not self.b_trigger_updating:
            if not self.b_trigger.disabled:
                self.b_trigger_apply.button_type = 'warning'
                self.b_trigger_apply.disabled = True
                state = GUITriggerSettings[self.b_trigger.value]
                self.handler.set_trigger(state)

    def time_input_change(self):
        self.handler.set_observation_time_from_string(self.w_time_input.value)

    def update(self):
        new = self.handler.server_status
        if not self.latest_status == new:
            self.latest_status = new

            self._update_hv(new)
            self._update_hv_level(new)
            self._update_trigger(new)
            self._update_time_input_buttons(new)

    def _update_hv(self, new):
        self.b_onoff_updating = True
        self.b_hv.active = self.hv_options.index(new.hv.name)
        self.b_onoff_updating = False
        if new.hv.name == "ON":
            self.b_hv.button_type = 'danger'
        elif new.hv.name == "OFF":
            self.b_hv.button_type = 'success'
        else:
            self.b_hv.button_type = 'warning'

    def _update_hv_level(self, new):
        self.b_hv_level_updating = True
        self.b_hv_level.active = new.hv_level.value
        self.b_hv_level_updating = False
        fp = shorten_path(new.hvpath)
        self.t_hv_level.text = "<b>HV LEVEL (requires ready):</b><br>{}".format(fp)
        if new.state == CameraState.READY:
            if new.hv_level > 0:
                self.b_hv_level.button_type = 'success'
            else:
                self.b_hv_level.button_type = 'warning'
            self.b_hv_level.disabled = False
        else:
            self.b_hv_level.button_type = 'default'
            self.b_hv_level.disabled = True

    def _update_trigger(self, new):
        self.b_trigger_updating = True
        # self.b_trigger.value = new.gui_trigger.name
        self.b_trigger_updating = False
        fp = shorten_path(new.triggerpath)
        self.t_trigger.text = """
        <b>TRIGGER (requires ready):</b><br>
        {}<br>
        Current: {}
        """.format(fp, new.gui_trigger.name)
        if new.state == CameraState.READY:
            self.b_trigger.disabled = False
            self.b_trigger_apply.disabled = False
            self.b_trigger_apply.button_type = 'success'
        else:
            self.b_trigger.disabled = True
            self.b_trigger_apply.disabled = True
            self.b_trigger_apply.button_type = 'default'

    def update_time_input(self):
        self.w_time_input.value = self.handler.get_observation_time()

    def _update_time_input_buttons(self, new):
        time = self.handler.get_observation_time()
        self.t_time_input.text = """
        <b>Observation Time (requires ready):</b>
        <br>{}
        """.format(time)
        if new.state == CameraState.READY:
            self.w_time_input_apply.disabled = False
            self.w_time_input_apply.button_type = 'success'
            self.w_time_input_refresh.disabled = False
            self.w_time_input_refresh.button_type = 'success'
        else:
            self.w_time_input_apply.disabled = True
            self.w_time_input_apply.button_type = 'default'
            self.w_time_input_refresh.disabled = True
            self.w_time_input_refresh.button_type = 'default'


class RunButtons:
    def __init__(self):
        self.handler = server_thread.SERVER_HANDLER
        self.latest_status = None

        self.pedestal_run = PedestalRun(self.handler)
        self.tf_run = TFRun(self.handler)

        t_run = Div(text="<h1><u>Runs</u></h1>")

        self.b_pedestal = Button(label="PEDESTAL", width=150)
        self.b_pedestal.on_click(self.pedestal_change)

        self.b_tf = Button(label="TRANSFER FUNCTION", width=150)
        self.b_tf.on_click(self.tf_change)

        wb_list = [
            [t_run],
            [self.b_pedestal],
            [self.b_tf],
        ]
        self.layout = layout(wb_list)

    def pedestal_change(self):
        if not self.b_pedestal.disabled:
            self.b_pedestal.button_type = 'warning'
            self.b_pedestal.disabled = True
            self.running = True
            self.pedestal_run.run()

    def tf_change(self):
        if not self.b_tf.disabled:
            self.b_tf.button_type = 'warning'
            self.b_tf.disabled = True
            self.running = True
            self.tf_run.run()

    def update(self):
        new = self.handler.server_status
        if not self.latest_status == new:
            self.latest_status = new

            self._update_pedestal(new)
            self._update_tf(new)

    def check_running(self):
        if self.pedestal_run.running:
            return True
        if self.tf_run.running:
            return True
        return False

    def _update_pedestal(self, new):
        if self.pedestal_run.running:
            self.b_pedestal.disabled = True
            self.b_pedestal.button_type = 'danger'
        elif self.check_running():
            self.b_pedestal.disabled = True
            self.b_pedestal.button_type = 'default'
        elif new.state == CameraState.READY:
            self.b_pedestal.disabled = False
            self.b_pedestal.button_type = 'success'
        else:
            self.b_pedestal.disabled = True
            self.b_pedestal.button_type = 'default'

    def _update_tf(self, new):
        if self.tf_run.running:
            self.b_tf.disabled = True
            self.b_tf.button_type = 'danger'
        elif self.check_running():
            self.b_tf.disabled = True
            self.b_tf.button_type = 'default'
        elif new.state == CameraState.READY:
            self.b_tf.disabled = False
            self.b_tf.button_type = 'success'
        else:
            self.b_tf.disabled = True
            self.b_tf.button_type = 'default'


# class StatusDisplays:
#     def __init__(self):
#         self.handler = server_thread.SERVER_HANDLER
#         self.latest_status = None
#
#         t_run = Div(text="<h1>Status Displays:</h1>")
#
#         self.b_pedestal = Button(label="PEDESTAL", width=150)
#         self.b_pedestal.on_click(self.pedestal_change)
#
#         self.b_tf = Button(label="TRANSFER FUNCTION", width=150)
#         self.b_tf.on_click(self.tf_change)
#
#         wb_list = [
#             [t_run],
#             [self.b_pedestal],
#             [self.b_tf],
#         ]
#         self.layout = layout(wb_list)
#
#     def pedestal_change(self):
#         if not self.b_pedestal.disabled:
#             self.b_pedestal.button_type = 'warning'
#             self.b_pedestal.disabled = True
#             self.running = True
#             self.pedestal_run.run()
#
#     def tf_change(self):
#         if not self.b_tf.disabled:
#             self.b_tf.button_type = 'warning'
#             self.b_tf.disabled = True
#             self.running = True
#             self.tf_run.run()
#
#     def update(self):
#         new = self.handler.server_status
#         if not self.latest_status == new:
#             self.latest_status = new
#
#             self._update_pedestal(new)
#             self._update_tf(new)
#
#     def check_running(self):
#         if self.pedestal_run.running:
#             return True
#         if self.tf_run.running:
#             return True
#         return False
#
#     def _update_pedestal(self, new):
#         if self.pedestal_run.running:
#             self.b_pedestal.disabled = True
#             self.b_pedestal.button_type = 'danger'
#         elif self.check_running():
#             self.b_pedestal.disabled = True
#             self.b_pedestal.button_type = 'default'
#         elif new.state == CameraState.READY:
#             self.b_pedestal.disabled = False
#             self.b_pedestal.button_type = 'success'
#         else:
#             self.b_pedestal.disabled = True
#             self.b_pedestal.button_type = 'default'
#
#     def _update_tf(self, new):
#         if self.tf_run.running:
#             self.b_tf.disabled = True
#             self.b_tf.button_type = 'danger'
#         elif self.check_running():
#             self.b_tf.disabled = True
#             self.b_tf.button_type = 'default'
#         elif new.state == CameraState.READY:
#             self.b_tf.disabled = False
#             self.b_tf.button_type = 'success'
#         else:
#             self.b_tf.disabled = True
#             self.b_tf.button_type = 'default'


class ExpertButtons:
    def __init__(self):
        self.handler = server_thread.SERVER_HANDLER
        self.latest_status = None

        self.flasher_list = list(OnOffState.__members__.keys())
        self.ds_list = list(OnOffState.__members__.keys())
        self.b_flasher_updating = False
        self.b_ds_updating = False

        self.b_flasher = RadioButtonGroup(labels=self.flasher_list,
                                     active=self.flasher_list.index("MAYBEON"))
        self.b_flasher.on_click(self.flasher_change)
        t_flasher = Div(text="<h3>Flasher</h3>")

        self.b_ds = RadioButtonGroup(labels=self.ds_list,
                                     active=self.ds_list.index("MAYBEON"))
        self.b_ds.on_click(self.ds_change)
        t_ds = Div(text="<h3>Data Sending</h3>")

        t_expert = Div(text="<h1><u>EXPERT</u></h1>")

        wb_list = [
            [t_expert],
            [t_flasher],
            [self.b_flasher],
            [t_ds],
            [self.b_ds],
        ]
        self.layout = layout(wb_list)

    def flasher_change(self, index):
        if not self.b_flasher_updating:
            state = OnOffState[self.flasher_list[index]]
            self.handler.set_flasher_state(state)

    def ds_change(self, index):
        if not self.b_ds_updating:
            state = OnOffState[self.ds_list[index]]
            self.handler.set_data_sending_state(state)

    def update(self):
        new = self.handler.server_status
        if not self.latest_status == new:
            self.latest_status = new

            self._update_flasher(new)
            self._update_ds(new)

    def _update_flasher(self, new):
        self.b_flasher_updating = True
        self.b_flasher.active = self.flasher_list.index(new.flasher.name)
        self.b_flasher_updating = False
        if new.flasher.name == "ON":
            self.b_flasher.button_type = 'danger'
        elif new.flasher.name == "OFF":
            self.b_flasher.button_type = 'success'
        else:
            self.b_flasher.button_type = 'warning'

    def _update_ds(self, new):
        self.b_ds_updating = True
        self.b_ds.active = self.ds_list.index(new.data_sending.name)
        self.b_ds_updating = False
        if new.data_sending.name == "ON":
            self.b_ds.button_type = 'danger'
        elif new.data_sending.name == "OFF":
            self.b_ds.button_type = 'success'
        else:
            self.b_ds.button_type = 'warning'


class FileButtons:
    def __init__(self):
        self.handler = server_thread.SERVER_HANDLER
        self.latest_status = None

        self.b_file_dict = {}
        self.b_file_list = []
        self.b_d_file_list = []

        for type_ in self.handler.known_filetypes:
            b = Button(label=type_.upper(), width=400, button_type='success')
            b_d = Button(label="DEFAULT", width=100, button_type='success')
            f = partial(self.filepath_change, type_)
            f_d = partial(self.filepath_default, type_)
            b.on_click(f)
            b_d.on_click(f_d)

            self.b_file_dict[type_] = b
            self.b_file_list.append(b)
            self.b_d_file_list.append(b_d)

        self.tk = tk.Tk()
        self.tk.withdraw()
        self.tk.lift()
        self.tk.attributes('-topmost', True)

        wb_list = []
        for b, b_d in zip(self.b_file_list, self.b_d_file_list):
            wb_list.append([b, b_d])
        self.layout = layout(wb_list)

    def filepath_change(self, filetype):
        status = self.handler.server_status
        current = dirname(getattr(status, filetype+'path'))
        if not current:
            current = '/home/cta/Software/CHECInterface/trunk/config'
        fp = filedialog.askopenfilename(parent=self.tk, initialdir=current)
        if fp:
            getattr(self.handler, "set_{}_filepath".format(filetype))(fp)

    def filepath_default(self, filetype):
        getattr(self.handler, "set_{}_filepath".format(filetype))("", True)

    def update(self):
        new = self.handler.server_status
        if not self.latest_status == new:
            self.latest_status = new
            for type_, button in self.b_file_dict.items():
                path = shorten_path(getattr(new, type_ + 'path'))
                button.label = "{}: {}".format(type_.upper(), path)


def main():

    # Wait for state to be set
    print("GUI waiting for handler connection...")
    while not server_thread.SERVER_HANDLER:
        pass
    print("Handler waiting for a server status...")
    while not server_thread.SERVER_HANDLER.server_status:
        pass
    print("GUI CONNECTED")

    # Plots

    # Widgets
    w_states = StateButtons()
    w_secondary = SecondaryButtons()
    w_runs = RunButtons()
    w_expert = ExpertButtons()
    w_files = FileButtons()

    w_connection = ConnectionButtons(w_secondary)

    # Layouts
    l_connection = w_connection.layout
    l_states = w_states.layout
    l_secondary = w_secondary.layout
    l_runs = w_runs.layout
    l_expert = w_expert.layout
    l_files = w_files.layout

    # Setup layout
    l = layout([
        [l_connection],
        [l_states, l_secondary, l_runs],
        [l_expert],
        [l_files]
    ])

    curdoc().add_periodic_callback(w_states.update, 100)
    curdoc().add_periodic_callback(w_secondary.update, 100)
    curdoc().add_periodic_callback(w_runs.update, 100)
    curdoc().add_periodic_callback(w_expert.update, 100)
    curdoc().add_periodic_callback(w_files.update, 100)
    curdoc().add_root(l)
    curdoc().title = "States"


# if __name__ == '__main__':
main()
