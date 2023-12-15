import tkinter as tk
from tkinter import filedialog

version = "2.1.0"
date = "(2023-Jun-09)"


from .gui import App

# calls the GUI?
root = tk.Tk()
app = App(root)
root.resizable(False,False)
root.mainloop()

# Sets the data directory
dataFolder,graphFolder,resultsFolder = app.getFolders()
#Gets the results.xslx name if applicatble
resultsName,channel,voltage = app.getEntries()
# Gets the correction option from the gui
isVehicleCorrected = app.getCorrection()
# Gets from the GUI if vehicles have to be drawn on the compound graphs
drawVehicleOnGraph = app.getVehicleDraw()
# Retrieves the way error bars are presented (SEM or STDDev)
stats = app.getAnalysisType()

# later get theses from the GUI
tableTitle = (channel+" current density at "+voltage+".")



if isVehicleCorrected :
    vehicleData = "Uncorrected_density_mean"
    blockData = "Corrected_density_mean"
    blockColName = "Corrected current density"
    bslColName = "Normalized current Density"
    pvalData = "Corrected_density"
    dataList = "DensityList"
    corrPrint = "-> Analyzing data with corrected values"


else :
    vehicleData = "corrVal_mean"
    blockData = "Uncorrected_density_mean"
    blockColName = "Normalized current density"
    bslColName = "Vehicle current density"
    pvalData = "Uncorrected_density"
    dataList = "RawDensityList"
    corrPrint = "-> Analyzing data with uncorrected values"

if stats == "SEM" :
    errorBarType = "SEM"
else :
    errorBarType = "StdDev"
