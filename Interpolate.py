import fmeobjects
import bisect
import math

""" Global Variables
"""

LOGIT=1
MAXTIMEDIFF=100 # in seconds
MINPOINTDISTANCE=3.0  # minimum distance between gfi points

##############################################################################
class FMEInterpolatePoints(object):
    def __init__(self):
        self.gpsData = []
        self.gfiData = []
        self.metaArray = {'GFI':self.gfiData, 'GPS':self.gpsData}
        self.previousBearing = None
        self.previousX = None
        self.previousY = None

        self.logger = fmeobjects.FMELogFile()

    def logging(self, m):
        if LOGIT: self.logger.logMessageString( str(m) )

    def input(self,f):
        if f.getAttribute('SOURCE') in ('GFI','GPS'):
            self.metaArray[ f.getAttribute('SOURCE') ].append( f )
        else:
            self.logging("Unknown feature.")

            
    # assumptions: sorted by BUSID,TIMESTAMP
    def close(self):
        currentBus = 0
        currentTime = 0
        currentGPS = self.gpsData.pop(0)
        lastGPS = None
        self.previousBearing = None
        self.previousX = None
        self.previousY = None
        
        self.logging("FMEInterpolatePoints: Processing...")
        self.logging("FMEInterpolatePoints: gfiData %s" % len(self.gfiData) )
        self.logging("FMEInterpolatePoints: gpsData %s" % len(self.gpsData) )
        
        for gfi in self.gfiData:
            self.logging("\nFMEInterpolatePoints: working on %s %s" % (
                    gfi.getAttribute( 'BUSID' ),gfi.getAttribute( 'TIMESTAMP' )))
            self.logging("FMEInterpolatePoints: gps is %s %s" % (
                    currentGPS.getAttribute( 'BUSID' ),currentGPS.getAttribute( 'TIMESTAMP' )))
            
            # new bus, move up apc data until bus matches
            if currentBus < int( gfi.getAttribute('BUSID')):
                currentBus = int( gfi.getAttribute('BUSID') )
                self.logging("FMEInterpolatePoints: new bus %s" % str(currentBus) )
                self.previousBearing = None
                self.previousX = None
                self.previousY = None
                while ( currentBus > int( currentGPS.getAttribute('BUSID')) ):
                    lastGPS = currentGPS
                    currentGPS = self.gpsData.pop(0)
                self.logging("FMEInterpolatePoints: gps bus/moved to %s %s" % (
                        currentGPS.getAttribute( 'BUSID' ),currentGPS.getAttribute( 'TIMESTAMP' )))
            
            # no more apc data for current bus
            if int( currentGPS.getAttribute('BUSID')) > currentBus:
                self.logging("FMEInterpolatePoints: no more gps for bus %s" % str(currentBus) )
                self.pyoutput( self.makeNullFeature( gfi))
            else:
                # timestamp match - copy point
                if int( gfi.getAttribute('TIMESTAMP')) == int( currentGPS.getAttribute('TIMESTAMP')):
                    self.logging("FMEInterpolatePoints: gfi TIMESTAMP equal")
                    self.pyoutput( self.makePointFeature( gfi, currentGPS, lastGPS ))

                # move up apc data past current GFI timestamp and interpolate
                elif int( gfi.getAttribute('TIMESTAMP')) > int( currentGPS.getAttribute('TIMESTAMP')):
                    self.logging("FMEInterpolatePoints: gfi TIMESTAMP > gps")
                    while ( int(gfi.getAttribute('TIMESTAMP')) > int(currentGPS.getAttribute('TIMESTAMP')) ):
                        lastGPS = currentGPS
                        if len(self.gpsData) < 1:
                            self.logging("    gps data finished")
                            currentGPS = None
                            break
                        else:
                            currentGPS = self.gpsData.pop(0)

                        if currentBus != int(currentGPS.getAttribute('BUSID')): 
                            self.logging("    have passed over bus/apc")
                            break
                    
                    if (currentGPS is not None) and (currentBus == int(currentGPS.getAttribute('BUSID'))):
                        self.logging("    going to interpolate")
                        self.pyoutput( self.makePointFeature( gfi, currentGPS, lastGPS ))
                    else:
                        self.logging("    going to null")
                        self.pyoutput( self.makeNullFeature( gfi))

                else: # gfi.getAttribute('TIMESTAMP') < currentGPS.getAttribute('TIMESTAMP')
                    self.logging("FMEInterpolatePoints: gif TIMESTAMP < gps")
                    if lastGPS and ( int(currentGPS.getAttribute('BUSID')) == int(lastGPS.getAttribute('BUSID')) ): 
                        self.logging("    going to interpolate")
                        self.pyoutput( self.makePointFeature( gfi, currentGPS, lastGPS ))                    
                    else:
                        self.logging("FMEInterpolatePoints: gif TIMESTAMP fail -> going to null")
                        self.pyoutput( self.makeNullFeature( gfi))

                if len(self.gpsData) < 1:
                    self.logging("    gps data finished - exit")
                    break

    def makePointFeature( self, g, gps1, gps2=None):
        self.logging("makePointFeature: making new point for %s %s" % (
                g.getAttribute( 'BUSID' ),g.getAttribute( 'TIMESTAMP' )))
        f = fmeobjects.FMEFeature()
        for a in g.getAllAttributeNames():
            f.setAttribute( a, g.getAttribute( a ))

        if gps2:
            self.logging("makePointFeature: interpolating")
            x1,y1 = gps1.getCoordinate(0)
            x2,y2 = gps2.getCoordinate(0)
            timestamp1 = float(gps1.getAttribute( 'TIMESTAMP' ))
            timestamp2 = float(gps2.getAttribute( 'TIMESTAMP' ))
            timestamp0 = float(g.getAttribute( 'TIMESTAMP' ))

            dx = float(x2-x1)
            dy = float(y2-y1)
            timeRatio = (timestamp0 - timestamp1) / (timestamp2 - timestamp1)
            x = (timeRatio * dx) + x1
            y = (timeRatio * dy) + y1
            
        else:
            self.logging("makePointFeature: not interpolating")
            x,y = gps1.getCoordinate(0)
            
        if self.previousX is None: 
            #previousPointDistance=0
            f.setAttribute( 'POINTCALC', 0)
        else: 
            previousPointDistance= math.sqrt(math.pow(( self.previousX-x ),2) 
                    + math.pow(( self.previousY-y ),2))
        
            dx = float(self.previousX - x)
            dy = float(self.previousY - y)
            bearing = math.degrees( math.atan2( dy,dx ) ) % 360
            distance= math.sqrt(math.pow(( dx ),2) + math.pow(( dy ),2))
            speed = distance / float(timestamp1 - timestamp2)

            if not self.previousBearing or (previousPointDistance > MINPOINTDISTANCE):
                self.previousBearing = bearing
            else:  # bus has not moved > MINPOINTDISTANCE
                bearing = self.previousBearing
        
            f.setAttribute( 'POINTCALC', 1)
            f.setAttribute( 'SPEED', speed)
            f.setAttribute( 'BEARING', bearing)
                
        self.previousX = x
        self.previousY = y

        f.setAttribute( 'GPSID', gps1.getAttribute( '_ID' ))
        f.setAttribute( '_STATUS', 1)
        f.setCoordSys( gps1.getCoordSys() )
        f.setGeometryType( gps1.getGeometryType() )
        f.addCoordinate( x, y )
        f.setAttribute( 'LATITUDE', y)
        f.setAttribute( 'LONGITUDE', x)
        return f
        
    def makeNullFeature( self, g ):
        g.setAttribute( '_STATUS', 0)
        g.setAttribute( 'POINTCALC', 0)
        return g

##############################################################################
class FMEInterpolatePoints2(object):
    def __init__(self):
        self.apcData = []
        self.gfiData = []
        self.metaArray = {'GFI':self.gfiData, 'APC':self.apcData}
        
        self.logger = fmeobjects.FMELogFile()

    def logging(self, m):
        if LOGIT: self.logger.logMessageString( str(m) )

        
    def input(self,f):
        if f.getAttribute('SOURCE') in ('GFI','APC'):
            self.metaArray[ f.getAttribute('SOURCE') ].append( f )
        else:
            self.logging("Unknown feature.")


    def close(self):
        currentBus = 0
        currentTime = 0
        currentApc = self.apcData.pop(0)
        lastApc = None
        
        self.logging("FMEInterpolatePoints2: Processing...")
        self.logging("FMEInterpolatePoints2: gfiData %s" % len(self.gfiData) )
        self.logging("FMEInterpolatePoints2: apcData %s" % len(self.apcData) )
        
        for gfi in self.gfiData:
            self.logging("\nFMEInterpolatePoints2: working on %s %s" % (
                    gfi.getAttribute( 'BUS' ),gfi.getAttribute( 'TIMESTAMP' )))
            self.logging("FMEInterpolatePoints2: apc is %s %s" % (
                    currentApc.getAttribute( 'BUSID' ),currentApc.getAttribute( 'TIMESTAMP' )))
            
            # new bus, move up apc data until bus matches
            if currentBus < int( gfi.getAttribute('BUS')):
                currentBus = int( gfi.getAttribute('BUS') )
                self.logging("FMEInterpolatePoints2: new bus %s" % str(currentBus) )
                while ( currentBus > int( currentApc.getAttribute('BUSID')) ):
                    lastApc = currentApc
                    currentApc = self.apcData.pop(0)
                self.logging("FMEInterpolatePoints2: apc bus/moved to %s %s" % (
                        currentApc.getAttribute( 'BUSID' ),currentApc.getAttribute( 'TIMESTAMP' )))
            
            # no more apc data for current bus
            if int( currentApc.getAttribute('BUSID')) > currentBus:
                self.logging("FMEInterpolatePoints2: no more apc for bus %s" % str(currentBus) )
                self.pyoutput( self.makeNullFeature( gfi))
            else:
                # timestamp match - copy point
                if int( gfi.getAttribute('TIMESTAMP')) == int( currentApc.getAttribute('TIMESTAMP')):
                    self.logging("FMEInterpolatePoints2: gfi TIMESTAMP equal")
                    self.pyoutput( self.makePointFeature( gfi, currentApc ))

                # move up apc data past current GFI timestamp and interpolate
                elif int( gfi.getAttribute('TIMESTAMP')) > int( currentApc.getAttribute('TIMESTAMP')):
                    self.logging("FMEInterpolatePoints2: gfi TIMESTAMP > apc")
                    while ( int(gfi.getAttribute('TIMESTAMP')) > int(currentApc.getAttribute('TIMESTAMP')) ):
                        lastApc = currentApc
                        currentApc = self.apcData.pop(0)
                        if currentBus != int(currentApc.getAttribute('BUSID')): 
                            self.logging("    have passed over bus/apc")
                            break
                    self.logging("    time/moved apc to %s %s" % (
                            currentApc.getAttribute( 'BUSID' ),currentApc.getAttribute( 'TIMESTAMP' )))
                    
                    if currentBus == int(currentApc.getAttribute('BUSID')):
                        self.logging("    going to interpolate")
                        self.pyoutput( self.makePointFeature( gfi, currentApc, lastApc ))
                    else:
                        self.logging("    going to null")
                        self.pyoutput( self.makeNullFeature( gfi))

                else: # gfi.getAttribute('TIMESTAMP') < currentApc.getAttribute('TIMESTAMP')
                    self.logging("FMEInterpolatePoints2: gif TIMESTAMP < apc")
                    if lastApc and ( int(currentApc.getAttribute('BUSID')) == int(lastApc.getAttribute('BUSID')) ): 
                        self.logging("    going to interpolate")
                        self.pyoutput( self.makePointFeature( gfi, currentApc, lastApc ))                    
                    else:
                        self.logging("FMEInterpolatePoints2: gif TIMESTAMP fail -> going to null")
                        self.pyoutput( self.makeNullFeature( gfi))
                
    def makePointFeature( self, g, apc1, apc2 = None):
        self.logging("makePointFeature: making new point for %s %s" % (
                g.getAttribute( 'BUS' ),g.getAttribute( 'TIMESTAMP' )))
        f = fmeobjects.FMEFeature()
        for a in g.getAllAttributeNames():
            f.setAttribute( a, g.getAttribute( a ))
        
        if apc2:
            self.logging("makePointFeature: interpolating")
            x1,y1 = apc1.getCoordinate(0)
            x2,y2 = apc2.getCoordinate(0)
            timestamp1 = float(apc1.getAttribute( 'TIMESTAMP' ))
            timestamp2 = float(apc2.getAttribute( 'TIMESTAMP' ))
            timestamp0 = float(g.getAttribute( 'TIMESTAMP' ))

            timeRatio = (timestamp0 - timestamp1) / (timestamp2 - timestamp1)
            x = (timeRatio * (x2 - x1)) + x1
            y = (timeRatio * (y2 - y1)) + y1

            f.setCoordSys( apc1.getCoordSys() )
            f.setGeometryType( apc1.getGeometryType() )
            f.addCoordinate( x, y )
            f.setAttribute( '_STATUS', 1)
            f.setAttribute( 'POINTCALC', 1)

        else:
            self.logging("makePointFeature: not interpolating")
            f.setCoordSys( apc1.getCoordSys() )
            f.setGeometryType( apc1.getGeometryType() )
            f.setGeometry( apc1.getGeometry() )
            f.setAttribute( '_STATUS', 1)
            f.setAttribute( 'POINTCALC', 0)
        
        return f
        
    def makeNullFeature( self, g ):
        g.setAttribute( '_STATUS', 0)
        g.setAttribute( 'POINTCALC', 0)
        return g

        
##############################################################################       
class FMEInterpolatePoints3(object):
    def __init__(self):
        self.apcData = {}
        self.apcTimestamps = {}
        self.gfiData = []
        #self.metaArray = {'GFI':self.gfiData, 'APC':self.apcData}
        
        self.logger = fmeobjects.FMELogFile()

    def logging(self, m):
        if LOGIT: self.logger.logMessageString( str(m) )

        
    def input(self,f):
        if f.getAttribute('_SOURCE') == 'GFI':
            self.gfiData.append( f )
        elif f.getAttribute('_SOURCE') == 'APC':
            busID = int( f.getAttribute('BUSID') )
            if busID not in self.apcData.keys(): 
                self.apcData[ busID ] = []
                self.apcTimestamps[ busID ] = []
            self.apcData[ busID ].append( f )
            self.apcTimestamps[ busID ].append( int(f.getAttribute('TIMESTAMP')) )
        else:
            self.logging("FMEmatchAPC: Unknown feature.")

            

    def close(self):
        self.logging("FMEInterpolatePoints2: Processing...")
        self.logging("FMEInterpolatePoints2: gfiData %s" % len(self.gfiData) )
        self.logging("FMEInterpolatePoints2: apcData %s" % len(self.apcData) )
        
        for gfi in self.gfiData:
            self.logging("\nFMEInterpolatePoints2: working on %s %s" % (
                    gfi.getAttribute( 'BUS' ),gfi.getAttribute( 'TIMESTAMP' )))
            
            busID = int( gfi.getAttribute('BUS') )
            timestamp = int( gfi.getAttribute( 'TIMESTAMP' ))
            i = bisect.bisect_right( self.apcTimestamps[ busID ], timestamp )
            
            if i == 0:  # time is before first APC timestamp
                self.pyoutput( self.nullFeature( gfi) )
            elif timestamp == self.apcTimestamps[ busID ][ i -1 ]: 
                self.pyoutput( self.copyCoordinates( gfi, i -1 , busID ))
            elif i < len( self.apcTimestamps[ busID ]): 
                self.pyoutput( self.interpolateCoordinates( gfi, i, busID ))
            else:
                self.pyoutput( self.nullFeature( gfi) )

                
    def interpolateCoordinates( self, g, i, busID ):
        self.logging("makePointFeature: making new point for %s %s" % (
                g.getAttribute( 'BUS' ),g.getAttribute( 'TIMESTAMP' )))

        x1,y1 = self.apcData[busID][i-1].getCoordinate(0)
        x2,y2 = self.apcData[busID][i].getCoordinate(0)
        timestamp1 = float(self.apcData[busID][i-1].getAttribute( 'TIMESTAMP' ))
        timestamp2 = float(self.apcData[busID][i].getAttribute( 'TIMESTAMP' ))
        timestamp0 = float(g.getAttribute( 'TIMESTAMP' ))
        
        if abs( timestamp0 - timestamp2) > MAXTIMEDIFF or abs( timestamp0 - timestamp1) > MAXTIMEDIFF:
            g.setAttribute( '_STATUS', 0)
        else:
            timeRatio = (timestamp0 - timestamp1) / (timestamp2 - timestamp1)
            x = (timeRatio * (x2 - x1)) + x1
            y = (timeRatio * (y2 - y1)) + y1
            
            g.setAttribute( 'LATITUDE', y )
            g.setAttribute( 'LONGITUDE',x )
            g.setAttribute( 'POINTCALC', 1)
            g.setAttribute( 'TIMEDIFF', (timestamp2 - timestamp1)/2.0 )
            g.setAttribute( '_STATUS', 1)        
        return g


    def nullFeature( self, g ):
        self.logging("nullFeature: no point for %s %s" % (
                g.getAttribute( 'BUS' ),g.getAttribute( 'TIMESTAMP' )))
        g.setAttribute( '_STATUS', 0)
        return g
        

    def copyCoordinates( self, g, i, busID ):
        self.logging("copyCoordinates: copying point for %s %s" % (
                g.getAttribute( 'BUS' ),g.getAttribute( 'TIMESTAMP' )))
        x,y = self.apcData[busID][i].getCoordinate(0)
        g.setAttribute( 'LATITUDE', y )
        g.setAttribute( 'LONGITUDE',x )
        g.setAttribute( 'POINTCALC', 0)
        g.setAttribute( 'TIMEDIFF', 0)
        g.setAttribute( '_STATUS', 1)
        return g
        
'''
        if bool(set(NEEDED_ATTRIBUTES) & set(f.getAllAttributeNames())) :
            points = {}
            points['timestamp'] = map( lambda i: float(f.getAttribute("APC{%d}.TIMESTAMP" % i)), range(0,2))
            points['timestamp'].append( float(f.getAttribute('TIMESTAMP')) )
            points['lat'] = map( lambda i: float(f.getAttribute("APC{%d}.LAT" % i)), range(0,2))
            points['lon'] = map( lambda i: float(f.getAttribute("APC{%d}.LON" % i)), range(0,2))
            
            timeRatio = (points['timestamp'][2] - points['timestamp'][0]) / (points['timestamp'][1] - points['timestamp'][0])
            pLat,pLon = map( lambda p: (timeRatio * (p[1] - p[0])) + p[0], (points['lat'],points['lon']) )
            
            f.setAttribute('LONGITUDE',pLon)
            f.setAttribute('LATITUDE',pLat)
            f.setAttribute('HAVECOORDINATES',1)
        else:
            f.setAttribute('HAVECOORDINATES',0)
        self.pyoutput(f)
'''

                

                
