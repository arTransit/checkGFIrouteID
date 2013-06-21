import fmeobjects
import bisect
import math

""" Global Variables
"""
LOGIT=0
MAXTIMEDIFF=100 # in seconds

##############################################################################
class FMEcalculatePoint(object):
    def __init__(self):
        self.distance = 0
        self.points=[]
        self.logger = fmeobjects.FMELogFile()

    def logging(self, m):
        if LOGIT: self.logger.logMessageString( str(m) )

    def input(self,f):
        if 'CONFIGDATA' in f.getAllAttributeNames():
            self.distance = float(f.getAttribute('DISTANCE'))
        else:
            self.points.append(f)

    def close(self):
        if self.distance > 0:
            for p in self.points:
                newX,newY= self.calculcateOffsetPoint(p.getCoordinate(0),float(p.getAttribute('STOPANGLE')),self.distance)
                newPoint = p.clone()
                newPoint.resetCoords()
                newPoint.addCoordinate(newX,newY)
                self.pyoutput(p)
                self.pyoutput(newPoint)
                
        else:
            self.logging("FMEcalculatePoint: ERROR - distance not defined")
        
    def calculcateOffsetPoint(self, coordinate,angle,distance):
        x = math.cos( math.radians((90.0 - angle) % 360.0)) * distance
        y = math.sin( math.radians((90.0 - angle) % 360.0)) * distance
        return x+coordinate[0],y+coordinate[1]
        
        

                
