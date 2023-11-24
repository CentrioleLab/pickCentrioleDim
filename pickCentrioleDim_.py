
# This is how we can acces the ImageJ API:
# https://imagej.nih.gov/ij/developer/api/allclasses-noframe.html
from ij import IJ, WindowManager
from ij.gui import GenericDialog, Roi, Plot, WaitForUserDialog
from ij.process import ImageConverter
from ij.plugin.frame import RoiManager
from java.awt.event import ActionListener
from fiji.util.gui import GenericDialogPlus
from ij.measure import ResultsTable
from ij.gui import NonBlockingGenericDialog
from ij.io import OpenDialog
from ij import gui
import os


def returnPlotProfile(col):
    if col == 0:
        bg_col = "Magenta"
    else :
        bg_col = "Cyan"
    ## check an imge is opened
    if WindowManager.getIDList() is None:
        return False
    select_ok = False
    while(select_ok == False):
        ima = IJ.getImage()
        user_roi = ima.getRoi()
        if (str(type(user_roi)) != '<type \'NoneType\'>'): # A Roi exists
            if (user_roi.getType() == 0) or (user_roi.getType() == 5): # ROI OK
                profile = gui.ProfilePlot(ima) # profile is a ProfilePlot
                plotprofile = profile.getPlot()    #plotprofile is a Plot
                plotprofile.setBackgroundColor(bg_col)
                plotprofile.show()
                select_ok = True
                return (plotprofile, profile.getPlotSize().width)
        wait = WaitForUserDialog("Select a line/rectangle for plotprofile")
        wait.show()

def measureCoordsXY():
    IJ.run("Measure")
    table = ResultsTable.getResultsTable()
    nval = table.size()
    y1 = table.getValue("Y", nval - 2) # 1er point
    x1 = table.getValue("X", nval - 2)
    x2 = table.getValue("X", nval - 1) # 2eme pointf
    y2 = table.getValue("Y", nval - 1)
    return (x1, y1, x2, y2)


def draw50lines(plotprofile, maxwidth, coords):
    x1, y1, x2, y2 = coords
    plotprofile.setLineWidth(3)
    plotprofile.drawDottedLine(0, y1/2, x1, y1/2,int(maxwidth/75))
    plotprofile.drawDottedLine(x2, y2/2, maxwidth, y2/2, int(maxwidth/100))
    plotprofile.setLineWidth(1)
    plotprofile.updateImage()


def waitFor2points():
    n_points = 0
    while(n_points!=2):
        IJ.setTool("multipoint")
        wait = WaitForUserDialog("Select 2 points")
        wait.show()
        ima = IJ.getImage()
        proi = ima.getRoi()
        roi_points = proi.getContainedPoints()
        n_points = len(roi_points)
        if n_points != 2: #Ask if the user wants to retry picking
            win = GenericDialog("Wrong Picking")
            win.addMessage('You didn\'t pick 2 points.')
            win.enableYesNoCancel('I\'ll pick again.', 'Abort plugin.')
            win.hideCancelButton()
            win.showDialog()
            if win.wasCanceled():
                return False
            elif win.wasOKed():
                continue
            else:
                return False
    # We can extract coordinates point :
    return measureCoordsXY()


def getLengthPosition(col):
    plotprofile = returnPlotProfile(col)
    coords = waitFor2points()
    if coords :
        draw50lines(plotprofile[0], plotprofile[1], coords)
    else : # if the user doesn't want to pick anymore
        return False
    IJ.run("Select None") # Reset selection
    final = waitFor2points()
    return final


def workingWindow(filename):
    cancel = False
    n_p = 0
    while (cancel == False):
        win = NonBlockingGenericDialog("Options Choices")
        win.addChoice('Draw a line for a plot profile. The signal is', ['1st Prot','2nd Prot'], '1st Prot')
        win.addMessage('then, select "50% Lines" to pick the 50% intensity points.\n')
        win.addMessage('---------------------------------------------------------')
        win.addChoice('Select 2 points as:', ['1st Prot','2nd Prot'], '1st Prot')
        win.addMessage('then, select "Save points" to save them in a file.\n')
        win.addStringField("centriole name :", "", 20)
        win.enableYesNoCancel('50% Lines', 'Save points')
        win.showDialog()
        choice_1 = win.getNextChoiceIndex()
        choice_2 = win.getNextChoiceIndex()
        label = win.getNextString()
        if win.wasCanceled():
            return False
        elif win.wasOKed(): # Draw the mid-intensity line
            getLengthPosition(choice_1)
        else: # Save selected points
            if choice_2 == 0: # Red/Magenta signal
                newline = True
            else :
                newline = False
            points = getXselectedPoints()
            if points:
                writePointsFile( filename, points, newline, label)


def getXselectedPoints():
    ima = IJ.getImage()
    proi = ima.getRoi()
    if proi is None:
        win = GenericDialog("Wrong Picking")
        win.addMessage('You didn\'t select 2 points.')
        win.showDialog()
        return False
    roi_points = proi.getContainedPoints()
    n_points = len(roi_points)
    if n_points != 2:
        win = GenericDialog("Wrong Picking")
        win.addMessage('You didn\'t select 2 points.')
        win.showDialog()
        return False
    # We can extract coordinates point :
    return measureCoordsXY()


def writePointsFile(filout, points, newline = True, label = ''):
    x1 = str(points[0])
    x2 = str(points[2])
    if newline :
        line = '\n' + label + ', ' + x1 + ', ' + x2
    else:
        line = ', ' + x1 + ', ' + x2
    output = open(filout, 'a')
    output.write(line)
    output.close()


def outputFile():
    ok = False
    while (ok == False):
        gd = GenericDialogPlus("Output")
        gd.addDirectoryField("Select output Folder :", IJ.getDirectory("current"), 20)
        gd.addStringField("Output filename :", "output.csv", 20)
        gd.showDialog()
        folder = gd.getNextString()
        name = gd.getNextString()
        filename = folder + '/' + name
        if (os.path.exists(filename)):
            win = GenericDialog("Warning")
            win.addMessage('File Exists and will be deleted.')
            win.enableYesNoCancel('Change name', 'Keep this name')
            win.hideCancelButton()
            win.showDialog()
            if win.wasOKed():
                ok = False
            else:
                ok = True
        else :
            ok = True
    IJ.log(filename)
    output = open(filename, 'w')
    output.write('Label, prot1_pk1, prot1_pk2, prot2_pk1, prot2_pk2')
    output.close()
    return filename

if __name__ in ['__builtin__','__main__']:
    filename = outputFile()
    res  = workingWindow(filename)




