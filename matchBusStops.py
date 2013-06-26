import fmeobjects

LOGIT=1

class FMEmatchBusStops(object):
    def __init__(self):
        self.logger = fmeobjects.FMELogFile()


    def logging(self, m):
        if LOGIT: self.logger.logMessageString( str(m) )
 

    def input(self,feature):
        self.logging("FMEmatchBusStops: starting %s" % feature.getAttribute('_ID'))
        # Get feature attributes
        stopAngles = self.getListAttribute(feature,'close{}.STOPANGLE')
        stopIDs = self.getListAttribute(feature,'close{}.STOPID')
        distances = self.getListAttribute(feature,'close{}.distance')

        # Calculate the entry angle onto the bus as being 90 degrees left of the current bearing
        # Boarding angle is equal to the direction one would be facing standing on the sidewalk
        # facing the front door of the bus 
        if feature.getAttribute('BEARING'):
            boardingAngle = float(feature.getAttribute('BEARING'))
            self.logging("FMEmatchBusStops: boardingAngle %s" % str(boardingAngle))
            
            # For each stop within the 60m radius defined by the neighbour finder determine the difference between the 
            # Stop angle and the boarding angle.  0 indicates a perfect match
            #divergence = map(lambda a: min( (float(a)-boardingAngle) % 360, (boardingAngle-float(a)) % 360), stopAngles)
            divergence = dict(map( lambda (i,a): (i, min( (float(a)-boardingAngle) % 360, 
                    (boardingAngle-float(a)) % 360) ), stopAngles.items()))
            
            '''
            for n in stopAngles:
                if boardingAngle < 45 and float(n) > 315:
                    divergence.append(abs(float(boardingAngle)-float(n)+360))
                elif boardingAngle > 315 and float(n) < 45:
                    divergence.append(abs(float(boardingAngle)-float(n)-360))
                else:
                    divergence.append(abs(float(boardingAngle)-float(n)))
            '''
            self.logging("FMEmatchBusStops: checking %d stopAngles" % len(stopAngles))        
            self.logging("FMEmatchBusStops: checking %d stopIDs" % len(stopIDs))        
            self.logging("FMEmatchBusStops: checking %d distances" % len(distances))        
            self.logging("FMEmatchBusStops: len.divergence %d" % len(divergence))        
            
            '''
            print "------------------------------------------------------"
            print "FMEmatchBusStops: starting %s" % feature.getAttribute('_ID')
            print "stopAngles"
            print stopAngles
            print "stopIDs"
            print stopIDs
            print "distances"
            print distances
            print "divergence"
            print divergence
            '''
            
            while len(distances) > 0:
                minDistance = min(distances.values())
                # minIndex = distances.index(minDistance)
                minIndex = [k for k,v in distances.items() if v == minDistance][0]
                self.logging("FMEmatchBusStops: minDistance %s, minIndex %s" % (str(minDistance),str(minIndex)))
                if divergence[minIndex] < 100:
                    #self.logging("FMEmatchBusStops: trying to match: %s" % 'close{'+str(minIndex)+'}.STOPID')
                    match = stopIDs[minIndex] 
                    self.logging("FMEmatchBusStops: match %s" % str(match))
                    feature.setAttribute('MATCH',match)
                    self.logging("FMEmatchBusStops: matchDistance %s" % str(minDistance))
                    feature.setAttribute('MATCHDISTANCE',minDistance)
                    feature.setAttribute('STATUS','MATCHED')
                    feature.setAttribute('DIVERGENCE',divergence[minIndex])
                    break
                else:
                    #distances.remove(minDistance)
                    del( distances[minIndex] )
                    
            if len(distances) == 0:
                feature.setAttribute('STATUS','TOODIVERGENT')

            feature.setAttribute('BANGLE',boardingAngle)
        else:
            feature.setAttribute('STATUS','NEIGHBOURMATCHED')
            feature.setAttribute('MATCH',feature.getAttribute('STOPID'))
        
        
        self.pyoutput(feature)
            
            
        '''
        if len(divergence) > 0:
            # determine the index of the closest match    
            minDivergence = min(divergence)
            minIndex = divergence.index(minDivergence)
            self.logging("FMEmatchBusStops: divergence %s %s" % (str(minDivergence),str(minIndex)))        
            if minDivergence < 90:
                #Return the STOPID of the closest match
                self.logging("FMEmatchBusStops: trying to match: %s" % 'close{'+str(minIndex)+'}.STOPID')
                match = stopIDs[minIndex] #feature.getAttribute('close{'+str(minIndex)+'}.STOPID')
                self.logging("FMEmatchBusStops: match %s" % str(match))
                feature.setAttribute('MATCH',match)
                matchDistance = distances[minIndex] #feature.getAttribute('close{'+str(minIndex)+'}.distance')
                self.logging("FMEmatchBusStops: matchDistance %s" % str(matchDistance))
                feature.setAttribute('MATCHDISTANCE',matchDistance)
                feature.setAttribute('STATUS','MATCHED')
            else:
                feature.setAttribute('STATUS','TOODIVERGENT')
                
            feature.setAttribute('BANGLE',boardingAngle)
            feature.setAttribute('DIVERGENCE',minDivergence)
        else:
            feature.setAttribute('STATUS','NOMATCHES')
        self.pyoutput(feature)
        '''

    def getListAttribute(self, feature, s):
        l = {}
        self.logging("getListAttribute: reading list %s" % s)
        for a in feature.getAllAttributeNames():
            #self.logging("getListAttribute: -- attribute %s" % a)
            if a.startswith( s[:s.find('{')] ) and a.endswith( s[s.find('}'):] ):
                i = int( a[a.find('{') + 1 : a.find('}')] )
                l[i] = float(feature.getAttribute( a ))
                self.logging("getListAttribute: -- -- appending %s:%s" % (a,str(feature.getAttribute( a ))))
        # self.logging("getListAttribute: done")
        return l
