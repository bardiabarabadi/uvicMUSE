import os

import nest_asyncio

nest_asyncio.apply()
# os.environ["KIVY_NO_CONSOLELOG"] = "1"

from importlib import __import__
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.config import Config
from kivy.uix.popup import Popup
import kivy.utils

# from .Backend import Backend
# from .helper import resource_path
# from .constants import *
# from .MuseFinder import MuseFinder


Config.set('graphics', 'width', '750')
Config.set('graphics', 'height', '400')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
from kivy.uix.image import Image
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, Rectangle

from kivy.resources import resource_add_path
import asyncio
import pkg_resources


from uvicmuse.helper import resource_path
from uvicmuse.constants import *

# Frontend Test Branch
# noinspection PyBroadException,PyUnusedLocal
class UVicMuse(FloatLayout):

    def __init__(self, **kwargs):
        super(UVicMuse, self).__init__(**kwargs)
        self.press_search_txt = "Search for a list of Available Muses on BLE"
        self.btn_color = (204 / 256, 213 / 256, 216 / 256, 1)
        self.txt_color = kivy.utils.get_color_from_hex("#5a636c")
        self.chbx_color = kivy.utils.get_color_from_hex("#0f0f0f")
        # self.txt_color = kivy.utils.get_color_from_hex("#F8B195")
        self.muses = []
        self.sock = None
        self.muse = None
        self.did_connect = False
        self.udp_address = 'localhost'
        self.connected_address = ""
        self.host_address = 'localhost'
        self.current_muse_id = 0

        def draw_background(widget, prop):
            with widget.canvas.before:
                Color(rgba=(240 / 256, 240 / 256, 240 / 256, 1))
                Rectangle(pos=self.pos, size=self.size)

        self.bind(size=draw_background)
        self.bind(pos=draw_background)

        # Create UVic Muse Logo
        DATA_PATH = pkg_resources.resource_filename('uvicmuse', 'docs/')
        self.img = Image(source=os.path.join(DATA_PATH, 'Header.png'), allow_stretch=True)

        # Initiate Labels
        self.status_label = Label(
            text="Press Search to Look For Nearby Muse",
            color=self.txt_color, font_size='16sp', pos_hint={'x': 0.033, 'y': .2*3/2-0.15}, size_hint=(1.0, 1.0), halign="left",
            valign="middle")
        self.status_label.bind(size=self.status_label.setter('text_size'))

        self.filter_title = Label(text="Filters", color=self.txt_color, font_size='18sp', bold=True,
                                  pos_hint={'x': -0.4, 'y': -.015*3/2-0.20})

        self.about_button = Button(text="About Us", size_hint=(.15, .07*3/2), pos_hint={'x': 0.82, 'y': 0.5-0.2*3/2-0.15},
                                   background_color=self.btn_color,
                                   on_release=self.about)

        self.search_button = Button(text="Search", size_hint=(.15, .07*3/2), pos_hint={'x': 0.82, 'y': .5+.1*3/2-0.15},
                                    background_color=self.btn_color, on_press=self.update_status_search,
                                    on_release=self.search)

        # Initiate Buttons and bind press and release to functions
        self.connect_button = Button(text="Connect", size_hint=(.15, .07*3/2), pos_hint={'x': 0.82, 'y': .5+0.0*3/2-0.15},
                                     background_color=self.btn_color,
                                     on_release=self.connect, on_press=self.on_connect_press)
        self.stream_button = Button(text="Start Stream", size_hint=(.15, .07*3/2), pos_hint={'x': 0.82, 'y': 0.5-0.1*3/2-0.15},
                                    background_color=self.btn_color,
                                    on_release=self.stream)

        self.lowpass_label = Label(text="Lowpass", color=self.txt_color, font_size='16sp',
                                   pos_hint={'x': -0.25, 'y': .035*3/2-0.2}, halign='left', valign='middle')
        self.notch_label = Label(text="Notch (60Hz)", color=self.txt_color, font_size='16sp',
                                 pos_hint={'x': -0.25, 'y': -.015*3/2-0.2}, halign='left', valign='middle')
        self.highpass_label = Label(text="Highpass", color=self.txt_color, font_size='16sp',
                                    pos_hint={'x': -0.25, 'y': -.065*3/2-0.2}, halign='left', valign='middle')

        # initiate List with max height
        self.list_box = Spinner(text=self.press_search_txt, values='', size_hint=(0.77, 0.07*3/2),
                                pos_hint={'x': 0.03, 'y': .5+0.1*3/2-0.15}, background_color=self.btn_color)
        self.list_box.dropdown_cls.max_height = self.list_box.height * 1.6

        self.lowpass_checkbox = CheckBox(active=False, size_hint_y=0.02*3/2, size_hint_x=0.02,
                                         pos_hint={'x': 0.4, 'y': 0.5 + 0.025*3/2-0.2}, color=self.chbx_color)
        self.notch_checkbox = CheckBox(active=True, size_hint_y=0.02*3/2, size_hint_x=0.02,
                                       pos_hint={'x': 0.4, 'y': 0.5 - 0.025*3/2-0.2}, color=self.chbx_color)
        self.highpass_checkbox = CheckBox(active=False, size_hint_y=0.02*3/2, size_hint_x=0.02,
                                          pos_hint={'x': 0.4, 'y': 0.5 - 0.075*3/2-0.2}, color=self.chbx_color)
        # Initiate textbox's to enter text
        self.lowpass_text = TextInput(font_size='14sp', pos_hint={"x": 0.50, "y": 0.5 + .015*3/2-0.2}, size_hint=(0.07, 0.05*3/2),
                                      multiline=False, text='30', write_tab=False, halign='center',
                                      background_color=(204 / 256, 213 / 256, 216 / 256, 1))
        self.highpass_text = TextInput(font_size='14sp', pos_hint={"x": 0.50, "y": 0.5 - 0.085*3/2-0.2}, size_hint=(0.07, 0.05*3/2),
                                       multiline=False, text='0.1', write_tab=False, halign='center',
                                       background_color=(204 / 256, 213 / 256, 216 / 256, 1))



        # add widgets that have been initiated to frame
        self.add_widget(self.img)
        self.add_widget(self.about_button)
        self.add_widget(self.search_button)
        self.add_widget(self.connect_button)
        self.add_widget(self.stream_button)
        self.add_widget(self.status_label)
        self.add_widget(self.lowpass_text)
        self.add_widget(self.highpass_text)
        self.add_widget(self.lowpass_label)
        self.add_widget(self.highpass_label)
        self.add_widget(self.lowpass_checkbox)
        self.add_widget(self.highpass_checkbox)
        self.add_widget(self.notch_checkbox)
        self.add_widget(self.notch_label)
        self.add_widget(self.list_box)
        self.add_widget(self.filter_title)

        # Adjust positions of widgets that have been added to the frame
        self.img.pos_hint = {'x': 0, 'y': 0.7}
        self.img.size_hint = (1, 0.3)

        self.notch_checkbox.disabled = True
        self.lowpass_checkbox.disabled = True
        self.highpass_checkbox.disabled = True
        self.highpass_text.disabled = True
        self.lowpass_text.disabled = True
        self.stream_button.disabled = True
        self.connect_button.disabled = True

        from uvicmuse.Backend import Backend

        self.backend = Backend()

    # logic

    def on_connect_press(self, event):
        if self.did_connect:
            pass
        else:
            self.status_label.text = "Connecting to the selected MUSE..."

    # As Search takes 10 seconds, update the status before the process begins
    def update_status_search(self, event):
        self.status_label.text = "Searching for nearby Muses, this may take up to ten seconds..."

    # Function to change state of all components
    def button_state(self, search_state, stream_state, notch_state, lowpass_check_state,
                     lowpass_cut_state, highpass_cut_state, list_box_state):
        self.search_button.disabled = search_state
        self.stream_button.disabled = stream_state
        self.notch_checkbox.disabled = notch_state
        self.lowpass_checkbox.disabled = lowpass_check_state
        self.lowpass_text.disabled = lowpass_cut_state
        self.highpass_checkbox.disabled = highpass_cut_state
        self.highpass_text.disabled = highpass_cut_state
        self.list_box.disabled = list_box_state

    def about(self, event):
        popup = Popup(title="About UVicMUSE", content=Label(text='Developed and Designed by \nBardia'
                                                                 'Barabadi\n\nKrigolson Lab '
                                                                 '(Theoretical and \nApplied Neuroscience '
                                                                 'Laboratory)\n\n '
                                                                 'University of Victoria, Canada, 2020.'
                                                            ), size_hint=(None, None), size=(300, 200))
        popup.open()

    def reset(self, event):
        if self.did_connect:
            self.disconnect(event)
        else:
            self.muses = []
            self.muse = []
            self.host_address = 'localhost'
            self.backend = Backend()
            self.current_muse_id = 0
            self.did_connect = False
            self.connect_button.text = "Connect"
            self.connect_button.disabled = True
            self.list_box.values = []
            self.list_box.text = self.press_search_txt

    # Function for starting Data Stream
    def stream(self, event):

        if self.backend.is_udp_streaming:
            self.backend.udp_stop_btn_callback()
            self.status_label.text = "Data stream has been stopped"
            self.stream_button.text = "Start Streaming"

            self.lowpass_checkbox.disabled = False
            self.highpass_checkbox.disabled = False
            self.notch_checkbox.disabled = False
            self.highpass_text.disabled = False
            self.lowpass_text.disabled = False
            # self.LSL_checkbox.disabled = False

            return

        self.button_state(True, False, True, True, True, True, True)

        self.backend.udp_stream_btn_callback(
            use_low_pass=self.lowpass_checkbox.active,
            use_high_pass=self.highpass_checkbox.active,
            low_pass_cutoff=float(self.get_lowpass_cutoff()),
            high_pass_cutoff=float(self.get_highpass_cutoff()),
            use_notch=self.get_notch_checkbox, )
        if self.backend.is_udp_streaming:
            self.status_label.text = "Streaming Data"
            self.stream_button.text = "Stop Streaming"
        else:
            self.status_label.text = "Unsuccessful streaming attempt"

    # Function for stopping Data Stream
    def stop_stream(self, event):
        self.button_state(True, False, False, False, False, False, True)
        self.backend.udp_stop_btn_callback()
        self.status_label.text = "Data stream has been stopped"

    def get_lowpass_cutoff(self):
        return float(self.lowpass_text.text)

    def get_highpass_cutoff(self):
        return float(self.highpass_text.text)

    def get_notch_checkbox(self):
        if self.notch_checkbox.active:
            return True
        return False

    def get_host_entry(self):
        return str(self.host_text.text)

    # Function for Connecting to selected Muse in Dropdown list
    def connect(self, event):

        if self.did_connect:
            self.disconnect(event)
            return

        try:
            self.button_state(True, False, False, False, False, False, True)

            self.current_muse_id = self.list_box.values.index(self.list_box.text)

            self.backend.connect_btn_callback(self.current_muse_id)
            self.did_connect = self.backend.is_connected()
            if self.did_connect:
                self.status_label.text = "Successfully connected to " + str(
                    self.muses[self.current_muse_id].name + ", select filters to stream data with")
                self.connected_address = self.muses[self.current_muse_id].address
                self.connect_button.text = "Disconnect"
            else:
                self.status_label.text = "Unsuccessful connection attempt, make sure Muse is turned on"
        except:
            self.status_label.text = "Please select a Muse from the dropdown menu before connecting"
            self.button_state(False,
                              True, True, True,
                              True, True, False)

    # Function for Disconnecting from connected Muse
    def disconnect(self, event):
        self.button_state(False, True, False,
                          False, False, False, False)

        self.backend.disconnect_btn_callback()
        self.status_label.text = "Disconnected from " + str(self.muses[self.current_muse_id].name)
        self.did_connect = False
        self.connect_button.text = "Connect"
        self.connect_button.disabled = True
        self.list_box.values = []
        self.list_box.text = self.press_search_txt

    # Function for Searching for nearby Muses
    def search(self, event):

        if self.did_connect:
            self.disconnect(event)

        try:
            self.button_state(False,
                              True, True, True,
                              True, True, False)

            self.connect_button.disabled = False

            self.muses, succeed = self.backend.refresh_btn_callback(event)
            self.vals = []
            for i in range(len(self.muses)):
                self.vals.append(self.muses[i].name + ", Address: " + str(self.muses[i].address))

            if (len(self.muses)) == 0:
                self.status_label.text = "No nearby devices were found, please try again                               "
            if (len(self.muses)) == 1:
                self.status_label.text = "1 device was found, please choose sensors to connect with"
            if (len(self.muses)) > 1:
                self.status_label.text = str(
                    len(self.muses)) + " Devices were found, please choose sensors to connect with"

            self.list_box.values = self.vals

            self.list_box.text = str(len(self.muses)) + " Devices were found, Press to choose"
        except:
            self.status_label.text = "No BLE Module Found"


class MuseApp(App):
    title = "uvicMuse"

    def build(self):
        resource_add_path(resource_path('.'))

        return UVicMuse()


def runGUI():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(App.async_run(MuseApp(), async_lib='asyncio'))
    loop.close()
    # MuseApp().run()