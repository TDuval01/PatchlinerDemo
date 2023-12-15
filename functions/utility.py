import xlsxwriter
import pandas as pd
import os
import sys
from . import constants as c


# ---Creates a Pandas Excel Writer ----#s
#inputs has to be a list of dataframes and a list of names for the tabs
class utilities :
    # writes dataframes into an excel files with tabs
    def excelWriter (dfList,namesList) :
        writer = pd.ExcelWriter(c.resultsFolder+"/"+c.resultsName+'.xlsx', engine='xlsxwriter')
        for finalDf,name in zip(dfList,namesList) :

            finalDf.to_excel(writer, sheet_name=name, startrow=1, header=False, index=False)

            # Get the xlsxwriter workbook and worksheet objects.
            workbook = writer.book
            # new sheet name
            worksheet = writer.sheets[name]

            # Get the dimensions of the dataframe.
            (max_row, max_col) = finalDf.shape

            # Create a list of column headers, to use in add_table().
            column_settings = [{'header': column} for column in finalDf.columns]

            # Add the Excel table structure. Pandas will add the data.
            if name != "Table Results" :
                worksheet.add_table(0, 0, max_row, max_col - 1, {'columns': column_settings})

            # Make the columns wider for clarity.
            worksheet.set_column(0, max_col - 1, 20)
        writer.close()
        return()

    # retrieves the configuration for the corresponding vehicle if a "non traditionnal" run is done
    def vehicleCorrect (df) :
        concOrder = [y.upper()+"_conc"+str(x) for x,y in zip(df["conc_order"],df["Compound"])]
        # identifies the correct vehicle correction to use for each specific concentration
        corrEq = ["conc"+str(x) for x in df["vehicle_equivalent"]]
        # returns a dictionnary for mapping the correction to the correct concentration
        return {x:y for x,y in zip(concOrder,corrEq)}


    # Merges every csv files from the specified folder into a single dataframe
    def dataMerger (dataFolder) :

        def fileIntegrity (df) :
            reqCol = ["Info","Cells","Compound","sweep","conc","block"]
            fileOK = []
            wrongCol = []
            checkVal =  True
            for col in reqCol :
                if col.upper() not in df.columns.str.upper() :
                    fileOK.append(False)
                    wrongCol.append(col)
            if False in fileOK :
                checkVal = False

            return(checkVal,wrongCol)

        #Creates an empty "master" dataframe for appending every CSV
        mergedDf = pd.DataFrame()
        #Iterates throught every.csv files in the data folder
        emptyFolder = True
        if not os.path.exists(dataFolder) :
            print("*** ERROR ("+dataFolder+") does not exist, make sure to select a valid data folder")
            k = input ("Press any key to close")
            sys.exit()
        for file in os.listdir(dataFolder):
            # opens only csv files
            if ".csv" in file :
                emptyFolder = False
                # Reads opens the csv file in pandas
                fileDf = pd.read_csv(dataFolder+"/"+file, skiprows=2)
                fileCheck,col = fileIntegrity(fileDf)
                if not fileCheck :
                    print("Missing column(s) "+"'"+",".join(col)+"'","for '"+file+"' , skipping this file to prevent errors in analysis")
                    continue
                fileDf = fileDf[fileDf["block"].notna()]
                # Merges the opened file into the master dataframe
                mergedDf = pd.concat([fileDf,mergedDf])
            elif ".gitignore" in file :
                continue
            else :
                print("Invalid file format :",file,"in", dataFolder ,"will not be analyzed")
        if emptyFolder :
            print("*** ERROR : The selected data folder ("+dataFolder+") is empty, choose a folder with valid data and try again ***")
            k = input ("Press any key to close")
            sys.exit()
        return mergedDf
