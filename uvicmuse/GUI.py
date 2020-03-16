import socket
import struct

from pylsl import StreamInfo
from functools import partial

from uvicmuse.muse import Muse
from uvicmuse.constants import MUSE_SCAN_TIMEOUT, AUTO_DISCONNECT_DELAY, \
    MUSE_NB_EEG_CHANNELS, MUSE_SAMPLING_EEG_RATE, LSL_EEG_CHUNK, \
    MUSE_NB_PPG_CHANNELS, MUSE_SAMPLING_PPG_RATE, LSL_PPG_CHUNK, \
    MUSE_NB_ACC_CHANNELS, MUSE_SAMPLING_ACC_RATE, LSL_ACC_CHUNK, \
    MUSE_NB_GYRO_CHANNELS, MUSE_SAMPLING_GYRO_RATE, LSL_GYRO_CHUNK
from uvicmuse.Backend import Backend

from tkinter import ttk, font, messagebox
import tkinter as tk

from tkinter import *
from PIL import ImageTk, Image
import pygubu


class HelloWorldApp:

    def __init__(self, master):
        self.master = master

        self.log = "Welcome to UVicMUSE"
        self.muses = []
        self.sock = None
        self.muse = None
        self.did_connect = False
        self.udp_address = ()
        self.connected_address = ""
        self.muse_backend = 'bgapi'  # TODO: Get this from user

        self.backend = Backend(self.muse_backend)

        self.prv_ts = 0
        # 1: Create a builder
        self.builder = pygubu.Builder()

        # 2: Load an ui file
        self.builder.add_from_file('./testGUI.ui')

        self.mainwindow = self.builder.get_object('Toplevel_1')
        self.refresh_btn = self.builder.get_object('Refresh')
        self.frame_list = self.builder.get_object("Frame_list")
        self.log_msg = self.builder.get_object("Label_2")
        self.img_lbl = self.builder.get_object("img_label")

        self.address_entry = self.builder.get_object("address_entry")
        self.port_entry = self.builder.get_object("port_entry")
        self.UDP_send_btn = self.builder.get_object("UDP_send_btn")
        self.UDP_stop_btn = self.builder.get_object("UDP_stop_btn")

        self.connect_btn = self.builder.get_object("Connect")
        self.disconnect_btn = self.builder.get_object("Disconnect")

        self.img = Image.open('./RedMuse.png')
        self.image = self.img.resize((372, 102))
        self.background_image = ImageTk.PhotoImage(self.image)
        self.img_lbl.configure(image=self.background_image)

        list_font = font.Font(family='Helvetica', size=12)  # , weight='bold')

        self.frame_list.yScroll = tk.Scrollbar(self.frame_list, orient=tk.VERTICAL)
        self.frame_list.yScroll.grid(row=0, column=1, sticky=tk.N + tk.S)

        self.frame_list.xScroll = tk.Scrollbar(self.frame_list, orient=tk.HORIZONTAL)
        self.frame_list.xScroll.grid(row=1, column=0, sticky=tk.E + tk.W)

        self.frame_list.listbox = tk.Listbox(self.frame_list, font=list_font,
                                             xscrollcommand=self.frame_list.xScroll.set,
                                             yscrollcommand=self.frame_list.yScroll.set)
        self.frame_list.listbox.grid(row=0, column=0, sticky=tk.N + tk.S + tk.E + tk.W)
        self.frame_list.xScroll['command'] = self.frame_list.listbox.xview
        self.frame_list.yScroll['command'] = self.frame_list.listbox.yview

        self.frame_list.listbox.config(width=70, height=15)
        self.frame_list.listbox.pack()

        self.frame_list.listbox.insert(END, " Refresh to get a list of MUSEs ")

        callbacks = {
            'refresh_btn': self.refresh_callback,
            'connect_callback': self.connect_callback,
            'disconnect_callback': self.disconnect_callback,
            'UDP_send_btn': self.UDP_send_btn_callback,
            'UDP_stop_btn': self.UDP_stop_btn_callback
        }

        self.UDP_stop_btn.configure(state=DISABLED)
        self.UDP_stop_btn.update_idletasks()

        self.UDP_send_btn.configure(state=DISABLED)
        self.UDP_send_btn.update_idletasks()

        self.disconnect_btn.configure(state=DISABLED)
        self.disconnect_btn.update_idletasks()

        self.connect_btn.configure(state=DISABLED)
        self.connect_btn.update_idletasks()

        self.builder.connect_callbacks(callbacks)
        self.master.resizable(True, True)

    def run(self):
        self.mainwindow.mainloop()

    def connect_callback(self):
        id_to_connect = self.frame_list.listbox.curselection()
        if not id_to_connect:
            self.log_msg["text"] = 'Select one device from the list.                                '
            self.log_msg.update_idletasks()
            return
        else:
            id_to_connect = id_to_connect[0]
            self.backend.connect_btn_callback(id_to_connect, True, False, False, False)
            self.log_msg["text"] = 'Connecting to ' + self.backend.get_muse_name() + '...                      '
            self.log_msg.update_idletasks()

            self.did_connect = self.backend.is_connected()

            if self.did_connect:
                self.log_msg["text"] = 'Connected to ' + self.backend.get_muse_name() + '...                 '
                self.log_msg.update_idletasks()

                self.disconnect_btn.configure(state=NORMAL)
                self.disconnect_btn.update_idletasks()

                self.connect_btn.configure(state=DISABLED)
                self.connect_btn.update_idletasks()

                self.UDP_send_btn.configure(state=NORMAL)
                self.UDP_send_btn.update_idletasks()

    def disconnect_callback(self):
        suc = self.backend.disconnect_btn_callback()
        if not suc:
            return

        self.did_connect = False

        self.disconnect_btn.configure(state=DISABLED)
        self.disconnect_btn.update_idletasks()

        self.connect_btn.configure(state=DISABLED)
        self.connect_btn.update_idletasks()

        self.UDP_send_btn.configure(state=DISABLED)
        self.UDP_send_btn.update_idletasks()

        self.log_msg.configure(text='Disconnected from all MUSE devices...                                     ')
        self.log_msg.update_idletasks()

    def UDP_send_btn_callback(self):
        if not self.did_connect:
            messagebox._show("No Connection", "Connect to a MUSE before starting the UDP stream")
            return
        self.backend.udp_stream_btn_callback(int(self.port_entry.get()), self.address_entry.get())

        self.UDP_stop_btn.configure(state=NORMAL)
        self.UDP_stop_btn.update_idletasks()

        self.UDP_send_btn.configure(state=DISABLED)
        self.UDP_send_btn.update_idletasks()

        self.log_msg.configure(text='Streaming over UDP...                                              ')
        self.log_msg.update_idletasks()

    def UDP_stop_btn_callback(self):
        self.backend.udp_stop_btn_callback()

        self.UDP_stop_btn.configure(state=DISABLED)
        self.UDP_stop_btn.update_idletasks()

        self.UDP_send_btn.configure(state=NORMAL)
        self.UDP_send_btn.update_idletasks()

        self.log_msg.configure(text='Streaming over UDP stopped. Still connected to MUSE...                        ')
        self.log_msg.update_idletasks()

    def refresh_callback(self):

        self.log_msg.configure(text='Searching for MUSE devices...                                                ')
        self.log_msg.update_idletasks()

        self.refresh_btn["text"] = "Refreshing..."
        self.refresh_btn.configure(state=DISABLED)
        self.refresh_btn.update_idletasks()

        self.muses, succeed = self.backend.refresh_btn_callback()

        self.refresh_btn.configure(state=NORMAL)
        self.refresh_btn["text"] = "Refresh"
        self.refresh_btn.update_idletasks()

        if not succeed:
            self.log_msg["text"] = 'No MUSEs found...                                                           '
            self.log_msg.update_idletasks()
            size = self.frame_list.listbox.size()
            self.frame_list.listbox.delete(0, size)
            self.frame_list.listbox.insert(END, ' Nothing found. Try again.')
        else:
            self.log_msg["text"] = str(len(self.muses)) + ' MUSEs found. Select one to connect...                     '
            self.log_msg.update_idletasks()
            size = self.frame_list.listbox.size()
            self.frame_list.listbox.delete(0, size)
            for i in range(len(self.muses)):
                self.frame_list.listbox.insert(END, self.muses[i])
            self.connect_btn.configure(state=NORMAL)
            self.connect_btn.update_idletasks()


def runGUI():
    root = Tk()
    root.withdraw()

    root.title('UVic MUSE')
    app = HelloWorldApp(root)
    app.run()
    root.withdraw()
    root.destroy()
