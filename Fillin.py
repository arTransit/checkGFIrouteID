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

    def input(self,f):

        if f.getAttribute('MATCH') and (int(f.getAttribute('MATCH')) >0):
            self.stopid=int(f.getAttribute('MATCH'))
            self.timestamp=int(f.getAttribute('TIMESTAMP'))
            self.busid=int(f.getAttribute('BUS'))
            f.setAttribute('TIMEDIFF', 0 )
            
        elif self.busid == int(f.getAttribute('BUS')):
            f.setAttribute('MATCH', self.stopid )
            f.setAttribute('TIMEDIFF', int(f.getAttribute('TIMESTAMP')) - self.timestamp )

        else:
            f.setAttribute('MATCH', 0 )
            f.setAttribute('TIMEDIFF', 0 )
            
        self.pyoutput( f )
                
    def close(self):
        pass

