# Made by T.Duval
# 2023

#import modules
import pandas as pd
import os
import glob
import math
import xlsxwriter

#import custom functions

from functions import constants as c
from functions.tables import tableFunctions as tf
from functions.graphs import graphFunctions as gf
from functions.utility import utilities as u

# pandas options
pd.options.mode.chained_assignment = None
import warnings
warnings.filterwarnings("ignore", category=FutureWarning) 

#Used for the initial message in the terminal
term_size = os.get_terminal_size()

print('=' * term_size.columns)
print("Patchliner analysis script for IPST \nVersion",c.version,c.date,"\n")
print('=' * term_size.columns)
# Stating used parameters
print(c.corrPrint)
print("-> Analyzing data using",c.errorBarType,"for error bars")

print("\nAnalyzing... ")
# 1 - Deletes the graphs of the graph folder
graphDir = c.graphFolder


# Creates the graph folder if it's missing, and if its the default "graph/" folder
defaultGraphFolder = os.path.join(os.getcwd(),"graphs")

if graphDir == defaultGraphFolder :
    try :
        os.mkdir(defaultGraphFolder)
    except :
        pass

    # Deletes previously generated graphs
    filelist = [ f for f in os.listdir(defaultGraphFolder) if f.endswith(".png") ]
    for f in filelist:
        # does not delete .gitignore in the folder
        if "gitignore" in f :
            continue
        os.remove(os.path.join(defaultGraphFolder, f))

# 2 - Gets the configuration for the vehicleConfig file
if os.path.exists("config/vehicleConfig.xlsx") :
    configDict = u.vehicleCorrect(pd.read_excel ("config/vehicleConfig.xlsx"))
else :
    configDict = {}

# 3 - merges every csv data file from the data folder into one, using the custom "dataMerger function for functions/utilites.py"
masterDf = u.dataMerger(c.dataFolder)

# 4 - Edits the merged dataframe to a usable format for pandas

#Fills "N/A" values in the compound row with the previous compound
masterDf.fillna(method='ffill', inplace=True)
masterDf["Compound"] = masterDf["Compound"].str.upper()
# creates a "fake" concentration for the baseline value set at 0.001 pM
masterDf.loc[masterDf['block'] == 0, 'conc'] = 1E-15
#Creates a temporary label for concentration labeling for each compound in the next step
masterDf["concX"] = masterDf["Compound"]+"_"+masterDf["conc"].astype("str")
# Creates an empty dataframe for the label operations
labeledDf = pd.DataFrame()
# Map the conc# to each label for each concentration
for compound in masterDf["Compound"].drop_duplicates() :
    # Uses the concLabelMap function written above
    df = tf.concLabelMap(masterDf[masterDf["Compound"].str.contains(compound)])
    # Concatenates with the merged labeled dataframe created earlier
    labeledDf = pd.concat([df,labeledDf])



if "VEHICLE" not in labeledDf["Compound"].tolist() :
    print("Missing vehicle data, generating dummy values with no block")
    concNum = labeledDf["concLabel"].drop_duplicates().sort_values()
    dumVehicleDf = tf.vehicleDummyTable(labeledDf.columns,concNum)
    labeledDf = pd.concat([labeledDf,dumVehicleDf])

# Maps concentration label by the "right" vehicle label if the compound is analyzed in different batches
labeledDf['concVLabel'] = (labeledDf['concLabelTemp'].map(configDict).fillna(labeledDf['concLabel']))

# Message to indicate progress
print("VEHICLE")
# Data operations for the vehicle
vehicleDf,nothing = tf.dataOrganizer(labeledDf[labeledDf["Compound"].str.contains("VEHICLE|VEHICULE")],0)


# Graph generation for the vehicle
gf.vehicleCurveFit(vehicleDf)
# Creates a dictionnary of rundown correction for each concentration
runDownDict = {x:y for x,y in zip(vehicleDf["concLabel"],1-vehicleDf["Corrected_density_mean"])}

# Creates a separate dataframe for the remaining non-vehicle data : arg1 = dataframe, arg2 = rundown dict
remainDf = labeledDf[~labeledDf["Compound"].str.contains("VEHICLE|VEHICULE")].sort_values(by=["Compound","concLabel"])

#Empty dataframe placeholders
emptyRow = pd.DataFrame([[]])
graphpadDf = pd.DataFrame()
tableListDf = pd.DataFrame()
ic50Df = pd.DataFrame()
ic50Dict = {}
# Used to assign the correct number to the table name
order = 0

#---- Loop to analyse every compound----#

for compound in remainDf["Compound"].drop_duplicates() :
    # Shows which compound is being analysed
    order = order+1

    dfTemp, inhibDf= tf.dataOrganizer(remainDf[remainDf["Compound"].str.contains(compound)],runDownDict)

    if dfTemp.empty :
        # Ignoring analysis for n = 1 to prevent pvalues errors
        print(compound + " : doesn't have enough datapoints for analysis (n=1), skipping analysis")
        continue
    else :
        print(compound)

    # Generates data for graphpad analysis
    graphpadDf = pd.concat([graphpadDf,tf.graphPadOrganizer(dfTemp),emptyRow])

    #Generates graphs using the curveFit function
    realIC50 = gf.curveFit(dfTemp)

    if not realIC50 :
        print("Skipping the analysis for",compound)
        continue

    # Finds the max concentrations to set a value higher than the max tested concentration
    # if the IC50 can not be determined with the current dataset
    maxConc = dfTemp["Concentration (nM)"].max()

    realIC50 = round(realIC50,1)
    if math.isnan(realIC50) :
        realIC50 = ("> " + str(maxConc))
    elif realIC50 > maxConc :
        realIC50 = ("> " + str(maxConc))

    # Appends inhibition values to the IC50 dataframe
    ic50Df = pd.concat([ic50Df,inhibDf])
    # Adds the IC50 value of the compound into the dictionnary for it (ic50Dict)
    ic50Dict[compound] = realIC50
    # Exporting data for tables
    tableHeader = "Table "+str(order)+". Effects of "+compound+" on " + c.tableTitle
    tableDf, header = tf.tableOrganizer(dfTemp)
    # Generates the title for each table in the table_data.csv
    tableTitle=pd.DataFrame(columns = header, index=range(2))
    tableTitle["Compound"] = [tableHeader,""]
    tableTitle.loc[2] = header
    tableTitleConcat = pd.concat([tableTitle,tableDf])

    # Appends table data to the existing table_data to combine every compounds in one file
    tableListDf = pd.concat([tableListDf,tableTitleConcat,emptyRow])


# 8 - Calls the ic50 sorting function to generates a correctly formatted ic50 dataframe
ic50Df = tf.IC50sorter(ic50Df,ic50Dict)  

# 9 - Adds the selected dataframes into the Results.xslx
u.excelWriter([tableListDf,graphpadDf,ic50Df],["Table Results","Graphpad Results","IC50"])

# creates a file indication the version of the patchliner script for reproductibility purposes
for folder in [c.resultsFolder,graphDir] :
    with open(folder+"/version.txt", 'w') as f:
        f.write('Data analyzed with version '+c.version+" "+c.date+" of the python patchliner script for IPST")

print("... Done !",str(order),"compounds analyzed.")
k = input ("Press any key to close")
