from . import constants as c
from scipy import stats
import numpy as np
import math
import pandas as pd

class tableFunctions:

    def unitConverter (unit) :
        if unit < 1000 :
            unit = str(unit) + " nM"
        elif  1E03 <= unit < 1E06 :
            unit = str(unit/10**3) + " µM"
        elif  1E-03 <= unit < 1 :
            unit = str(unit/10**6) + " mM"
        else :
            unit = str(unit/10**9) + " M"
        return unit

# Function to sort igor exported csv data into a usable format for every compound
    def concLabelMap(df) :

        # tries to convert comma decimal into dot decimal if there is formatting confusion
        try :
            df["block"] = df["block"].str.replace(',', '.').astype(float)
        except :
            pass
        df = df.sort_values(by="conc")
        #Lists every concentration in increasing numbers
        concList = df["concX"].drop_duplicates()
        #Creates labels for each concentration ex :conc1,conc2
        concLabelList = ["conc"+str(i) for i in range(0,len(concList))]
        # Creates a dictionnary of concentration label to actual concentration ex : {1E-09 : conc1}
        concDict = {x:y for x,y in zip(concList,concLabelList)}
        # Adds the concentration label to each concentration
        df["concLabel"] = df['concX'].map(concDict)
        df["concLabelTemp"] = df["Compound"]+"_"+df['concX'].map(concDict)

        return df

# Organizes dataframes
    def dataOrganizer (df,correction) :

        # Adds correction value of 0 if the dataset is the vehicle itself
        if "VEHICLE" in df["Compound"].str.upper().iloc[0] :
            df["corrVal"] = 0
        # else map the correction for each concentration label
        else :
            df["corrVal"] = df["concVLabel"].map(correction)

        #Converts block value to current density
        df["Uncorrected_density"] = 1-df["block"]
        # Converts negative current density to 0
        #df.loc[df['Uncorrected_density'] < 0, 'Uncorrected_density'] = 0
        df["True_Uncorr_Density"] = df["Uncorrected_density"]

        df["Uncorrected_density"] = [np.random.uniform(0, 0.00001)  if x < 0 else x for x in df["Uncorrected_density"] ]

        # Adds corrected current density by adding the amount of block for the vehicle at this timepoint
        df["Corrected_density"] = df["Uncorrected_density"] + df["corrVal"]
        # converts correction value to % of current remaining after vehicle exposure
        df["corrVal"] = 1 - df["corrVal"]

        # temporary groupby to count number of cells per concentration
        dfTemp = df.groupby(["concLabel"]).count().reset_index()

        # dict to map number of cells per concentration
        countDict = {i:j for i,j in zip (dfTemp["concLabel"],dfTemp["Cells"])}
        # Drops unused columns
        df.drop(columns=["Cells","sweep","block"],inplace=True)
        # paired t.test
        pvalDict ={}
        # Loop for each concentration
        for col in df["concLabel"].drop_duplicates() :

            #filters the dataframe by concentration, selected the correct row wheter data has to be corrected or not
            target = df[df["concLabel"].str.contains(col)][c.pvalData]
            #Skips t.test if n=1, and replaces values by NaN
            if target.size <= 1 :
                pvalDict[col] = np.nan
            else :
                # Runs t-test by comparing to "baseline" values of 1, with the same amount of values as the screened compounds
                stat,pval = stats.ttest_rel([1 for x in range(len(target))],target)
                # appends the pvalues to the pvalue dictionnary
                pvalDict[col] = pval

        # Lists of individual datapoints before averaging, to be used in graph generation
        concListDict = {}
        rawConcListDict = {}
        for conc in df["concLabel"].drop_duplicates() :
            df2 = df[df["concLabel"].str.contains(conc)]
            rawConcList = [round(conc,3) for conc in df2["Uncorrected_density"]]
            concList = [round(conc,3) for conc in df2["Corrected_density"]]
            concListDict[conc]=concList
            rawConcListDict[conc]=rawConcList
        
        #Removes unsuitable columns for group, and then groups by concentration to generate stddev and mean values
        statsDf = df.drop(columns =["Info","Compound","concX","concLabelTemp","concVLabel","Online_1_base"]).groupby("concLabel").agg([np.mean, np.std])
        # Columns flatteing
        statsDf.columns =  ['_'.join(col) for col in statsDf.columns]
        # Removes useless column
        statsDf.drop(columns="conc_std",inplace=True)
        # Adds compound name to compound column
        statsDf["Compound"] = df["Compound"].iloc[0]
        #Resets the index
        statsDf.reset_index(inplace=True)
        #Fills NaN to 0 in the event that std deviations are NaN due to n=1
        statsDf.fillna(0,inplace=True)
        # renames conc_mean to conc
        statsDf.rename(columns={"conc_mean": "conc"}, inplace=True)

        #Round down scientific notation values to 3 digits to prevent errors
        lowConc = math.floor(round(1/statsDf["conc"][0],0))
        statsDf["conc"]=[round(x*lowConc,1)/lowConc for x in statsDf["conc"]]
        # remapping number of cells per conc
        statsDf["n="] = statsDf["concLabel"].map(countDict)
        #add SEM values to data
        statsDf["Corrected_density_sem"] = statsDf["Corrected_density_std"]/np.sqrt(statsDf["n="])
        #Converts concentrations to nM
        statsDf["Concentration (nM)"] = round(statsDf["conc"]*10**9,1)
        #Reorders columns
        statsDf = statsDf[["Compound","n=","concLabel","Concentration (nM)","Uncorrected_density_mean","Corrected_density_mean","corrVal_mean","Corrected_density_std","Corrected_density_sem"]]
        #Renames columns
        statsDf.rename(columns={"Corrected_density_std": "StdDev", "Corrected_density_sem": "SEM"}, inplace=True)
        # Adds pvalues to each concentration
        statsDf["pval"] = statsDf["concLabel"].map(pvalDict)

        # Add list of individual concentration to each concentration label
        statsDf["RawDensityList"] = statsDf["concLabel"].map(rawConcListDict)
        statsDf["DensityList"] = statsDf["concLabel"].map(concListDict)

        lowestConc = statsDf[statsDf["concLabel"].str.contains("conc1")]["Concentration (nM)"]
        statsDf.at[0, 'Concentration (nM)'] = round(lowestConc/100,3)

        # creates a dictionnary for IC50 tables indicating the % of inhibition
        inhibDict = {}
        for label,value in zip(statsDf["Concentration (nM)"][1:],statsDf[c.blockData][1:]) :
            inhibVal = round((1-value)*100,1)
            inhibDict[label] = inhibVal

        IC50Df2 = pd.DataFrame(data=inhibDict, index=[0])
        IC50Df2["Compound"] = statsDf["Compound"].iloc[0]

        return statsDf,IC50Df2

    def graphPadOrganizer (dfGp) :

        dfGp = dfGp[["Compound","Concentration (nM)",c.blockData,c.errorBarType,"n=",c.vehicleData]]
        dfGp.insert(1,"X title",dfGp["n="])
        dfGp.rename(columns={c.blockData: c.blockColName,c.vehicleData : c.bslColName}, inplace=True)
        dfGp ["n="] = dfGp ["n="].astype("int64")
        dfGp [c.blockColName] = np.round(dfGp [c.blockColName]*100,3)
        dfGp [c.bslColName] = np.round(dfGp [c.bslColName]*100,3)
        dfGp [c.errorBarType] = np.round(dfGp [c.errorBarType]*100,3)
        dfGp ["X title"] = "n=" + dfGp ["n="].astype("str")
        dfGp.drop_duplicates(subset = "Concentration (nM)", inplace=True)
        dfGp = dfGp.tail(-1)

        return dfGp

    def tableOrganizer (funcTableDf) :

        # removes the values from the baseline concentration
        funcTableDf = funcTableDf[~funcTableDf["concLabel"].str.contains("conc0")]

        decimals = 3
        header = ["Compound","Concentration",c.bslColName,c.blockColName,"Standard deviation","SEM","n=","p="]
        funcTableDf = funcTableDf[["Compound","Concentration (nM)",c.vehicleData,c.blockData,"StdDev","SEM","n=","pval"]]
        # pvalues formatting
        pList = ['{:.2e}'.format(x) for x in funcTableDf["pval"]]
        funcTableDf["p="] = pList
        #Values formatting and columns renaming
        funcTableDf["StdDev"] = np.round(funcTableDf["StdDev"],decimals)
        funcTableDf["SEM"] = np.round(funcTableDf["SEM"],decimals)
        funcTableDf[c.blockColName] = np.round(funcTableDf[c.blockData],decimals)
        funcTableDf[c.bslColName] = np.round(funcTableDf[c.vehicleData],decimals)

        # adds the right units to the concentrations values
        funcTableDf["Concentration"] = [(str((x/10**6))+" mM") if x >= 10**6 else (str((x/10**3))+" µM") if x >= 10**3 else (str(x)+" nM") for x in funcTableDf["Concentration (nM)"] ]

        funcTableDf = funcTableDf.rename(columns={"StdDev": "Standard deviation", "B": "c"})
        # Assigns a star to concentrations with a p-value under 0.05
        funcTableDf["Concentration"] = [(c+" *") if p <= 0.05 else (c) for p,c in zip(funcTableDf["pval"],funcTableDf["Concentration"])]

        funcTableDf = funcTableDf[header]

        # table float formating to 3 decimals
        for x in [c.bslColName,c.blockColName,"Standard deviation","SEM"] :
            funcTableDf[x] = funcTableDf[x].astype("float64").apply(lambda x: "{:.3f}".format(x))

        funcTableDf.loc[-1] = [funcTableDf["Compound"].tolist()[0],'Baseline', '1.000', '1.000',"n/a","n/a","n/a","n/a"]  # adding a row
        funcTableDf.index = funcTableDf.index + 1  # shifting index
        funcTableDf = funcTableDf.sort_index()  # sorting by index

        return funcTableDf,header

    def IC50sorter (ic50df,ic50Dict) :
        # Maps IC50 values for each compound
        ic50df["IC50 (nM)"] = ic50df["Compound"].map(ic50Dict)
        #Removes columns for conc0 and the index columns that shows up from using reset_index
        ic50df = ic50df.reset_index().drop(columns = ["index"])
        #Reorders the columns by moving the last 2 into the first position
        cols = ic50df.columns.tolist()
        # sorts column list by order of magnitude
        cols.sort(key=lambda v: (isinstance(v, str), v))
        #places Compound and IC50 at the begining
        cols = cols[-2:] + cols[:-2]
        ic50df = ic50df[cols]
        # Converts columns valus to % inhibition + value
        colList2=[x if isinstance(x,str) else ("% inhibition at "+str(tableFunctions.unitConverter(x))) for x in cols]
        #changes the column names
        ic50df.columns = colList2

        return ic50df

    def vehicleDummyTable(columns,concLabels) :

        df = pd.DataFrame(columns=columns)
        df["concLabel"] = concLabels
        for col in df.columns :
            if "concLabel" not in col :
                df[col] = 0

        df["Compound"] = "VEHICLE"
        df["concLabelTemp"] = df["Compound"] +"_" +df["concLabel"]
        df["Cells"] = [i for i in range(1,len(df["concLabel"])+1)]
        df["conc"] = [(float(10**i))/1E09 for i in range(1,len(df["concLabel"])+1)]
        df.reset_index(inplace=True,drop=True)


        return(df)
