import time
import subprocess
from multiprocessing import Process
import sys
import pygatt
from functools import partial
import socket
import os
from kivy.lang import Builder
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.config import Config
Config.set('graphics', 'width', '750')
Config.set('graphics', 'height', '600')
Config.set('graphics', 'resizable', False)
from kivy.uix.image import Image
from kivy.graphics import *
from kivy.uix.checkbox import CheckBox
from kivy.uix.switch import Switch
from kivy.uix.recycleview import RecycleView
from kivy.uix.textinput import TextInput
from kivy.uix.dropdown import DropDown 
from kivy.uix.spinner import Spinner
from uvicmuse.muse import Muse
from .Backend import Backend
import pkg_resources

# from kivy.core.window import Window
# Window.clearcolor = (1, 1, 1, 1)


#Frontend Test Branch
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
        self.current_muse_id = 0

        # Create UVic Muse Logo
        DATA_PATH = pkg_resources.resource_filename('uvicmuse', 'docs/')
        self.img = Image(source=os.path.join(DATA_PATH, 'logo.png'))

        # Initiate Labels
        self.status_label = Label(text="Press Search to Look For Nearby Muse                                                ", color=(.05, .5, .95, 1), font_size=14)
        self.canvas.add(Rectangle(size=(570, 250), pos=(25, 225), color=(1, 1, 1, 1)))
        self.sensors_title = Label(text = "Sensors", color = (.3, .3, 1, 1), font_size = 16)
        self.LSL_title = Label(text = "Lab Streaming", color = (.3, .3, 1, 1), font_size = 16)
        self.LSL2_title = Label(text = "Layer", color = (.3, .3, 1, 1), font_size = 16)
        self.filter_title = Label(text = "Filters", color = (.3, .3, 1, 1), font_size = 16)

        self.search_button = Button(text="Search", size_hint=(.15, .08), pos_hint={'x': 0.82, 'y': .65},
                                    background_color=(.05, .5, .95, 1),on_press= self.update_status_search, on_release=self.search)

        # Initiate Buttons and bind press and release to functions
        self.start_stream_button = Button(text="Start Stream", size_hint=(.15, .08), pos_hint={'x': 0.82, 'y': .55},
                                          background_color=(.05, .5, .95, 1),
                                          on_release=self.stream)
        self.stop_stream_button = Button(text="Stop Stream", size_hint=(.15, .08), pos_hint={'x': 0.82, 'y': .45},
                                         background_color=(.05, .5, .95, 1),
                                         on_release=self.stop_stream)

        self.connect_button = Button(text = "Connect",size_hint=(.13, .08), pos_hint={'x': 0.6, 'y': .65},
                                    background_color=(.05, .5, .95, 12), on_release = self.connect)


        self.disconnect_button = Button(text = "Disonnect",size_hint=(.13, .08), pos_hint={'x': 0.6, 'y': .51},
                                    background_color=(.05, .5, 0.95, 12), on_release = self.disconnect)

        self.LSL_label = Label(text="LSL", color=(.3, .3, 1, 1), font_size=14)
        self.EEG_label = Label(text="EEG", color=(.3, .3, 1, 1), font_size=14)
        self.PPG_label = Label(text="PPG", color=(.3, .3, 1, 1), font_size=14)
        self.ACC_label = Label(text="ACC", color=(.3, .3, 1, 1), font_size=14)
        self.GYRO_label = Label(text="GYRO", color=(.3, .3, 1, 1), font_size=14)
        self.notch_label = Label(text="Notch", color=(.3, .3, 1, 1), font_size=14)        
        self.lowpass_label = Label(text="Lowpass Filter", color=(.3, .3, 1, 1), font_size=14)
        self.highpass_label = Label(text="Highpass Filter", color=(.3, .3, 1, 1), font_size=14)
        self.lowpass_cutoff = Label(text="Cutoff", color=(.3, .3, 1, 1), font_size=14)
        self.highpass_cutoff = Label(text="Cutoff", color=(.3, .3, 1, 1), font_size=14)

        #initiate List with max height
        self.list_box = Spinner(text = "Press for List of Available Muses", values = '', size_hint = (0.5,0.08), pos_hint = {'x': 0.03, 'y':.65} , background_color = (0.3,0.3,1,1) )
        self.list_box.dropdown_cls.max_height = self.list_box.height* 1.6
        

        # Initiate Checkbox's
        self.LSL_checkbox = CheckBox(active=True, size_hint_y=0.02, size_hint_x=0.02)
        self.EEG_checkbox = CheckBox(active=True, size_hint_y=0.02, size_hint_x=0.02)
        self.PPG_checkbox = CheckBox(active=False, size_hint_y=0.02, size_hint_x=0.02)
        self.ACC_checkbox = CheckBox(active=False, size_hint_y=0.02, size_hint_x=0.02)
        self.GYRO_checkbox = CheckBox(active=False, size_hint_y=0.02, size_hint_x=0.02)
        self.lowpass_checkbox = CheckBox(active=False, size_hint_y=0.02, size_hint_x=0.02)
        self.highpass_checkbox = CheckBox(active=False, size_hint_y=0.02, size_hint_x=0.02)
        self.notch_checkbox = CheckBox(active = True, size_hint_y = 0.02, size_hint_x = 0.02)

        # Initiate textbox's to enter text
        self.lowpass_text = TextInput(font_size=13, pos_hint={"x": 0.795, "y": 0.225}, size_hint=(0.07, 0.043),
                                      multiline=False, text='30', write_tab=False)
        self.highpass_text = TextInput(font_size=13, pos_hint={"x": 0.795, "y": 0.092}, size_hint=(0.07, 0.043),
                                       multiline=False, text='0.1', write_tab=False)

        

        # add widgets that have been initiated to frame
        self.add_widget(self.img)
        self.add_widget(self.search_button)
        self.add_widget(self.start_stream_button)
        self.add_widget(self.stop_stream_button)
        self.add_widget(self.status_label)
        self.add_widget(self.lowpass_text)
        self.add_widget(self.highpass_text)
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
        # self.add_widget(self.lowpass_cutoff)
        # self.add_widget(self.highpass_cutoff)
        self.add_widget(self.notch_checkbox)
        self.add_widget(self.notch_label)
        self.add_widget(self.connect_button)
        self.add_widget(self.disconnect_button)
        self.add_widget(self.list_box)
        self.add_widget(self.sensors_title)
        self.add_widget(self.filter_title)
        self.add_widget(self.LSL_title)
        self.add_widget(self.LSL2_title)

        # Adjust positions of widgets that have been added to the frame
        self.img.pos = (0, 220)
        self.status_label.pos = (-155, -90)


        self.EEG_label.pos =  (-263, -157)              
        self.PPG_label.pos =  (-160, -157)
        self.ACC_label.pos = (-263, -200)
        self.GYRO_label.pos = (-160, -200)

        self.notch_label.pos = (170, -190)

        self.LSL_checkbox.pos =  (355, 100)
        self.EEG_checkbox.pos =  (104, 122)         
        self.PPG_checkbox.pos =  (210, 122)
        self.ACC_checkbox.pos = (104, 78)
        self.GYRO_checkbox.pos = (210, 78)

        self.lowpass_label.pos = (140, -150)
        self.highpass_label.pos = (140, -230)
        self.lowpass_checkbox.pos = (570, 142)
        self.highpass_checkbox.pos = (570, 63)
        self.lowpass_cutoff.pos = (235, -150)
        self.highpass_cutoff.pos = (235, -230)
        self.notch_checkbox.pos = (570, 100)

        self.sensors_title.pos = (-210, -125)
        self.LSL_title.pos = (-10, -125)
        self.LSL2_title.pos = (-12, -142)
        self.filter_title.pos = (200, -125)

        #initial state
        self.PPG_checkbox.disabled = True 
        self.LSL_checkbox.disabled = True
        self.EEG_checkbox.disabled = True
        self.ACC_checkbox.disabled = True
        self.GYRO_checkbox.disabled = True
        self.notch_checkbox.disabled = True
        self.lowpass_checkbox.disabled = True
        self.highpass_checkbox.disabled = True  
        self.highpass_text.disabled = True
        self.lowpass_text.disabled = True
        self.start_stream_button.disabled = True
        self.stop_stream_button.disabled = True
        self.connect_button.disabled = True
        self.disconnect_button.disabled = True

    #logic
    
    #As Search takes 10 seconds, update the status before the process begins
    def update_status_search(self, event):
        self.status_label.text = "Searching for nearby Muses, this may take up to ten seconds..."

    #Function to change state of all components
    def button_state(self, connect_state, disconnect_state, search_state, 
                    stream_state, stop_state, LSL_state, EEG_state, PPG_state, 
                    ACC_state, GYRO_state, Notch_state, Lowpass_check_state, 
                    lowpass_cut_state, highpass_check_state, highpass_cut_state, list_box_state):
        self.connect_button.disabled = connect_state
        self.disconnect_button.disabled = disconnect_state
        self.search_button.disabled = search_state
        self.start_stream_button.disabled = stream_state 
        self.stop_stream_button.disabled = stop_state
        self.LSL_checkbox.disabled = LSL_state
        self.EEG_checkbox.disabled = EEG_state
        self.PPG_checkbox.disabled = PPG_state
        self.ACC_checkbox.disabled = ACC_state
        self.GYRO_checkbox.disabled = GYRO_state
        self.notch_checkbox.disabled = Notch_state
        self.lowpass_checkbox.disabled = Lowpass_check_state
        self.lowpass_text.disabled = lowpass_cut_state
        self.highpass_checkbox.disabled = highpass_cut_state
        self.highpass_text.disabled = highpass_cut_state
        self.list_box.disabled = list_box_state

    #Function for starting Data Stream
    def stream(self, event):
        self.button_state(True, True, True, True, False, True, True, True,
            True, True, True, True, True, True, True, True)

        self.backend.udp_stream_btn_callback(
            use_low_pass=self.lowpass_checkbox.active,
            use_high_pass=self.highpass_checkbox.active,
            low_pass_cutoff=(float)(self.get_lowpass_cutoff()),
            high_pass_cutoff=(float)(self.get_highpass_cutoff()),
            use_notch=self.get_notch_checkbox,)
        if self.backend.is_udp_streaming:
            self.status_label.text = "Streaming Data                                                                                                  "
        else:
            self.status_label.text = "Unsuccessful streaming attempt"

    #Function for stopping Data Stream
    def stop_stream(self, event):
        self.button_state(True, False, True, False, True, False, True, True, True, True, 
            False, False, False, False, False, True)       
        self.backend.udp_stop_btn_callback()
        self.status_label.text = "Data stream has been stopped                                                                  "

    def get_lowpass_cutoff(self):
        return float(self.lowpass_text.text)

    def get_highpass_cutoff(self):
        return float(self.highpass_text.text)

    def get_notch_checkbox(self):
        if (self.notch_checkbox.active):
            return True
        return False

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

    #Function for Connecting to selected Muse in Dropdown list
    def connect(self, event):
        try:
            self.button_state(True, False, True, False, True, 
                False, True, True, True, True, 
                False, False, False, False, False, True)

            self.current_muse_id = self.list_box.values.index(self.list_box.text)

            self.backend.connect_btn_callback(self.current_muse_id, self.get_EEG_checkbox(), self.get_PPG_checkbox(),
                                                  self.get_ACC_checkbox(), self.get_GYRO_checkbox())
            self.did_connect = self.backend.is_connected()
            if(self.did_connect):
                self.status_label.text = "                    Successfully connected to " + str(self.muses[0]['name'] + ", select filters to stream data with")
                self.connected_address = self.muses[0]['address']
            else:
                self.status_label.text = "Unsuccessful connection attempt, make sure Muse is turned on                                     "
        except:
            self.status_label.text = "                      Please select a Muse from the dropdown menu before connecting                "
            self.button_state( False, True, False, 
                   True, True, True, False, False, 
                    False, False,True, True, 
                    True, True, True, False)
    
    #Function for Disconnecting from connected Muse
    def disconnect(self, event):
        self.button_state(False, True, 
                   False, True, True, False, False, 
                    False, False,False, False, 
                    False, False, False, False, False)


        self.backend.disconnect_btn_callback()
        self.status_label.text = "Disconnected from " + str(self.muses[self.current_muse_id]['name'] + "                                                                 ")

    #Function for Searching for nearby Muses 
    def search(self, event):
        try:
            self.button_state( False, True, False, 
                   True, True, True, False, False, 
                    False, False,True, True, 
                    True, True, True, False)

            self.muses, succeed = self.backend.refresh_btn_callback()
            self.vals = []
            for i in range(len(self.muses)):
                self.vals.append(self.muses[i]['name'] + " Mac Address " + str(self.muses[i]['address']))

            if(len(self.muses)) == 0:
                self.status_label.text = "No nearby devices were found, please try again                               "
            if(len(self.muses)) == 1:
                self.status_label.text = "1 device was found, please choose sensors to connect with       "
            if(len(self.muses)) > 1:
                self.status_label.text = str(len(self.muses)) + "Devices were found, please choose sensors to connect with       "

            self.list_box.values = self.vals
        except:
            self.status_label.text = "No BLE Module Found                                                                                 "
             
class Muse(App):
    def build(self):
        return UVicMuse()


def runGUI():
    Muse().run()
