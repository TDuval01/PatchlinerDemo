from . import constants as c
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
from scipy.optimize import curve_fit

import warnings
warnings.filterwarnings("ignore")


# Graphs parameters ---
#Defines the limits for each parameters of the function (Top,Hill curve,IC50,bottom)
boundsFit=((0, -4, 0, 0), (10, 4, 10**12, 1))
# inital guess for the curve fitting
guess = [0, 1, 1, 1]
# Numbers of points to try curve fitting
fitPoints = 250000


class graphFunctions:
        #4PL formula to fit data for IC50 calculation
    def curveFitHill(x,Min, HillSlope, Mid, Max):
        return (Max+((Min-Max)/(1+(x/Mid)**HillSlope)))

    # Function to calculate the IC50 from the 4PL above
    def ICfifty (y,Min,HillSlope,Mid,Max) :
        return Mid*(((Min-Max)/(y-Max)-1)**(1/HillSlope))
    
    # Functions that extracts scatter and mean values for the graph generation, also generates x values needed for the fit
    def curveData (df) :
        # "Explodes" the individual concentration list to generate a scatterplot for each data point
        dfExploded = df[1:].explode([c.dataList])

        # scatter values for the graph
        xScatter = dfExploded["Concentration (nM)"]
        yScatter = dfExploded[c.dataList]

        # means values used for curve fitting normalized compound data
        xMean = df["Concentration (nM)"]
        yMean = df[c.blockData]

        #Defines the amount of "x values" the data will be fitted on
        xFit = np.linspace(xMean.min(),xMean.max(),fitPoints)
        
        return xScatter,yScatter,xMean,yMean,xFit
    
    # Function cut the graph to to the x values actually screened
    def graphBounds (x_fit) :
        xFitCut = []
        for x in x_fit :
            start = x_fit[0]
            if x >= start*100:
                xFitCut.append(x)
            else :
                pass

        fitStart = len(x_fit)-len(xFitCut)
        graphX = x_fit[fitStart:]

        return graphX
    # Function that sets the parameters for each graph
    def graphSettings (settingsDf):

        #Gets the name of the compound
        compoundName = settingsDf["Compound"].iloc[0]
        # Gets the maximum value including the stdDev to set the maximum Y=value on the graph
        settingsDf["mean+std"] = settingsDf[c.blockData] + settingsDf[c.errorBarType]
        ymax = round(settingsDf["mean+std"].max(),1)+0.05
        # Sets ymax value to 1.2 if the ymax is lower than this value
        if ymax < 1.2 :
            ymax = 1.2

        xmin = settingsDf["Concentration (nM)"][1:].min()/5
        xmax = settingsDf["Concentration (nM)"].max()*5

        plt.title(compoundName)
        plt.xlabel("["+compoundName+"] (nM)")
        plt.xscale('symlog',subs=[2, 3, 4, 5, 6, 7, 8, 9])
        plt.xticks([1,10,100,1000,10000,100000,1000000,10000000,100000000])
        plt.xlim(xmin,xmax)

        plt.ylim([-0.1,ymax])
        plt.yticks(np.arange(-0.1, round(ymax,1), step=0.1))
        plt.ylabel(c.voltage+" normalized \n post-compound current density")

        plt.grid(color="grey",linestyle="--",linewidth=0.5,axis="y")
        plt.legend(loc="upper right")

        plt.gca().xaxis.set_major_formatter(StrMethodFormatter('{x:.0f}'))
        plt.gca().tick_params(direction='inout', length=8, width=1.5, colors='k',grid_color='k', grid_alpha=0.5, which="major")
        plt.gca().tick_params(direction='inout', length=4, width=1, colors='k',grid_color='k', grid_alpha=0.5, which="minor")

        loopCount = 0
        for x,y,n,p in zip(settingsDf["Concentration (nM)"],settingsDf[c.blockData],settingsDf["n="],settingsDf["pval"]):
            loopCount += 1
            if loopCount > 1 :
                if p <= 0.05 :
                    label = "* n = " + str(n)
                else :
                    label = "  n = " + str(n)
            else :
                label = ""

            plt.annotate(label, # this is the text
                        (x,y), # these are the coordinates to position the label
                        textcoords="offset points", # how to position the text
                        xytext=(20,10), # distance from text to points (x,y)
                            ha='center') # horizontal alignment can be left, right or center

        plt.savefig(c.graphFolder+"/"+compoundName,dpi=100, bbox_inches="tight", pad_inches=0.3)
        plt.close()
        return()
    
    # Function ot fit the generated data into a 4PL equation and calculate the resulting IC50 if applicable
    def curveFit(curveDf) :

        # retrieves data for the curve fitting
        x_val_scatter,y_val_scatter,x_val,y_val,x_fit = graphFunctions.curveData(curveDf)
        #retrieves the parameters of the curve fitting function for the 4PL equation descript in the curveFitHill function
        nbTries = 10
        try :
            popt,cov =  curve_fit(graphFunctions.curveFitHill, x_val, y_val , guess, bounds=boundsFit)
       
        # tries a different guess if the initial guess did not work
        except :
            retry = 0
            # Tries to fit the data nbTries amount of time by changing the guesses
            while retry < nbTries :
                retry += 1
                guess_retry = [retry,retry,retry,retry]
                try :
                    popt,cov =  curve_fit(graphFunctions.curveFitHill, x_val, y_val , guess_retry, bounds=boundsFit)
                    retry = nbTries+1
                except :
                    continue           
                # If theres still no fit after 10 steps, display error message and skip analysis of this compound
                if retry == nbTries :
                    print("Error in the fit for",curveDf["Compound"].iloc[0],": could not manage to fit the data into a 4PL equation , perhaps add more data points/concentrations?")
                    return False
                
        # Gets the real x values for the graph
        graphX = graphFunctions.graphBounds(x_fit)

        # Does not calculate the IC50 of the "bottom" value of the 4PL is above 0.5, to prevent double scalar error
        if popt[3] > 0.5 :
            ic50 = np.nan
        else :
            ic50= graphFunctions.ICfifty (0.5,*popt)

        #Curve fitting plot
        plt.plot(graphX,graphFunctions.curveFitHill(graphX,*popt), label = curveDf["Compound"].iloc[0],c="dodgerblue",zorder=1) # datafit
        if c.drawVehicleOnGraph :
            poptVeh,covVeh =  curve_fit(graphFunctions.curveFitHill, x_val, curveDf["corrVal_mean"] , guess, bounds=boundsFit)
            plt.plot(graphX,graphFunctions.curveFitHill(graphX,*poptVeh), label = "Vehicle", ls="dashed",c = "g",zorder=1) # Vehicle fit

        #Scatterplots
        plt.scatter(x_val_scatter,y_val_scatter,s=8,c="dodgerblue",zorder=2),  # Uncorrected individual data points
        plt.errorbar(curveDf["Concentration (nM)"][1:],curveDf[c.blockData][1:],curveDf[c.errorBarType][1:],fmt="none",color="k",elinewidth=1,capthick=1,capsize=3) # error bars

        graphFunctions.graphSettings(curveDf)

        return ic50
    
    # Function ot fit the generated vehicle data into a 4PL equation
    def vehicleCurveFit(vehicleCurveDf) :

        # Retrieves graph data from the curveData function
        x_val_scatter,y_val_scatter,x_val,y_val,x_fit = graphFunctions.curveData(vehicleCurveDf)

        popt,cov =  curve_fit(graphFunctions.curveFitHill, x_val, y_val , guess, bounds=boundsFit)

        graphX = graphFunctions.graphBounds(x_fit)

        #Scatterplot
        plt.scatter(x_val_scatter,y_val_scatter,s=4),
        plt.plot(graphX,graphFunctions.curveFitHill(graphX,*popt), label = "Vehicle")
        plt.errorbar(vehicleCurveDf["Concentration (nM)"],vehicleCurveDf["Uncorrected_density_mean"],vehicleCurveDf[c.errorBarType],fmt="none",color="k",elinewidth=1,capthick=1,capsize=3)
        graphFunctions.graphSettings(vehicleCurveDf)

        return()
    
