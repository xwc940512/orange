#
# OWParallelGraph.py
#
# the base for all parallel graphs

import sys
import math
import orange
import os.path
from qt import *
from OWTools import *
from qwt import *
from Numeric import *

class DiscreteAxisScaleDraw(QwtScaleDraw):
    def __init__(self, labels):
        apply(QwtScaleDraw.__init__, (self,))
        self.labels = labels

    def label(self, value):
        index = int(round(value))
        if (index >= len(self.labels)):
            return ''
        if (index < 0):
            return ''
        return QString(str(self.labels[index]))

class OWParallelGraph(QwtPlot):
    def __init__(self, parent = None, name = None):
        "Constructs the graph"
        QwtPlot.__init__(self, parent, name)
        self.setWFlags(Qt.WResizeNoErase) #this works like magic.. no flicker during repaint!

        self.scaledData = []
        self.scaledDataAttributes = []
        
        self.enableAxis(QwtPlot.yLeft, 1)
        self.enableAxis(QwtPlot.xBottom, 1)
        self.setAutoReplot(FALSE)
        self.setAutoLegend(FALSE)
        self.setAxisAutoScale(QwtPlot.xBottom)
        self.setAxisAutoScale(QwtPlot.xTop)
        self.setAxisAutoScale(QwtPlot.yLeft)
        self.setAxisAutoScale(QwtPlot.yRight)
        self.setCanvasColor(QColor(Qt.white))
        self.repaint()

        newFont = QFont('Helvetica', 10, QFont.Bold)
        self.setTitleFont(newFont)
        self.enableGridX(FALSE)
        self.enableGridY(FALSE)
        self.setAxisTitleFont(QwtPlot.xBottom, newFont)
        self.setAxisTitleFont(QwtPlot.xTop, newFont)
        self.setAxisTitleFont(QwtPlot.yLeft, newFont)
        self.setAxisTitleFont(QwtPlot.yRight, newFont)
        #self.setAxisScale(QwtPlot.yLeft, 0, 1, 1)
        #self.setAxisScale(QwtPlot.yRight, 0, 1, 1)

        newFont = QFont('Helvetica', 9)
        self.setAxisFont(QwtPlot.xBottom, newFont)
        self.setAxisFont(QwtPlot.xTop, newFont)
        self.setAxisFont(QwtPlot.yLeft, newFont)
        self.setAxisFont(QwtPlot.yRight, newFont)
        self.setLegendFont(newFont)

        self.tipLeft = None
        self.tipRight = None
        self.tipBottom = None
        self.dynamicToolTip = DynamicToolTip(self)

        self.showMainTitle = FALSE
        self.mainTitle = None
        self.showXaxisTitle = FALSE
        self.XaxisTitle = None
        self.showYLaxisTitle = FALSE
        self.YLaxisTitle = None
        self.showYRaxisTitle = FALSE
        self.YRaxisTitle = None
        
        self.noneSymbol = QwtSymbol()
        self.noneSymbol.setStyle(QwtSymbol.None)        
        self.curveIndex = 0

    def setCanvasColor(self, c):
        self.setCanvasBackground(c)
        self.repaint()


    def saveToFile(self):
        qfileName = QFileDialog.getSaveFileName("graph.png","Portable Network Graphics (.PNG)\nWindows Bitmap (.BMP)\nGraphics Interchange Format (.GIF)", None, "Save to..")
        fileName = str(qfileName)
        (fil,ext) = os.path.splitext(fileName)
        ext = ext.replace(".","")
        ext = ext.upper()

        buffer = QPixmap(self.size()) # any size can do, now using the window size
        painter = QPainter(buffer)
        painter.fillRect(buffer.rect(), QBrush(self.palette().active().background())) # make background same color as the widget's background
        self.printPlot(painter, buffer.rect())
        painter.end()
        buffer.save(fileName, ext)
    
    def setXlabels(self, labels):
        self.setAxisScaleDraw(QwtPlot.xBottom, DiscreteAxisScaleDraw(labels))
        self.setAxisScale(QwtPlot.xBottom, 0, len(labels) - 1, 1)
        self.setAxisMaxMinor(QwtPlot.xBottom, 0)
        self.setAxisMaxMajor(QwtPlot.xBottom, len(labels))
        self.updateToolTips()

    def updateToolTips(self):
        "Updates the tool tips"
#        self.dynamicToolTip.addToolTip(self.yRight, self.tipRight)
#        self.dynamicToolTip.addToolTip(self.yLeft, self.tipLeft)
#        self.dynamicToolTip.addToolTip(self.xBottom, self.tipBottom)

    def resizeEvent(self, event):
        "Makes sure that the plot resizes"
        self.updateToolTips()
        self.updateLayout()

    def paintEvent(self, qpe):
        QwtPlot.paintEvent(self, qpe) #let the ancestor do its job
        self.replot()
 
    def setShowMainTitle(self, b):
        self.showMainTitle = b
        if (self.showMainTitle <> 0):
            self.setTitle(self.mainTitle)
        else:
            self.setTitle(None)
        self.updateLayout()
        self.repaint()

    def setMainTitle(self, t):
        self.mainTitle = t
        if (self.showMainTitle <> 0):
            self.setTitle(self.mainTitle)
        else:
            self.setTitle(None)
        self.updateLayout()
        self.repaint()

    def scaleData(self, data, index):
        attr = data.domain[index]
        temp = []
        # is the attribute discrete
        if attr.varType == orange.VarTypes.Discrete:
            # TO DO NUJNO: naredi hash tabelo z imeni kategoricnih vrednosti ter indexi
            if len(attr.values) > 1:
                num = float(len(attr.values)-1)
            else:
                num = float(1)
            for i in range(len(data)):
                if data[i][index].isSpecial():
                    temp.append(1)
                else:
                    temp.append(data.domain[index].values.index(data[i][index].value) / num)
        # is the attribute continuous
        else:
            # first find min and max value
            min = data[0][attr].value
            max = data[0][attr].value
            for item in data:
                if item[attr].value < min:
                    min = item[attr].value
                elif item[attr].value > max:
                    max = item[attr].value

            diff = max - min
            # create new list with values scaled from 0 to 1
            for i in range(len(data)):
                temp.append((data[i][attr].value - min) / diff)
        return temp


    def setData(self, data):
        self.rawdata = data
        self.scaledData = []
        self.scaledDataAttributes = []
        
        if data == None:
        	return

        for index in range(len(data.data.domain)):
            attr = data.data.domain[index]
            self.scaledDataAttributes.append(attr.name)
            scaled = self.scaleData(data.data, index)
            self.scaledData.append(scaled)

    def updateData(self, labels, className):
        self.removeCurves()
        self.axesKeys = []
        self.curveKeys = []
        
        self.setAxisScaleDraw(QwtPlot.xBottom, DiscreteAxisScaleDraw(labels))
        self.setAxisScale(QwtPlot.xBottom, 0, len(labels) - 1, 1)
        self.setAxisMaxMinor(QwtPlot.xBottom, 0)
        self.setAxisMaxMajor(QwtPlot.xBottom, len(labels)-1)

        if len(self.scaledData) == 0 or len(labels) == 0:
            self.updateLayout()
            return

        for i in range(len(labels)):
            newCurveKey = self.insertCurve(labels[i])
            self.axesKeys.append(newCurveKey)
            self.setCurveData(newCurveKey, [i,i], [0,1])
        
        length = len(labels)
        indices = []
        xs = []

        # create a table of indices that stores the sequence of variable indices
        for label in labels:
            index = self.scaledDataAttributes.index(label)
            indices.append(index)

        # create a table of class values that will be used for coloring the lines
        scaledClassData = []
        if className != "(One color)" and className != '':
            scaledClassData = self.scaleData(self.rawdata.data, className)

        xs = range(length)
        dataSize = len(self.scaledData[0])        
        for i in range(dataSize):
            newCurveKey = self.insertCurve(str(i))
            self.curveKeys.append(newCurveKey)
            newColor = QColor()
            if scaledClassData != []:
                newColor.setHsv(scaledClassData[i]*255, 255, 255)
            self.setCurvePen(newCurveKey, QPen(newColor))
            ys = []
            for index in indices:
                ys.append(self.scaledData[index][i])
            self.setCurveData(newCurveKey, xs, ys)
                       
    
if __name__== "__main__":
    #Draw a simple graph
    a = QApplication(sys.argv)        
    c = OWParallelGraph()
    c.setCoordinateAxes(['red','green','blue','light blue', 'dark blue', 'yellow', 'orange', 'magenta'])
    #c.setMainTitle("Graph Title")
    #c.setShowMainTitle(1)
        
    a.setMainWidget(c)
    c.show()
    a.exec_loop()
