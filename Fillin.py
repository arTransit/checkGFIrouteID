import fmeobjects

# fill in black stopIDs (called MATCH) with the previous stopID
#
# assume: data sorted by BUS and TIMESTAMP

LOGIT=0

class FMEFillInStops(object):
    def __init__(self):
        self.busid=0
        self.timestamp=0
        self.stopid=0
        self.logger = fmeobjects.FMELogFile()


    def logging(self, m):
        if LOGIT: self.logger.logMessageString( str(m) )
 

    def input(self,f):
        self.logging("FMEFillInStops: _ID %s" % f.getAttribute('_ID'))
        self.logging("FMEFillInStops: MATCH %s" % f.getAttribute('MATCH'))
        
        if f.getAttribute('MATCH'): 
            stopid = int(f.getAttribute('MATCH'))
        else: 
            stopid = 0

        if stopid >0:
            self.logging("FMEFillInStops: stopid > 0")
            self.stopid = stopid
            self.timestamp=int(f.getAttribute('TIMESTAMP'))
            self.busid=int(f.getAttribute('BUSID'))
            f.setAttribute('TIMEDIFF', 0 )
            
        elif (self.busid == int(f.getAttribute('BUSID'))) and (stopid ==0) :
            self.logging("FMEFillInStops: MATCH to %s" % str(self.stopid))
            f.setAttribute('MATCH', self.stopid )
            f.setAttribute('TIMEDIFF', int(f.getAttribute('TIMESTAMP')) - self.timestamp )
            f.setAttribute('MATCHSTATUS', '5MIN' )

        else:
            #f.setAttribute('MATCH', 0 )
            #f.setAttribute('TIMEDIFF', 0 )
            pass
            
        self.pyoutput( f )
                
    def close(self):
        pass

