import math
import fmeobjects

LOGIT = 1

class FMEgfiPeriods(object):
  
    def __init__(self):
        self.currentBus = 0
        self.currentRoute = 0
        self.fromTime = 0
        self.toTime = 0

        self.logger = fmeobjects.FMELogFile()

    def logging(self, m):
        if LOGIT: self.logger.logMessageString( str(m) )
        
    def input(self,f):
       # Variables to store current attribute values.
        newBus = int(f.getAttribute("BUS"))
        newRoute = int(f.getAttribute("ROUTE"))
        newTimestamp = int(f.getAttribute("TIMESTAMP"))
       
        # If this is the first record for this bus the bus has not moved
        #if (self.currentBusday,self.currentBus,self.currentRoute) != (newBusday,newBus,newRoute):
        if (self.currentBus,self.currentRoute) != (newBus,newRoute):
            g = fmeobjects.FMEFeature()
            g.setAttribute("BUSID",self.currentBus)
            g.setAttribute("ROUTEID",self.currentRoute)
            g.setAttribute("FROMTIME",self.fromTime)
            g.setAttribute("TOTIME",self.toTime)
            self.pyoutput( g )

            self.currentBus = newBus
            self.currentRoute = newRoute
            self.fromTime = newTimestamp
            self.toTime = 0
        else:
            self.toTime = newTimestamp
        
    
    def close(self):
        g = fmeobjects.FMEFeature()
        g.setAttribute("BUSID",self.currentBus)
        g.setAttribute("ROUTEID",self.currentRoute)
        g.setAttribute("FROMTIME",self.fromTime)
        g.setAttribute("TOTIME",self.toTime)
        self.pyoutput( g )

        
