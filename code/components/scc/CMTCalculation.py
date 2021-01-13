#!/usr/bin/env python3
#
# Events dispatcher
# This module is part of the Smart Center Control (SSC) solution
#
# Author:  Juan Esteban Rodríguez, Josep de la Puente
# Contact: juan.rodriguez@bsc.es, josep.delapuente@bsc.es
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

################################################################################
# Module imports
# System
import sys
import traceback
import json
from bson import ObjectId

# Third parties
import obspy
import numpy as np
from flask import jsonify
from haversine import haversine
from sklearn.cluster import DBSCAN 
from sklearn.preprocessing import StandardScaler 
from sklearn.preprocessing import normalize 
from sklearn.decomposition import PCA 
from sklearn.neighbors import NearestNeighbors
from kneed import KneeLocator

# Internal
from ucis4eq.misc import config
from ucis4eq.scc import microServiceABC

################################################################################
# Methods and classes

class Event():
    
    # Initialization method
    def __init__(self, lat, lon, depth, mag, strike=0., dip=0., rake=0.):
        """
        Initialize the event instance    
        """
        self.lat = lat
        self.lon = lon
        self.depth = depth
        self.mag = mag
        self.strike = strike
        self.dip = dip
        self.rake = rake

    def __repr__(self):
        return "Event()"
         
    def __str__(self):
        return "Strike: " + str(self.strike) + " Dip: " + str(self.dip) + " Rake: " + str(self.rake)
        
        
    def toJSON(self):
        return {"strike": str(self.strike), 
                "dip": str(self.dip),
                "rake": str(self.rake)}
        

class CMTInputs(microServiceABC.MicroServiceABC):
    
    # Attibutes 
    setup = {}             # Setup for the CMT calculation
    event = None           # Input event
    
    # Initialization method
    def __init__(self, setup):
        """
        Initialize the CMT Preprocess component implementation
        """
            
        # Read the input catalog from file
        with open(setup, 'r') as f:
            self.setup = json.load(f)
                        
        # Select the database
        self.db = config.database
        
    # Service's entry point definition
    def entryPoint(self, body):
        """
        Generate a CMT input for a posterior CMT calculation
        """
        try:
            # TODO: This part should be done by the workflow manager
            # For each new incomming event 
            inputParameters = self.setup        
                
            # Retrieve the event's complete information 
            event = self.db.EQEvents.find_one({"_id": ObjectId(body['event'])})
            
            # Add the current event
            inputParameters.update({
                                    "event": {
                                        "_id": body['event'],
                                        "alerts": event['alerts'],
                                        }
                                   })
            
            return jsonify(result = inputParameters, response = 201)
        
        except Exception as error:
            # Error while trying to create the resource
            config.printException()

            # Return error code and message
            return jsonify(result = str(error), response = 501)

class CMTCalculation(microServiceABC.MicroServiceABC):
    
    # Attibutes 
    setup = {}             # Setup for the CMT calculation
    event = None           # Input event
    
    # Initialization method
    def __init__(self, catalog):
        """
        Initialize the CMT statistical component implementation
        """
            
        # Read the input catalog from file
        self.cat = obspy.read_events(catalog)
        
    # Service's entry point definition
    def entryPoint(self, body):
        """
        Calculate a CMT approximation from historical earthquake events
        """
        try:
            # Configure the component
            self.setup = body['setup']
            
            # Check input parameters 
            #if self.setup['k']['min'] > self.setup['k']['max']:
            #   raise Exception('k-min value must be >= k-max')
                
            if self.setup['distance']['growthrate'] <= 1:
                raise Exception('The growthrate value must be > 1')
            
            if self.setup['distance']['threshold'] <= 0:
                raise Exception('Threshold must be > 0')
            
            # Set an input event with an unknown CMT
            e = body['event']
            self.event = Event(e['latitude'], 
                               e['longitude'], 
                               e['depth'], 
                               e['magnitude']
                              )

            return jsonify(result = self._getFocalMechanism(), response = 201)
                    
        except Exception as error:
            # Error while trying to create the resource
            config.printException()

            # Return error code and message
            return jsonify(result = str(error), response = 501)
                        
    def _getFocalMechanism(self):
        """
        This method obtains the Focal Mechanism from an historical provided 
        earthquakes events
        """
    
        # Retrieve the historical information from a past events catalog
        hEvents = []
        # For each event in the catalog, extract the FM, Mg and position
        # (only for events which mg >= MagnitudThreshold)
        for e in self.cat:
            if  e.magnitudes[0]['mag'] >= self.setup['magnitudethreshold']:
                fm = e.focal_mechanisms[0]['nodal_planes'].nodal_plane_1 
                hEvents.append(Event(e.origins[0]['latitude'],
                                     e.origins[0]['longitude'],
                                     e.origins[0]['depth'],
                                     e.magnitudes[0]['mag'],
                                     fm.strike, 
                                     fm.dip,
                                     fm.rake
                                    )
                             )
                        
        # Print the total number of events in the catalog and known focal
        # mechanisms
        #print("Total number of events: " + str(len(hEvents)))

        # Initialization
        vectorDistances = np.zeros((len(hEvents), 11))
        #vecMagMediana[contEventosThresholdDist,kk] = vecMagMed[kk]
        #latiMediana[contEventosThresholdDist,kk] = latiMed[kk]
        #longMediana[contEventosThresholdDist,kk] = longMed[kk]
        #deptMediana[contEventosThresholdDist,kk] = deptMed[kk]   
        #vecFocalMecanismMed[contEventosThresholdDist,kk,:] = mt2[kk,:]

        # Calculate Euclidean distances
        i = 0
        for e in hEvents:

            sphereDist = haversine((e.lat, e.lon), (self.event.lat, self.event.lon)) * 1000
            depthDist = (e.depth - self.event.depth)
                        
            euclideanDist = np.sqrt(sphereDist**2 + depthDist**2)
            # Store the calculated information
            vectorDistances[i, :] = [i, euclideanDist, sphereDist, depthDist, e.strike, e.dip, e.rake,  e.mag, e.depth, e.lat, e.lon]
            i=i+1

        # Sort by the distance by 'euclideanDist' field
        distSorted = vectorDistances[vectorDistances[:,1].argsort()]
        
        # Increase distance threshold till the minimum k-neighbors be reached
        kmin = self.setup['k']['min']
        growthrate = self.setup['distance']['growthrate']
        threshold = self.setup['distance']['threshold']*1000
        
        while True:

            # Sort and filter with the new threshold value
            # print('distSorted[:,1] <= threshold',distSorted[:,1],' <= ' ,threshold)
            distFiltered = distSorted[np.where(distSorted[:,1] <= threshold)]
                  
            # distFiltered = distFiltered[0:self.setup['k']['max'], :]
            
            k = len(distFiltered)
            vecMagNeig = distFiltered[0:k,7]            
            vecDepNeig = distFiltered[0:k,8]
            vecLatNeig = distFiltered[0:k,9]
            vecLonNeig = distFiltered[0:k,10]
            vecStrikeNeig = distFiltered[0:k,4]
            vecDipNeig = distFiltered[0:k,5]
            vecRakeNeig = distFiltered[0:k,6]
            
            # Check if the the number of neighbors found was enough
            if (kmin <= k) or (k == len(distSorted)):
                break
            
            # Increase the search threshold
            threshold = threshold * growthrate

        #print("Neighbors found:", str(k), "Final threshold:", str(threshold), "meters")
        
        
        # Check if the algorithm can continue
        if k < kmin:
            raise Exception('{}-neighbors found while the minimum required is {}'.format(k, kmin))
        
        # Calculate the median Focal Mechanism
        self.event.strike = np.percentile(distFiltered[0:k, 4], 50, interpolation = 'midpoint')
        self.event.dip = np.percentile(distFiltered[0:k, 5], 50, interpolation = 'midpoint')
        self.event.rake = np.percentile(distFiltered[0:k, 6], 50, interpolation = 'midpoint')
        
        
        # Build the list of CMTs for the current events
        cmts = {"Median": self.event.toJSON()}
        #print("[Median] --> " + str(self.event))
        
        for i in range(0,self.setup['output']['focalmechanisms']):
            #hEvents[distFiltered[0:self.setup['output']['focalmechanisms'], 0]]:
            name = "k-" + str(i+1) +  ""
            e = hEvents[int(distFiltered[i, 0])]
            #print("[" + name + "]"+ " --> " + str(e))
            cmts.update({name: e.toJSON()})                  
            
        ########################################    
        # Cluster results 
        X_results = np.zeros((k,4))
        distancesEvents = np.zeros(k)
        cont = -1
        dataCoordinatesCentroidEvent = (self.event.lon, self.event.lat) 
        profEvent = self.event.depth
        hEventsCluster = []
         
        for kk in range(0,k):
            if vecMagNeig[kk] != 0:
                cont += 1
                X_results[cont,0] = vecStrikeNeig[kk]
                X_results[cont,1] = vecDipNeig[kk]
                X_results[cont,2] = vecRakeNeig[kk]                  
                distEpicentral =  haversine(dataCoordinatesCentroidEvent, (vecLatNeig[kk],vecLonNeig[kk]))*1000
               # print('vecDepNeig[kk]',vecDepNeig[kk])
                distancesEvents[cont] = np.sqrt(distEpicentral**2 + (profEvent - vecDepNeig[kk])**2)
                X_results[cont, 3] = distancesEvents[cont] 
        
        ## DBSCAN hyperparameters 
        nearest_neighbors = NearestNeighbors(n_neighbors=2)
        neighbors = nearest_neighbors.fit(X_results[0:cont+1,:])
        distances, indices = neighbors.kneighbors(X_results[0:cont+1,:])
        distances = np.sort(distances[:,1], axis=0)
        i = np.arange(len(distances))
        knee = KneeLocator(i, distances, S=1, curve='convex', direction='increasing', interp_method='polynomial')
        clustering = DBSCAN(eps = distances[knee.knee], min_samples=2).fit(X_results[0:cont+1,:])
        labels = clustering.labels_
        counts = np.bincount(labels[labels >= 0])
        top_labels = np.argsort(-counts)[:2]
        n_clusters_ = len(set(labels)) 
       # print('n_clusters_',n_clusters_)
        X_resultsCluster = np.zeros((cont+1,9))
        X_resultsCluster[:,0:4] = X_results[0:cont+1,:]
        X_resultsCluster[:,4] = clustering.labels_        
        vecNumElementsCluster = np.zeros(cont+1)
        contCluster = 0
        contNumberCluster = -1
        for iCluster in np.arange(min(X_resultsCluster[:,4]),max(X_resultsCluster[:,4])+1):
          contNumberCluster += 1
          for kk in range(0,cont+1):
            if X_resultsCluster[kk,4] == iCluster:
              contCluster += 1
          vecNumElementsCluster[contNumberCluster] = contCluster
          contCluster = 0    
   
        percentageEachCluster = np.zeros(contNumberCluster+1)
        sumTotEvents = sum(vecNumElementsCluster[0:contNumberCluster+1])
  
        for ij in np.arange(contNumberCluster+1):
          percentageEachCluster[ij] = vecNumElementsCluster[ij]/sumTotEvents
        
        contNumberCluster = -1
        for iCluster in np.arange(min(X_resultsCluster[:,4]),max(X_resultsCluster[:,4])+1):
            contNumberCluster += 1
            for kk in range(0,cont+1):               
                if X_resultsCluster[kk,4] == iCluster:
                    X_resultsCluster[kk,5] = percentageEachCluster[contNumberCluster]
                    X_resultsCluster[kk,6] = vecLatNeig[kk]
                    X_resultsCluster[kk,7] = vecLonNeig[kk]
                    X_resultsCluster[kk,8] = vecDepNeig[kk]
                    
        # For each cluster obtained the median and the mean of the FM considering each angle as independent variable. Compare with the k-closest neighbors
                    
        X_resultsSortCluster = X_resultsCluster[X_resultsCluster[0:cont+1,4].argsort()]  
      
        VecTempClusterMean = np.zeros((contNumberCluster+1,3))
        VecTempClusterStd = np.zeros((contNumberCluster+1,3))
        VecTempClusterMedian = np.zeros((contNumberCluster+1,3)) 
        VecCentroides = np.zeros((contNumberCluster+1,3))
        VecCentroidesStd =  np.zeros((contNumberCluster+1,3))
        contTmp = -1
        contClustMean = -1
    
        for jj in np.arange(contNumberCluster+1):           
            #print('jj',jj)
            contTmpIni = int(contTmp + 1)
            contTmpFin = int(contTmpIni + vecNumElementsCluster[jj]-1)
            VecTempClusterMean[jj,0] = np.mean(X_resultsSortCluster[contTmpIni:contTmpFin+1,0])  #mean Strike,Dip,Rake Cluster
            VecTempClusterStd[jj,0] = np.std(X_resultsSortCluster[contTmpIni:contTmpFin+1,0])  #mean Strike,Dip,Rake Cluster
            VecTempClusterMedian[jj,0] = np.percentile(X_resultsSortCluster[contTmpIni:contTmpFin+1,0], 50, interpolation = 'midpoint')
            VecTempClusterMean[jj,1] = np.mean(X_resultsSortCluster[contTmpIni:contTmpFin+1,1])  #mean Strike,Dip,Rake Cluster
            VecTempClusterStd[jj,1] = np.std(X_resultsSortCluster[contTmpIni:contTmpFin+1,1])  #mean Strike,Dip,Rake Cluster
            VecTempClusterMedian[jj,1] = np.percentile(X_resultsSortCluster[contTmpIni:contTmpFin+1,1], 50, interpolation = 'midpoint')
            VecTempClusterMean[jj,2] = np.mean(X_resultsSortCluster[contTmpIni:contTmpFin+1,2])  #mean Strike,Dip,Rake Cluster
            VecTempClusterStd[jj,2] = np.std(X_resultsSortCluster[contTmpIni:contTmpFin+1,2])  #mean Strike,Dip,Rake Cluster
            VecTempClusterMedian[jj,2] = np.percentile(X_resultsSortCluster[contTmpIni:contTmpFin+1,2], 50, interpolation = 'midpoint')
            VecCentroides[jj,0] = np.mean(X_resultsSortCluster[contTmpIni:contTmpFin+1,6]) #Latitude
            VecCentroides[jj,1] = np.mean(X_resultsSortCluster[contTmpIni:contTmpFin+1,7]) #Longitude
            VecCentroides[jj,2] = np.mean(X_resultsSortCluster[contTmpIni:contTmpFin+1,8]) #Depth
            VecCentroidesStd[jj,0] = np.std(X_resultsSortCluster[contTmpIni:contTmpFin+1,6]) #Latitude
            VecCentroidesStd[jj,1] = np.std(X_resultsSortCluster[contTmpIni:contTmpFin+1,7]) #Longitude
            VecCentroidesStd[jj,2] = np.std(X_resultsSortCluster[contTmpIni:contTmpFin+1,8]) #Depth  
            contTmp = contTmpFin            
            contClustMean = contClustMean + 1
            hEventsCluster.append(Event(VecCentroides[jj,0],
                                 VecCentroides[jj,1],
                                 VecCentroides[jj,2],    
                                 0.0,
                                 VecTempClusterMean[jj,0],
                                 VecTempClusterMean[jj,1],
                                 VecTempClusterMean[jj,2]
                                 )
                             )
            name = "ClustMean-" + str(jj+1) +  ""
            e = hEventsCluster[int(contClustMean)]
            #print("[" + name + "]"+ " --> " + str(e))
            cmts.update({name: e.toJSON()})                                   
            contClustMean = contClustMean + 1
            hEventsCluster.append(Event(VecCentroides[jj,0],
                                 VecCentroides[jj,1],
                                 VecCentroides[jj,2],    
                                 0.0,
                                 VecTempClusterMedian[jj,0],
                                 VecTempClusterMedian[jj,1],
                                 VecTempClusterMedian[jj,2]
                                 )
                             )            
            name = "ClustMedian-" + str(jj+1) +  ""
            e = hEventsCluster[int(contClustMean)]
            #print("[" + name + "]"+ " --> " + str(e))
            cmts.update({name: e.toJSON()})               
            print('cmts',cmts)     
            
           
        # Return the JSON file!!!!
        
        return cmts
      
