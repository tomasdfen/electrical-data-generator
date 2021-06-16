#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# GUI module generated by PAGE version 6.1
#  in conjunction with Tcl version 8.6
#    May 13, 2021 09:43:03 PM CEST  platform: Windows NT

from tkcalendar import DateEntry
import generator_support
from tkinter.font import names
from ESIOS import ESIOS
import requests
import xlrd
import pandas as pd
from datetime import datetime
from tkinter.constants import DISABLED
from tkinter.filedialog import asksaveasfilename
from tkinter import messagebox

token = "c1308fa94915ff56abb97afc626cf162a9936b7bd960aa45303cb1279f0b701f"
esios = ESIOS(token=token)


try:
    import Tkinter as tk
    
except ImportError:
    import tkinter as tk

END = tk.END
try:
    import ttk
    py3 = False
except ImportError:
    import tkinter.ttk as ttk
    py3 = True


def vp_start_gui():
    '''Starting point when module is the main routine.'''
    global val, w, root
    root = tk.Tk()
    generator_support.set_Tk_var()
    top = generator(root)
    generator_support.init(root, top)
    root.mainloop()


w = None


def create_generator(rt, *args, **kwargs):
    '''Starting point when module is imported by another module.
       Correct form of call: 'create_generator(root, *args, **kwargs)' .'''
    global w, w_win, root
    #rt = root
    root = rt
    w = tk.Toplevel(root)
    generator_support.set_Tk_var()
    top = generator(w)
    generator_support.init(w, top, *args, **kwargs)
    return (w, top)


def destroy_generator():
    global w
    w.destroy()
    w = None

class IntEntry(tk.Entry):
    def __init__(self, master=None, **kwargs):
        self.var = tk.StringVar()
        self.var.set(1)
        ttk.Entry.__init__(self, master, textvariable=self.var, **kwargs)
        self.old_value = ''
        self.var.trace('w', self.check)
        self.get, self.set = self.var.get, self.var.set

    def check(self, *args):
        if self.get().isdigit(): 
            # the current value is only digits; allow this
            self.old_value = self.get()
        elif self.get() == '' or int(self.get()) == 0:
            self.set(1)

        else:
            # there's non-digit characters in the input; reject this 
            self.set(self.old_value)
            
            
def intValidation(s):
    if s.isdigit():
        return True
    else:
        return False


def to_timeseries_ESIOS(writer, df_list, steps, names):

    if isinstance(steps, int):
        steps = [steps for _ in df_list]
    else:
        assert len(df_list) == len(
            steps), "La cantidad de pasos no se corresponden con la cantidad de DataFrames"

    for i, df in enumerate(df_list):

        current_df = df.copy()

        current_df = current_df.drop(
            ['datetime', 'tz_time', 'geo_id', 'geo_name'], axis=1)
        current_df = current_df.resample("1H").sum()
        current_df.columns = [names[i]]
        print(names[i])
        for j in range(steps[i] - 1):
            current_df[f"{current_df.columns[0]}-{j+1}"] = current_df[current_df.columns[0]
                                                                      ].shift(j+1)

        current_df.dropna(inplace=True)
        current_df.index = current_df.index.tz_localize(None)
        current_df.to_excel(writer, sheet_name=current_df.columns[0][:31])

    writer.save()


def to_timeseries_GAS(writer, start, end):
    products = ["GWDES", "GDAES_D+1","GDAES_D+2","GDAES_D+3"]
    gas_url = "https://www.mibgas.es/es/file-access/MIBGAS_Data_{date}.xlsx?path=AGNO_{date}/XLS"
    years = set((start.year, end.year))
    urls = [gas_url.format(date=_year)
            for _year in range(min(years), max(years)+1)]
    gas_data = pd.DataFrame()

    for u in urls:
        r = requests.get(u, stream=True)
        try:
            temp = pd.read_excel(r.content, parse_dates=True, index_col=0, usecols=[
                'Trading day', 'Product', 'Last Daily Price\n[EUR/MWh]'], sheet_name="Trading Data PVB&VTP")
            print(temp)
            gas_data = gas_data.append(temp)

        except xlrd.biffh.XLRDError:
            temp = pd.read_excel(r.content, parse_dates=True, index_col=0, usecols=[
                'Trading day', 'Product', 'Last Daily Price\n[EUR/MWh]'], sheet_name="Trading Data PVB")
            print(temp)
            gas_data = gas_data.append(temp)
        except:
            print(f"Error con url {u}")
    gas_data.sort_index(inplace=True, level=0, sort_remaining=True)
    gas_data = gas_data[gas_data.Product.isin(products)]
    gas_data = gas_data[start:end]
    date = gas_data.index
    print(gas_data.columns)
    product = gas_data['Product'][:]
    gas_data.drop(['Product'], axis=1, inplace=True)
    gas_data.index = [date, product]
    gas_data.reindex(products, level=1)
    print(gas_data)
    gas_data.to_excel(writer, sheet_name="Precio Gas Natural")

    writer.save()


def to_timeseries_CO2(writer, start, end):
    def dateparse(x): return datetime.strptime(x, '%d-%m-%Y')
    co2_url = "https://www.sendeco2.com/site_sendeco/service/download-csv.php?year={year}"
    years = set((start.year, end.year))
    urls = [co2_url.format(year=_year)
            for _year in range(min(years), max(years)+1)]
    co2_data = pd.DataFrame()
    for u in urls:
        r = requests.get(u, stream=True)
        co2_data = co2_data.append(pd.read_csv(
            r.raw, parse_dates=True, index_col=0, date_parser=dateparse, sep=';'))

    co2_data = co2_data[start:end]

    co2_data.to_excel(writer, sheet_name='Precio CO2')

    writer.save()


class generator:
    def generate(self):

        df_list = []
        steps = []
        names = []
        if generator_support.precio_real_in.get():
            names += esios.get_names((10211,)).tolist()
            df_list.append(esios.get_data(10211,
                                          datetime.combine(
                                              self.from_precio_real.get_date(), datetime.min.time()),
                                          datetime.combine(self.to_precio_real.get_date(), datetime.min.time())))
            steps.append(int(self.steps_precio_real.get()))
        if generator_support.demanda_real_in.get():
            names += esios.get_names((1293,)).tolist()
            df_list.append(esios.get_data(1293,
                                          datetime.combine(
                                              self.from_demanda_real.get_date(), datetime.min.time()),
                                          datetime.combine(self.to_demanda_real.get_date(), datetime.min.time())))
            steps.append(int(self.steps_demanda_real.get()))
        if generator_support.demanda_prev_in.get():
            names += esios.get_names((544,)).tolist()
            df_list.append(esios.get_data(544,
                                          datetime.combine(
                                              self.from_demanda_prevista.get_date(), datetime.min.time()),
                                          datetime.combine(self.to_demanda_prevista.get_date(), datetime.min.time())))
            steps.append(int(self.steps_demanda_prev.get()))
        if generator_support.solar_real_in.get():
            names += esios.get_names((10206,)).tolist()
            df_list.append(esios.get_data(10206,
                                          datetime.combine(
                                              self.from_gen_solar_real.get_date(), datetime.min.time()),
                                          datetime.combine(self.to_gen_solar_real.get_date(), datetime.min.time())))
            steps.append(int(self.steps_gen_solar_real.get()))
        if generator_support.solar_prev_in.get():
            names += esios.get_names((10034,)).tolist()
            df_list.append(esios.get_data(10034,
                                          datetime.combine(
                                              self.from_gen_solar_prevista.get_date(), datetime.min.time()),
                                          datetime.combine(self.to_gen_solar_prevista.get_date(), datetime.min.time())))
            steps.append(int(self.steps_gen_solar_prev.get()))
        if generator_support.eol_real_in.get():
            names += esios.get_names((551,)).tolist()
            df_list.append(esios.get_data(551,
                                          datetime.combine(
                                              self.from_gen_eol_real.get_date(), datetime.min.time()),
                                          datetime.combine(self.to_gen_eol_real.get_date(), datetime.min.time())))
            steps.append(int(self.steps_gen_eol_real.get()))
        if generator_support.eol_prev_in.get():
            names += esios.get_names((541,)).tolist()
            df_list.append(esios.get_data(541,
                                          datetime.combine(
                                              self.from_gen_eol_prevista.get_date(), datetime.min.time()),
                                          datetime.combine(self.to_gen_eol_prevista.get_date(), datetime.min.time())))
            steps.append(int(self.steps_gen_eol_prevista.get()))

        filename = asksaveasfilename(initialdir="/", initialfile="dataset.xlsx", defaultextension=".xlsx",
                                     title="Guardar fichero", filetypes=(("archivos de Excel", "*.xlsx"), ("Todos los archivos", "*.*")))

        print(filename)

        writer = pd.ExcelWriter(filename, engine="openpyxl", mode='w', options={  # pylint: disable=abstract-class-instantiated
                                'remove_timezone': True})

        try:
            if df_list:
                to_timeseries_ESIOS(writer, df_list, steps, names)
        except Exception as e:
            print("Error escribiendo de ESIOS")
            print(e)

        try:
            if generator_support.gas_in.get():
                to_timeseries_GAS(writer,
                                  datetime.combine(
                                      self.from_gas.get_date(), datetime.min.time()),
                                  datetime.combine(self.to_gas.get_date(), datetime.min.time()))
        except Exception as e:
            print("Error escribiendo de ESIOS")
            print(e)

        try:
            if generator_support.co2_in.get():
                to_timeseries_CO2(writer,
                                  datetime.combine(
                                      self.from_co2.get_date(), datetime.min.time()),
                                  datetime.combine(self.to_co2.get_date(), datetime.min.time()))
        except Exception as e:
            print("Error escribiendo de ESIOS")
            print(e)
        messagebox.showinfo(title="Generador dataset", message="Hecho")

    def __init__(self, top=None):
        _bgcolor = '#d9d9d9'  # X11 color: 'gray85'
        _fgcolor = '#000000'  # X11 color: 'black'
        _compcolor = '#d9d9d9'  # X11 color: 'gray85'
        _ana1color = '#d9d9d9'  # X11 color: 'gray85'
        _ana2color = '#ececec'  # Closest X11 color: 'gray92'

        top.geometry("1200x512+312+143")
        top.minsize(120, 1)
        top.maxsize(3844, 1061)
        top.resizable(1,  1)
        top.title("Generador dataset")
        top.configure(background="#d9d9d9")
        top.configure(highlightbackground="#d9d9d9")
        top.configure(highlightcolor="black")

        reg = top.register(intValidation)

        self.labelframe_precio = tk.LabelFrame(top)
        self.labelframe_precio.place(
            relx=0.04, rely=0.024, height=70, relwidth=0.92)
        self.labelframe_precio.configure(relief='groove')
        self.labelframe_precio.configure(foreground="black")
        self.labelframe_precio.configure(text='''Precio tiempo real''')
        self.labelframe_precio.configure(background="#d9d9d9")
        self.labelframe_precio.configure(highlightbackground="#d9d9d9")
        self.labelframe_precio.configure(highlightcolor="black")

        self.precio_real_in = tk.Checkbutton(self.labelframe_precio)
        self.precio_real_in.place(
            relx=0.056, rely=0.4, relheight=0.338, relwidth=0.113, bordermode='ignore')
        self.precio_real_in.configure(activebackground="#ececec")
        self.precio_real_in.configure(activeforeground="#000000")
        self.precio_real_in.configure(background="#d9d9d9")
        self.precio_real_in.configure(disabledforeground="#a3a3a3")
        self.precio_real_in.configure(foreground="#000000")
        self.precio_real_in.configure(highlightbackground="#d9d9d9")
        self.precio_real_in.configure(highlightcolor="black")
        self.precio_real_in.configure(justify='left')
        self.precio_real_in.configure(text='''Incluir''')
        self.precio_real_in.configure(command=lambda : messagebox.showinfo("Aviso", "Ten en cuenta que ESIOS no dispone de variable asociada a precio previsto. Esto puede significar que optes por ampliar el intervalo de tiempo en el que quieras los datos de precio"))
        self.precio_real_in.configure(
            variable=generator_support.precio_real_in)

        self.from_precio_real = DateEntry(self.labelframe_precio)
        self.from_precio_real.place(
            relx=0.204, rely=0.308, height=30, relwidth=0.324, bordermode='ignore')
        self.from_precio_real.configure(background="white")
        self.from_precio_real.configure(disabledforeground="#a3a3a3")
        self.from_precio_real.configure(font="TkFixedFont")
        self.from_precio_real.configure(foreground="#000000")

        self.to_precio_real = DateEntry(self.labelframe_precio)
        self.to_precio_real.place(
            relx=0.574, rely=0.308, height=30, relwidth=0.324, bordermode='ignore')
        self.to_precio_real.configure(background="white")
        self.to_precio_real.configure(disabledforeground="#a3a3a3")
        self.to_precio_real.configure(font="TkFixedFont")
        self.to_precio_real.configure(foreground="#000000")

        self.steps_precio_real = IntEntry(self.labelframe_precio)
        self.steps_precio_real.place(
            relx=0.917, rely=0.308, height=30, relwidth=0.063, bordermode='ignore')
        self.steps_precio_real.configure(background="white")
        self.steps_precio_real.configure(font="TkFixedFont")
        
        
        
        self.labelframe_demanda = tk.LabelFrame(top)
        self.labelframe_demanda.place(
            relx=0.04, rely=0.180, height=70, relwidth=0.45)
        self.labelframe_demanda.configure(relief='groove')
        self.labelframe_demanda.configure(foreground="black")
        self.labelframe_demanda.configure(text='''Demanda tiempo real''')
        self.labelframe_demanda.configure(background="#d9d9d9")
        self.labelframe_demanda.configure(highlightbackground="#d9d9d9")
        self.labelframe_demanda.configure(highlightcolor="black")

        self.demanda_real_in = tk.Checkbutton(self.labelframe_demanda)
        self.demanda_real_in.place(
            relx=0.056, rely=0.4, relheight=0.338, relwidth=0.113, bordermode='ignore')
        self.demanda_real_in.configure(activebackground="#ececec")
        self.demanda_real_in.configure(activeforeground="#000000")
        self.demanda_real_in.configure(background="#d9d9d9")
        self.demanda_real_in.configure(disabledforeground="#a3a3a3")
        self.demanda_real_in.configure(foreground="#000000")
        self.demanda_real_in.configure(highlightbackground="#d9d9d9")
        self.demanda_real_in.configure(highlightcolor="black")
        self.demanda_real_in.configure(justify='left')
        self.demanda_real_in.configure(text='''Incluir''')
        self.demanda_real_in.configure(
            variable=generator_support.demanda_real_in)

        self.from_demanda_real = DateEntry(self.labelframe_demanda)
        self.from_demanda_real.place(
            relx=0.204, rely=0.308, height=30, relwidth=0.324, bordermode='ignore')
        self.from_demanda_real.configure(background="white")
        self.from_demanda_real.configure(disabledforeground="#a3a3a3")
        self.from_demanda_real.configure(font="TkFixedFont")
        self.from_demanda_real.configure(foreground="#000000")

        self.to_demanda_real = DateEntry(self.labelframe_demanda)
        self.to_demanda_real.place(
            relx=0.574, rely=0.308, height=30, relwidth=0.324, bordermode='ignore')
        self.to_demanda_real.configure(background="white")
        self.to_demanda_real.configure(disabledforeground="#a3a3a3")
        self.to_demanda_real.configure(font="TkFixedFont")
        self.to_demanda_real.configure(foreground="#000000")

        self.steps_demanda_real = IntEntry(self.labelframe_demanda)
        self.steps_demanda_real.place(
            relx=0.917, rely=0.308, height=30, relwidth=0.063, bordermode='ignore')
        self.steps_demanda_real.configure(background="white")
        self.steps_demanda_real.configure(font="TkFixedFont")
        
        self.labelframe_demanda_prevista = tk.LabelFrame(top)
        self.labelframe_demanda_prevista.place(
            relx=0.51, rely=0.180, height=70, relwidth=0.45)
        self.labelframe_demanda_prevista.configure(relief='groove')
        self.labelframe_demanda_prevista.configure(foreground="black")
        self.labelframe_demanda_prevista.configure(text='''Demanta previsa''')
        self.labelframe_demanda_prevista.configure(background="#d9d9d9")
        self.labelframe_demanda_prevista.configure(
            highlightbackground="#d9d9d9")
        self.labelframe_demanda_prevista.configure(highlightcolor="black")

        self.demanda_prev_in = tk.Checkbutton(self.labelframe_demanda_prevista)
        self.demanda_prev_in.place(
            relx=0.056, rely=0.4, relheight=0.338, relwidth=0.113, bordermode='ignore')
        self.demanda_prev_in.configure(activebackground="#ececec")
        self.demanda_prev_in.configure(activeforeground="#000000")
        self.demanda_prev_in.configure(background="#d9d9d9")
        self.demanda_prev_in.configure(disabledforeground="#a3a3a3")
        self.demanda_prev_in.configure(foreground="#000000")
        self.demanda_prev_in.configure(highlightbackground="#d9d9d9")
        self.demanda_prev_in.configure(highlightcolor="black")
        self.demanda_prev_in.configure(justify='left')
        self.demanda_prev_in.configure(text='''Incluir''')
        self.demanda_prev_in.configure(
            variable=generator_support.demanda_prev_in)

        self.from_demanda_prevista = DateEntry(
            self.labelframe_demanda_prevista)
        self.from_demanda_prevista.place(
            relx=0.204, rely=0.308, height=30, relwidth=0.324, bordermode='ignore')
        self.from_demanda_prevista.configure(background="white")
        self.from_demanda_prevista.configure(disabledforeground="#a3a3a3")
        self.from_demanda_prevista.configure(font="TkFixedFont")
        self.from_demanda_prevista.configure(foreground="#000000")

        self.to_demanda_prevista = DateEntry(self.labelframe_demanda_prevista)
        self.to_demanda_prevista.place(
            relx=0.574, rely=0.308, height=30, relwidth=0.324, bordermode='ignore')
        self.to_demanda_prevista.configure(background="white")
        self.to_demanda_prevista.configure(disabledforeground="#a3a3a3")
        self.to_demanda_prevista.configure(font="TkFixedFont")
        self.to_demanda_prevista.configure(foreground="#000000")

        self.steps_demanda_prev = IntEntry(self.labelframe_demanda_prevista)
        self.steps_demanda_prev.place(
            relx=0.917, rely=0.308, height=30, relwidth=0.063, bordermode='ignore')
        self.steps_demanda_prev.configure(background="white")
        self.steps_demanda_prev.configure(font="TkFixedFont")
        self.steps_demanda_prev.configure(foreground="#000000")


        self.labelframe_sol_real = tk.LabelFrame(top)
        self.labelframe_sol_real.place(
            relx=0.04, rely=0.336, height=70, relwidth=0.45)
        self.labelframe_sol_real.configure(relief='groove')
        self.labelframe_sol_real.configure(foreground="black")
        self.labelframe_sol_real.configure(
            text='''Generación Solar Tiempo Real''')
        self.labelframe_sol_real.configure(background="#d9d9d9")
        self.labelframe_sol_real.configure(highlightbackground="#d9d9d9")
        self.labelframe_sol_real.configure(highlightcolor="black")

        self.solar_real_in = tk.Checkbutton(self.labelframe_sol_real)
        self.solar_real_in.place(
            relx=0.056, rely=0.4, relheight=0.338, relwidth=0.113, bordermode='ignore')
        self.solar_real_in.configure(activebackground="#ececec")
        self.solar_real_in.configure(activeforeground="#000000")
        self.solar_real_in.configure(background="#d9d9d9")
        self.solar_real_in.configure(disabledforeground="#a3a3a3")
        self.solar_real_in.configure(foreground="#000000")
        self.solar_real_in.configure(highlightbackground="#d9d9d9")
        self.solar_real_in.configure(highlightcolor="black")
        self.solar_real_in.configure(justify='left')
        self.solar_real_in.configure(text='''Incluir''')
        self.solar_real_in.configure(variable=generator_support.solar_real_in)

        self.from_gen_solar_real = DateEntry(self.labelframe_sol_real)
        self.from_gen_solar_real.place(
            relx=0.204, rely=0.308, height=30, relwidth=0.324, bordermode='ignore')
        self.from_gen_solar_real.configure(background="white")
        self.from_gen_solar_real.configure(disabledforeground="#a3a3a3")
        self.from_gen_solar_real.configure(font="TkFixedFont")
        self.from_gen_solar_real.configure(foreground="#000000")

        self.to_gen_solar_real = DateEntry(self.labelframe_sol_real)
        self.to_gen_solar_real.place(
            relx=0.574, rely=0.308, height=30, relwidth=0.324, bordermode='ignore')
        self.to_gen_solar_real.configure(background="white")
        self.to_gen_solar_real.configure(disabledforeground="#a3a3a3")
        self.to_gen_solar_real.configure(font="TkFixedFont")
        self.to_gen_solar_real.configure(foreground="#000000")

        self.steps_gen_solar_real = IntEntry(self.labelframe_sol_real)
        self.steps_gen_solar_real.place(
            relx=0.917, rely=0.308, height=30, relwidth=0.063, bordermode='ignore')
        self.steps_gen_solar_real.configure(background="white")
        self.steps_gen_solar_real.configure(font="TkFixedFont")

        self.labelframe_sol_prevista = tk.LabelFrame(top)
        self.labelframe_sol_prevista.place(
            relx=0.51, rely=0.336, height=70, relwidth=0.45)
        self.labelframe_sol_prevista.configure(relief='groove')
        self.labelframe_sol_prevista.configure(foreground="black")
        self.labelframe_sol_prevista.configure(
            text='''Generación Solar Prevista''')
        self.labelframe_sol_prevista.configure(background="#d9d9d9")
        self.labelframe_sol_prevista.configure(highlightbackground="#d9d9d9")
        self.labelframe_sol_prevista.configure(highlightcolor="black")

        self.solar_prev_in = tk.Checkbutton(self.labelframe_sol_prevista)
        self.solar_prev_in.place(
            relx=0.056, rely=0.4, relheight=0.338, relwidth=0.113, bordermode='ignore')
        self.solar_prev_in.configure(activebackground="#ececec")
        self.solar_prev_in.configure(activeforeground="#000000")
        self.solar_prev_in.configure(background="#d9d9d9")
        self.solar_prev_in.configure(disabledforeground="#a3a3a3")
        self.solar_prev_in.configure(foreground="#000000")
        self.solar_prev_in.configure(highlightbackground="#d9d9d9")
        self.solar_prev_in.configure(highlightcolor="black")
        self.solar_prev_in.configure(justify='left')
        self.solar_prev_in.configure(text='''Incluir''')
        self.solar_prev_in.configure(variable=generator_support.solar_prev_in)

        self.from_gen_solar_prevista = DateEntry(self.labelframe_sol_prevista)
        self.from_gen_solar_prevista.place(
            relx=0.204, rely=0.308, height=30, relwidth=0.324, bordermode='ignore')
        self.from_gen_solar_prevista.configure(background="white")
        self.from_gen_solar_prevista.configure(disabledforeground="#a3a3a3")
        self.from_gen_solar_prevista.configure(font="TkFixedFont")
        self.from_gen_solar_prevista.configure(foreground="#000000")

        self.to_gen_solar_prevista = DateEntry(self.labelframe_sol_prevista)
        self.to_gen_solar_prevista.place(
            relx=0.574, rely=0.308, height=30, relwidth=0.324, bordermode='ignore')
        self.to_gen_solar_prevista.configure(background="white")
        self.to_gen_solar_prevista.configure(disabledforeground="#a3a3a3")
        self.to_gen_solar_prevista.configure(font="TkFixedFont")
        self.to_gen_solar_prevista.configure(foreground="#000000")

        self.steps_gen_solar_prev = IntEntry(self.labelframe_sol_prevista)
        self.steps_gen_solar_prev.place(
            relx=0.917, rely=0.308, height=30, relwidth=0.063, bordermode='ignore')
        self.steps_gen_solar_prev.configure(background="white")
        self.steps_gen_solar_prev.configure(font="TkFixedFont")


        self.labelframe_eol_real = tk.LabelFrame(top)
        self.labelframe_eol_real.place(
            relx=0.04, rely=0.492, height=70, relwidth=0.45)
        self.labelframe_eol_real.configure(relief='groove')
        self.labelframe_eol_real.configure(foreground="black")
        self.labelframe_eol_real.configure(
            text='''Generación Eólica Tiempo Real''')
        self.labelframe_eol_real.configure(background="#d9d9d9")
        self.labelframe_eol_real.configure(highlightbackground="#d9d9d9")
        self.labelframe_eol_real.configure(highlightcolor="black")

        self.eol_real_in = tk.Checkbutton(self.labelframe_eol_real)
        self.eol_real_in.place(
            relx=0.056, rely=0.4, relheight=0.338, relwidth=0.113, bordermode='ignore')
        self.eol_real_in.configure(activebackground="#ececec")
        self.eol_real_in.configure(activeforeground="#000000")
        self.eol_real_in.configure(background="#d9d9d9")
        self.eol_real_in.configure(disabledforeground="#a3a3a3")
        self.eol_real_in.configure(foreground="#000000")
        self.eol_real_in.configure(highlightbackground="#d9d9d9")
        self.eol_real_in.configure(highlightcolor="black")
        self.eol_real_in.configure(justify='left')
        self.eol_real_in.configure(text='''Incluir''')
        self.eol_real_in.configure(variable=generator_support.eol_real_in)

        self.from_gen_eol_real = DateEntry(self.labelframe_eol_real)
        self.from_gen_eol_real.place(
            relx=0.204, rely=0.308, height=30, relwidth=0.324, bordermode='ignore')
        self.from_gen_eol_real.configure(background="white")
        self.from_gen_eol_real.configure(disabledforeground="#a3a3a3")
        self.from_gen_eol_real.configure(font="TkFixedFont")
        self.from_gen_eol_real.configure(foreground="#000000")

        self.to_gen_eol_real = DateEntry(self.labelframe_eol_real)
        self.to_gen_eol_real.place(
            relx=0.574, rely=0.308, height=30, relwidth=0.324, bordermode='ignore')
        self.to_gen_eol_real.configure(background="white")
        self.to_gen_eol_real.configure(disabledforeground="#a3a3a3")
        self.to_gen_eol_real.configure(font="TkFixedFont")
        self.to_gen_eol_real.configure(foreground="#000000")

        self.steps_gen_eol_real = IntEntry(self.labelframe_eol_real)
        self.steps_gen_eol_real.place(
            relx=0.917, rely=0.308, height=30, relwidth=0.063, bordermode='ignore')
        self.steps_gen_eol_real.configure(background="white")
        self.steps_gen_eol_real.configure(font="TkFixedFont")

        self.labelframe_eol_prevista = tk.LabelFrame(top)
        self.labelframe_eol_prevista.place(
            relx=0.51, rely=0.492, height=70, relwidth=0.45)
        self.labelframe_eol_prevista.configure(relief='groove')
        self.labelframe_eol_prevista.configure(foreground="black")
        self.labelframe_eol_prevista.configure(
            text='''Generación Eólica Prevista''')
        self.labelframe_eol_prevista.configure(background="#d9d9d9")
        self.labelframe_eol_prevista.configure(highlightbackground="#d9d9d9")
        self.labelframe_eol_prevista.configure(highlightcolor="black")

        self.eol_prev_in = tk.Checkbutton(self.labelframe_eol_prevista)
        self.eol_prev_in.place(
            relx=0.056, rely=0.4, relheight=0.338, relwidth=0.113, bordermode='ignore')
        self.eol_prev_in.configure(activebackground="#ececec")
        self.eol_prev_in.configure(activeforeground="#000000")
        self.eol_prev_in.configure(background="#d9d9d9")
        self.eol_prev_in.configure(disabledforeground="#a3a3a3")
        self.eol_prev_in.configure(foreground="#000000")
        self.eol_prev_in.configure(highlightbackground="#d9d9d9")
        self.eol_prev_in.configure(highlightcolor="black")
        self.eol_prev_in.configure(justify='left')
        self.eol_prev_in.configure(text='''Incluir''')
        self.eol_prev_in.configure(variable=generator_support.eol_prev_in)
        self.eol_prev_in.configure(DISABLED)

        self.from_gen_eol_prevista = DateEntry(self.labelframe_eol_prevista)
        self.from_gen_eol_prevista.place(
            relx=0.204, rely=0.308, height=30, relwidth=0.324, bordermode='ignore')
        self.from_gen_eol_prevista.configure(background="white")
        self.from_gen_eol_prevista.configure(disabledforeground="#a3a3a3")
        self.from_gen_eol_prevista.configure(font="TkFixedFont")
        self.from_gen_eol_prevista.configure(foreground="#000000")

        self.to_gen_eol_prevista = DateEntry(self.labelframe_eol_prevista)
        self.to_gen_eol_prevista.place(
            relx=0.574, rely=0.308, height=30, relwidth=0.324, bordermode='ignore')
        self.to_gen_eol_prevista.configure(background="white")
        self.to_gen_eol_prevista.configure(disabledforeground="#a3a3a3")
        self.to_gen_eol_prevista.configure(font="TkFixedFont")
        self.to_gen_eol_prevista.configure(foreground="#000000")

        self.steps_gen_eol_prevista = IntEntry(self.labelframe_eol_prevista)
        self.steps_gen_eol_prevista.place(
            relx=0.917, rely=0.308, height=30, relwidth=0.063, bordermode='ignore')
        self.steps_gen_eol_prevista.configure(background="white")
        self.steps_gen_eol_prevista.configure(font="TkFixedFont")

        self.labelframe_gas_natural = tk.LabelFrame(top)
        self.labelframe_gas_natural.place(
            relx=0.04, rely=0.648, height=70, relwidth=0.45)
        self.labelframe_gas_natural.configure(relief='groove')
        self.labelframe_gas_natural.configure(foreground="black")
        self.labelframe_gas_natural.configure(text='''Precio Gas Natural''')
        self.labelframe_gas_natural.configure(background="#d9d9d9")
        self.labelframe_gas_natural.configure(highlightbackground="#d9d9d9")
        self.labelframe_gas_natural.configure(highlightcolor="black")

        self.gas_in = tk.Checkbutton(self.labelframe_gas_natural)
        self.gas_in.place(relx=0.056, rely=0.4, relheight=0.338,
                          relwidth=0.113, bordermode='ignore')
        self.gas_in.configure(activebackground="#ececec")
        self.gas_in.configure(activeforeground="#000000")
        self.gas_in.configure(background="#d9d9d9")
        self.gas_in.configure(disabledforeground="#a3a3a3")
        self.gas_in.configure(foreground="#000000")
        self.gas_in.configure(highlightbackground="#d9d9d9")
        self.gas_in.configure(highlightcolor="black")
        self.gas_in.configure(justify='left')
        self.gas_in.configure(text='''Incluir''')
        self.gas_in.configure(variable=generator_support.gas_in)

        self.from_gas = DateEntry(self.labelframe_gas_natural)
        self.from_gas.place(relx=0.204, rely=0.308, height=30,
                            relwidth=0.324, bordermode='ignore')
        self.from_gas.configure(background="white")
        self.from_gas.configure(disabledforeground="#a3a3a3")
        self.from_gas.configure(font="TkFixedFont")
        self.from_gas.configure(foreground="#000000")

        self.to_gas = DateEntry(self.labelframe_gas_natural)
        self.to_gas.place(relx=0.574, rely=0.308, height=30,
                          relwidth=0.324, bordermode='ignore')
        self.to_gas.configure(background="white")
        self.to_gas.configure(disabledforeground="#a3a3a3")
        self.to_gas.configure(font="TkFixedFont")
        self.to_gas.configure(foreground="#000000")

        self.labelframe_co2 = tk.LabelFrame(top)
        self.labelframe_co2.place(
            relx=0.51, rely=0.648, height=70, relwidth=0.45)
        self.labelframe_co2.configure(relief='groove')
        self.labelframe_co2.configure(foreground="black")
        self.labelframe_co2.configure(text='''Precio CO2''')
        self.labelframe_co2.configure(background="#d9d9d9")
        self.labelframe_co2.configure(highlightbackground="#d9d9d9")
        self.labelframe_co2.configure(highlightcolor="black")

        self.co2_in = tk.Checkbutton(self.labelframe_co2)
        self.co2_in.place(relx=0.056, rely=0.4, relheight=0.338,
                          relwidth=0.113, bordermode='ignore')
        self.co2_in.configure(activebackground="#ececec")
        self.co2_in.configure(activeforeground="#000000")
        self.co2_in.configure(background="#d9d9d9")
        self.co2_in.configure(disabledforeground="#a3a3a3")
        self.co2_in.configure(foreground="#000000")
        self.co2_in.configure(highlightbackground="#d9d9d9")
        self.co2_in.configure(highlightcolor="black")
        self.co2_in.configure(justify='left')
        self.co2_in.configure(text='''Incluir''')
        self.co2_in.configure(variable=generator_support.co2_in)

        self.from_co2 = DateEntry(self.labelframe_co2)
        self.from_co2.place(relx=0.204, rely=0.308, height=30,
                            relwidth=0.324, bordermode='ignore')
        self.from_co2.configure(background="white")
        self.from_co2.configure(disabledforeground="#a3a3a3")
        self.from_co2.configure(font="TkFixedFont")
        self.from_co2.configure(foreground="#000000")

        self.to_co2 = DateEntry(self.labelframe_co2)
        self.to_co2.place(relx=0.574, rely=0.308, height=30,
                          relwidth=0.324, bordermode='ignore')
        self.to_co2.configure(background="white")
        self.to_co2.configure(disabledforeground="#a3a3a3")
        self.to_co2.configure(font="TkFixedFont")
        self.to_co2.configure(foreground="#000000")

        self.generator = tk.Button(top)
        self.generator.place(relx=0.817, rely=0.850, height=24, width=58)
        self.generator.configure(activebackground="#ececec")
        self.generator.configure(activeforeground="#000000")
        self.generator.configure(background="#d9d9d9")
        self.generator.configure(disabledforeground="#a3a3a3")
        self.generator.configure(foreground="#000000")
        self.generator.configure(highlightbackground="#d9d9d9")
        self.generator.configure(highlightcolor="black")
        self.generator.configure(pady="0")
        self.generator.configure(text='''Generator''')
        self.generator.configure(command=self.generate)


if __name__ == '__main__':
    vp_start_gui()
