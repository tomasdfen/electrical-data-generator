#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# Support module generated by PAGE version 6.1
#  in conjunction with Tcl version 8.6
#    May 13, 2021 09:42:47 PM CEST  platform: Windows NT

import sys

try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

try:
    import ttk
    py3 = False
except ImportError:
    import tkinter.ttk as ttk
    py3 = True

def set_Tk_var():
    global precio_real_in
    precio_real_in = tk.IntVar()
    global demanda_real_in
    demanda_real_in = tk.IntVar()
    global demanda_prev_in
    demanda_prev_in = tk.IntVar()
    global solar_real_in
    solar_real_in = tk.IntVar()
    global solar_prev_in
    solar_prev_in = tk.IntVar()
    global eol_real_in
    eol_real_in = tk.IntVar()
    global eol_prev_in
    eol_prev_in = tk.IntVar()
    global gas_in
    gas_in = tk.IntVar()
    global co2_in
    co2_in = tk.IntVar()

def init(top, gui, *args, **kwargs):
    global w, top_level, root
    w = gui
    top_level = top
    root = top

def destroy_window():
    # Function which closes the window.
    global top_level
    top_level.destroy()
    top_level = None

if __name__ == '__main__':
    import generator
    generator.vp_start_gui()




