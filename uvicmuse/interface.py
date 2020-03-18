import time
import subprocess
from multiprocessing import Process
import sys
import pygatt
from functools import partial
import socket

from kivy.lang import Builder
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.config import Config

Config.set('graphics', 'width', '750')
Config.set('graphics', 'height', '600')
from kivy.uix.image import Image
from kivy.graphics import *
from kivy.uix.checkbox import CheckBox
from kivy.uix.switch import Switch
from kivy.uix.recycleview import RecycleView
from kivy.uix.textinput import TextInput
import os
from uvicmuse.muse import Muse
from uvicmuse.Backend import Backend

import pkg_resources

class UVicMuse(FloatLayout):

    def __init__(self, **kwargs):
        super(UVicMuse, self).__init__(**kwargs)

        self.muses = []
        self.sock = None
        self.muse = None
        self.did_connect = False
        self.udp_address = ""
        self.connected_address = ""
        self.muse_backend = 'bgapi'
        self.host_address = 'localhost'
        self.backend = Backend(self.muse_backend)

        # Create UVic Muse Logo
        DATA_PATH = pkg_resources.resource_filename('uvicmuse', 'docs/')
        self.img = Image(source=os.path.join(DATA_PATH, 'logo.png'))


        # Initiate Labels
        self.list_label1 = Label(text="", color=(0, 0, 0, 1), font_size=17)
        self.list_label2 = Label(text="", color=(0, 0, 0, 1), font_size=17)
        self.status_label = Label(text="Press Search to Look For Muse", color=(.05, .5, .95, 1), font_size=14)
        self.canvas.add(Rectangle(size=(570, 250), pos=(25, 225), color=(1, 1, 1, 1)))
        self.search_button = Button(text="Search", size_hint=(.15, .08), pos_hint={'x': 0.82, 'y': .65},
                                    background_color=(.05, .5, .95, 1), on_release=self.search_logic,
                                    on_press=self.update_status_search)
        self.start_stream_button = Button(text="Start Stream", size_hint=(.15, .08), pos_hint={'x': 0.82, 'y': .55},
                                          background_color=(.05, .5, .95, 1), on_press=self.update_status_stream,
                                          on_release=self.stream)
        self.stop_stream_button = Button(text="Stop Stream", size_hint=(.15, .08), pos_hint={'x': 0.82, 'y': .45},
                                         background_color=(.05, .5, .95, 1), on_press=self.update_status_stream,
                                         on_release=self.stop_stream)
        self.LSL_label = Label(text="LSL", color=(.3, .3, 1, 1), font_size=14)
        self.EEG_label = Label(text="EEG", color=(.3, .3, 1, 1), font_size=14)
        self.PPG_label = Label(text="PPG", color=(.3, .3, 1, 1), font_size=14)
        self.ACC_label = Label(text="ACC", color=(.3, .3, 1, 1), font_size=14)
        self.GYRO_label = Label(text="GYRO", color=(.3, .3, 1, 1), font_size=14)
        self.lowpass_label = Label(text="Lowpass Filter", color=(.3, .3, 1, 1), font_size=14)
        self.highpass_label = Label(text="Highpass Filter", color=(.3, .3, 1, 1), font_size=14)
        self.lowpass_cutoff = Label(text="Cutoff", color=(.3, .3, 1, 1), font_size=14)
        self.highpass_cutoff = Label(text="Cutoff", color=(.3, .3, 1, 1), font_size=14)

        # Initiate Buttons and bind press and release to functions
        self.connect_button1 = Button(text="Connect", size_hint=(.112, .059), pos_hint={'x': .56, 'y': .725},
                                      background_color=(.05, .5, .95, 1))
        self.connect_button1.bind(on_press=partial(self.update_status_connect, 'connect1'),
                                  on_release=partial(self.connect, 'connect1'))

        self.disconnect_button1 = Button(text="Disconnect", size_hint=(.112, .059), pos_hint={'x': .68, 'y': .725},
                                         background_color=(.05, .5, .95, 1))
        self.disconnect_button1.bind(on_press=partial(self.update_status_connect, 'disconnect1'),
                                     on_release=partial(self.disconnect, 'disconnect1'))

        self.connect_button2 = Button(text="Connect", size_hint=(.112, .059), pos_hint={'x': .56, 'y': .59},
                                      background_color=(.05, .5, .95, 1))
        self.connect_button2.bind(on_press=partial(self.update_status_connect, 'connect2'),
                                  on_release=partial(self.connect, 'connect2'))

        self.disconnect_button2 = Button(text="Disconnect", size_hint=(.112, .059), pos_hint={'x': .68, 'y': .59},
                                         background_color=(.05, .5, .95, 1))
        self.disconnect_button2.bind(on_press=partial(self.update_status_connect, 'disconnect2'),
                                     on_release=partial(self.disconnect, 'disconnect2'))

        # Initiate Checkbox's
        self.LSL_checkbox = CheckBox(active=True, size_hint_y=0.02, size_hint_x=0.02)
        self.EEG_checkbox = CheckBox(active=True, size_hint_y=0.02, size_hint_x=0.02)
        self.PPG_checkbox = CheckBox(active=False, size_hint_y=0.02, size_hint_x=0.02)
        self.ACC_checkbox = CheckBox(active=False, size_hint_y=0.02, size_hint_x=0.02)
        self.GYRO_checkbox = CheckBox(active=False, size_hint_y=0.02, size_hint_x=0.02)
        self.lowpass_checkbox = CheckBox(active=False, size_hint_y=0.02, size_hint_x=0.02)
        self.highpass_checkbox = CheckBox(active=False, size_hint_y=0.02, size_hint_x=0.02)

        # Initiate textbox's to enter text
        self.lowpass_text = TextInput(font_size=13, pos_hint={"x": 0.31, "y": 0.055}, size_hint=(0.07, 0.043),
                                      multiline=False, text='30', write_tab=False)
        self.highpass_text = TextInput(font_size=13, pos_hint={"x": 0.706, "y": 0.055}, size_hint=(0.07, 0.043),
                                       multiline=False, text='0.1', write_tab=False)

        # add widgets that have been initiated to frame
        self.add_widget(self.img)
        self.add_widget(self.search_button)
        self.add_widget(self.start_stream_button)
        self.add_widget(self.stop_stream_button)
        self.add_widget(self.status_label)
        self.add_widget(self.lowpass_text)
        self.add_widget(self.highpass_text)
        self.add_widget(self.LSL_label)
        self.add_widget(self.EEG_label)
        self.add_widget(self.PPG_label)
        self.add_widget(self.ACC_label)
        self.add_widget(self.GYRO_label)
        self.add_widget(self.LSL_checkbox)
        self.add_widget(self.EEG_checkbox)
        self.add_widget(self.PPG_checkbox)
        self.add_widget(self.ACC_checkbox)
        self.add_widget(self.GYRO_checkbox)
        self.add_widget(self.lowpass_label)
        self.add_widget(self.highpass_label)
        self.add_widget(self.lowpass_checkbox)
        self.add_widget(self.highpass_checkbox)
        self.add_widget(self.lowpass_cutoff)
        self.add_widget(self.highpass_cutoff)

        # Adjust positions of widgets that have been added to the frame
        self.img.pos = (0, 220)
        self.status_label.pos = (-250, -90)
        self.LSL_label.pos = (-120, -153)
        self.EEG_label.pos = (-20, -153)
        self.PPG_label.pos = (80, -153)
        self.ACC_label.pos = (180, -153)
        self.GYRO_label.pos = (280, -153)
        self.LSL_checkbox.pos = (247.5, 122)
        self.EEG_checkbox.pos = (347, 122)
        self.PPG_checkbox.pos = (447, 122)
        self.ACC_checkbox.pos = (547, 122)
        self.GYRO_checkbox.pos = (647, 122)
        self.lowpass_label.pos = (-193, -230)
        self.highpass_label.pos = (102, -230)
        self.lowpass_checkbox.pos = (250, 63)
        self.highpass_checkbox.pos = (547, 63)
        self.lowpass_cutoff.pos = (-170, -255)
        self.highpass_cutoff.pos = (125, -255)

    # logic
    def update_status_stream(self, event):
        self.status_label.text = "Starting UDP stream     "

    def stream(self, event):
        if not (self.did_connect):
            print("not connected")
            self.status_label.text = "Not connnected to Muse, please connect"
        else:
            print("stream")
            self.backend.udp_stream_btn_callback(
                                                 self.lowpass_checkbox.active, self.highpass_checkbox.active,
                                                 (float)(self.get_lowpass_cutoff()), (float)(self.get_highpass_cutoff())
                                                 , use_notch=True)  # TODO: Replace True with checkbox
            if self.backend.is_udp_streaming:
                print("streaming")
            else:
                print("not streaming")

    def stop_stream(self, event):
        self.backend.udp_stop_btn_callback()

    def get_lowpass_cutoff(self):
        return float(self.lowpass_text.text)

    def get_highpass_cutoff(self):
        return float(self.highpass_text.text)

    def get_LSL_checkbox(self):
        if (self.LSL_checkbox.active):
            return True
        return False

    def get_EEG_checkbox(self):
        if (self.EEG_checkbox.active):
            return True
        return False

    def get_PPG_checkbox(self):
        if (self.PPG_checkbox.active):
            return True
        return False

    def get_ACC_checkbox(self):
        if (self.ACC_checkbox.active):
            return True
        return False

    def get_GYRO_checkbox(self):
        if (self.GYRO_checkbox.active):
            return True
        return False

    def get_host_entry(self):
        return str(self.host_text.text)

    def update_status_connect(self, button, event):
        if (button) == 'connect1':
            self.status_label.text = "Connecting to " + str(self.muses[0]['name'] + "            ")
        if (button) == 'disconnect1':
            self.status_label.text = "Disconnecting from " + str(self.muses[0]['name'])
        if (button) == 'connect2':
            self.status_label.text = "Connecting to " + str(self.muses[1]['name'] + "            ")
        if (button) == 'disconnect2':
            self.status_label.text = "Disconnecting from " + str(self.muses[1]['name'])

    def connect(self, button, event):
        if (button) == "connect1":
            if (self.backend.is_connected()):
                self.status_label.text = "Already Connected to Muse"
            else:
                self.backend.connect_btn_callback(0, self.get_EEG_checkbox(), self.get_PPG_checkbox(),
                                                  self.get_ACC_checkbox(), self.get_GYRO_checkbox())
                self.did_connect = self.backend.is_connected()
                if (self.did_connect):
                    self.status_label.text = "Successfully connected to " + str(self.muses[0]['name'])
                    self.connected_address = self.muses[0]['address']
                    print(self.connected_address)
                else:
                    self.status_label.text = "Unsuccessful connection attempt"

        if (button) == "connect2":
            if (self.backend.is_connected()):
                self.status_label.text = "Already Connected to Muse"
            else:
                self.backend.connect_btn_callback(1, self.get_EEG_checkbox(), self.get_PPG_checkbox(),
                                                  self.get_ACC_checkbox(), self.get_GYRO_checkbox())
                self.did_connect = self.backend.is_connected()
                if (self.did_connect):
                    self.status_label.text = "Succesfully connected to " + str(self.muses[1]['name'])
                    self.connected_address = self.muses[1]['address']
                    print(self.connected_address)
                else:
                    self.status_label.text = "Unsuccessful connection attempt"

    def disconnect(self, button, event):
        if (button) == 'disconnect1':
            if (self.backend.disconnect_btn_callback()):
                self.status_label.text = "Disconnected from " + str(self.muses[0]['name'])
            else:
                self.status_label.text = "Not connected to a Muse"

        if (button) == 'disconnect2':
            if (self.backend.disconnect_btn_callback()):
                self.status_label.text = "Disconnected from " + str(self.muses[1]['name'])
            else:
                self.status_label.text = "Not connected to a Muse"

    def update_status_search(self, event, ):
        self.status_label.text = "Searching For Muse, Please Wait"

    def search_logic(self, event):
        self.muses, succeed = self.backend.refresh_btn_callback()
        devices = (len(self.muses))
        if (devices) == 1:
            self.status_label.text = " 1 device was found                            "
        else:
            self.status_label.text = str(devices) + " devices were found                        "
        if (devices) == 1:
            self.add_widget(self.list_label1)
            self.list_label1.pos = (-170, 150)
            self.list_label1.text = str(self.muses[0]['name']) + ", Mac Address " + str(self.muses[0]['address'])
            self.add_widget(self.connect_button1)
            self.add_widget(self.disconnect_button1)
        if (devices) == 2:
            self.add_widget(self.list_label1)
            self.list_label1.pos = (-170, 150)
            self.list_label1.text = str(self.muses[0]['name']) + ", Mac Address " + str(self.muses[0]['address'])
            self.add_widget(self.connect_button1)
            self.add_widget(self.disconnect_button1)
            self.add_widget(self.list_label2)
            self.list_label2.pos = (-170, 70)
            self.list_label2.text = str(self.muses[1]['name']) + ", Mac Address " + str(self.muses[1]['address'])
            self.add_widget(self.connect_button2)
            self.add_widget(self.disconnect_button2)


class app1(App):
    def build(self):
        return UVicMuse()


def runGUI():
    app1().run()
