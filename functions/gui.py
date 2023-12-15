# This GUI was built with the help of ChatGPT
import os
import tkinter as tk
from tkinter import filedialog
import pandas as pd
import subprocess
import xlsxwriter
import sys

from . import constants as c


if __name__ == "__main__" :
    os.chdir("../")

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def shortPath (path) :
    shortPath = "... "+path[-20:]
    return shortPath


class App:
    def __init__(self, master):
        self.master = master
        master.title("Patchliner analysis software,the PYLiner")
        master.geometry("700x500")

        # Software title
        self.required_label = tk.Label(master, text= "Patchliner analysis software for IPST", font = "Helvetica 16 bold ", justify="center")
        self.required_label.place(x=150,y=10)

        # Add image to the GUI
        image_path = "images/patchliner.png"
        try :
            self.img = tk.PhotoImage(file=resource_path(image_path))
        except :
            self.img = tk.PhotoImage(file=resource_path("patchliner.png"))
            
        self.image_label = tk.Label(master, image=self.img)
        self.image_label.place(x=435, y=100)

        # Version number
        self.required_label = tk.Label(master, text= "Version "+ c.version+ " - " + c.date, font = "Helvetica 10")
        self.required_label.place(x=510,y=475)  

        reqXpos = 50
        reqYpos = 50

        # Required options label
        self.required_label = tk.Label(master, text= "Required settings", font = "Helvetica 10 bold underline")
        self.required_label.place(x=50,y=reqYpos)

        # Widget to selected whether to present data using SEM or STDDev
        self.analysis_label = tk.Label(master, text="How to display error bars")
        self.analysis_label.place(x=50, y=reqYpos+30)
        self.analysis_type = tk.StringVar(value="SEM")
        self.sem_radiobutton = tk.Radiobutton(master, text="SEM", variable=self.analysis_type, value="SEM")
        self.sem_radiobutton.place(x=200, y=reqYpos+30)
        self.stddev_radiobutton = tk.Radiobutton(master, text="Standard Deviation", variable=self.analysis_type, value="STDDEV")
        self.stddev_radiobutton.place(x=250, y=reqYpos+30)

        # Widget to select for corrected or uncorrected data
        self.correction_label = tk.Label(master, text="Select the type of analysis")
        self.correction_label.place(x=50, y=reqYpos+75)
        self.correction_type = tk.BooleanVar(value=False)
        self.uncorrected_radio = tk.Radiobutton(master, text="Uncorrected", variable=self.correction_type, value=False)
        self.corrected_radio = tk.Radiobutton(master, text="Corrected", variable=self.correction_type, value=True)
        self.uncorrected_radio.place(x=200, y=reqYpos+75)
        self.corrected_radio.place(x=300, y=reqYpos+75)

        # Widget to hide or show vehicle curves in the graph
        self.graphVehicleLabel = tk.Label(master, text="Show vehicle trend on \n the compound graph?")
        self.graphVehicleLabel.place(x=50, y=reqYpos+120)
        self.drawVehicle = tk.BooleanVar(value=False)
        self.drawVehYes_radiobutton = tk.Radiobutton(master, text="Yes", variable=self.drawVehicle, value=True)
        self.drawVehYes_radiobutton.place(x=200, y=reqYpos+120)
        self.drawVehNo_radiobutton = tk.Radiobutton(master, text="No", variable=self.drawVehicle, value=False)
        self.drawVehNo_radiobutton.place(x=250, y=reqYpos+120)

        # Optional settings label
        self.optional_label = tk.Label(master, text= "Optional settings", font = "Helvetica 10 bold underline")
        self.optional_label.place(x=50,y=reqYpos+170)

        # optional settings boxes coordinates
        optYstart = reqYpos+205
        spacing = 40
        boxOffset = 7
        boxWidth = 20

        # Widget to change the datafolder if data is stored somewhere else
        self.folder_var = tk.StringVar(value=os.path.join(os.getcwd(),"data"))
        self.folder_label = tk.Label(master, text="Change data folder ",justify="left")
        self.folder_label.place(x=50, y=optYstart+(spacing*0)+6)
        self.folder_button = tk.Button(master, text="Select data folder", command=self.select_dataFolder, width=boxWidth,justify="left")
        self.folder_button.place(x=250, y=optYstart+(spacing*0)+boxOffset)

        # Widget to change where the graphs are saved
        self.graphFolder_var = tk.StringVar(value=os.path.join(os.getcwd(),"graphs"))
        self.graphFolder_label = tk.Label(master, text="Change the folder where\nthe graphs are generated",justify="left")
        self.graphFolder_label.place(x=50, y=optYstart+(spacing*1))
        self.graphFolder_button = tk.Button(master, text="Select graph folder", command=self.select_graphFolder, width=boxWidth,justify="left")
        self.graphFolder_button.place(x=250, y=optYstart+(spacing*1)+boxOffset)

        # Widget to change where the table values are saved
        self.tableResults_var = tk.StringVar(value=os.getcwd())
        self.tableResults_label = tk.Label(master, text="Change where the table\nresults are saved",justify="left")
        self.tableResults_label.place(x=50, y=optYstart+(spacing*2))
        self.tableResults_button = tk.Button(master, text="Select results folder", command=self.select_resultsFolder, width=boxWidth,justify="left")
        self.tableResults_button.place(x=250, y=optYstart+(spacing*2)+boxOffset)

        # Widget to edit vehicles
        self.edit_label = tk.Label(master, text="Assign specific vehicle values \nto specific concentrations ", justify="left")
        self.edit_label.place(x=50, y=optYstart+(spacing*3))
        self.edit_button = tk.Button(master, text="Assign", command=self.edit_excel, width=20)
        self.edit_button.place(x=250, y=optYstart+(spacing*3)+2)

        # Widget to rename the results.xslx file
        defaultResults = "Results"
        self.resultsName_var = tk.StringVar(value=defaultResults)
        self.resultsName_label = tk.Label(master, text="Change 'Results.xslx' file name",justify="left")
        self.resultsName_label.place(x=50, y=optYstart+(spacing*4)+5)
        self.resultsName_field = tk.Entry(master,textvariable=self.resultsName_var,justify="center", width = boxWidth+4)
        self.resultsName_field.place(x=250, y=optYstart+(spacing*4)+boxOffset)
   
        # Widget to change the channel type
        self.channel_var = tk.StringVar(value="hERG")
        self.channel_label = tk.Label(master, text="Enter screened channel",justify="left")
        self.channel_label.place(x=50, y=optYstart+(spacing*4.5)+5)
        self.channel_field = tk.Entry(master,textvariable=self.channel_var,justify="center", width = boxWidth+4)
        self.channel_field.place(x=250, y=optYstart+(spacing*4.5)+boxOffset)

        # Widget to change the channel type
        self.voltage_var = tk.StringVar(value="+20 mV")
        self.voltage_label = tk.Label(master, text="Enter analysis voltage",justify="left")
        self.voltage_label.place(x=50, y=optYstart+(spacing*5)+6)
        self.voltage_field = tk.Entry(master,textvariable=self.voltage_var,justify="center", width = boxWidth+4)
        self.voltage_field.place(x=250, y=optYstart+(spacing*5)+boxOffset)


        # Run button
        self.run_button = tk.Button(master, text="Run script", command=self.run_script, width=20, height=2, font = "Helvetica 12 bold ")
        self.run_button.place(x=450, y=395)

        # Stops the script when closing the window
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

    def select_dataFolder(self):
        emptyFolder = True

        # Prompts the user to select a folder again if the selected one does not contain any .csv file
        while emptyFolder :
            folder_selected = filedialog.askdirectory()

            for fname in os.listdir(folder_selected):
                if fname.endswith(".csv") :
                    emptyFolder = False
                
            if emptyFolder :
                print("Selected folder does not contain any .csv file, chose another folder or add data in this folder")

        if folder_selected:
            self.folder_var.set(folder_selected)
            self.folder_button.config(text = shortPath(folder_selected) )

    def select_graphFolder(self):
        graphFolder = filedialog.askdirectory()
        if graphFolder:
            self.graphFolder_var.set(graphFolder)
            self.graphFolder_button.config(text = shortPath(graphFolder))


    def select_resultsFolder(self):
        resultsFolder = filedialog.askdirectory()
        if resultsFolder:
            self.tableResults_var.set(resultsFolder)
            self.tableResults_button.config(text = shortPath(resultsFolder))

    def edit_excel(self):

        def configCreator(file_path) :
            # Create a new XLSX file
            workbook = xlsxwriter.Workbook(file_path)
            # Add a worksheet to the workbook
            worksheet = workbook.add_worksheet()
            # Write data to the columns
            column_data = ['Compound', 'Concentration', 'conc_order', 'vehicle_equivalent']
            # Write the column headers
            for col_num, data in enumerate(column_data):
                worksheet.write(0, col_num, data)
            # Auto-adjust the column width based on content
            for col_num, data in enumerate(column_data):
                max_length = len(column_data[col_num])
                worksheet.set_column(col_num, col_num, max_length+2)  # Add some padding

            # Close the workbook
            workbook.close()
            return()
                
        def excelOpener(file_path) :
            subprocess.Popen(['start', '', file_path], shell=True)
            return()

        path = "config/"
        file_path = path+"/vehicleConfig.xlsx"  # replace with your file path               

        if os.path.exists(path) :
            if os.path.isfile(file_path):
                excelOpener(file_path)
            else :
                configCreator(file_path)
                excelOpener(file_path) 
        else:
            os.mkdir(path)   
            configCreator(file_path)
            excelOpener(file_path)


    # Switch gets SEM or STDDev
    def getAnalysisType(self) :
        stat = self.analysis_type.get()
        return stat

    # Gets the type of correction
    def getCorrection(self) :
        corr = self.correction_type.get()
        return corr

    # Gets the type of correction
    def getVehicleDraw(self) :
        vehicleDraw = self.drawVehicle.get()
        return vehicleDraw

    def getFolders(self) :
        dataFolder = self.folder_var.get()
        graphFolder = self.graphFolder_var.get()
        resultsFolder = self.tableResults_var.get()
        return dataFolder,graphFolder,resultsFolder
    
    def getEntries(self) :
        resultsName = self.resultsName_var.get()
        channel = self.channel_var.get()
        voltage = self.voltage_var.get()
        return resultsName,channel,voltage
    
    def run_script(self):
        self.master.destroy()  # close the GUI
        #print("Script executed successfully")

    def on_close(self):
        self.master.destroy()
        # ... any other cleanup code here ...
        sys.exit()
