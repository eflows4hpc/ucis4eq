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
from obspy.imaging.beachball import aux_plane

# Internal
import ucis4eq
from ucis4eq.misc import config, microServiceABC
from ucis4eq.dal import staticDataMap

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
        
@staticDataMap.build
class CMTInputs(microServiceABC.MicroServiceABC):
    
    # Attibutes 
    setup = {}             # Setup for the CMT calculation
    event = None           # Input event
    
    # Initialization method
    def __init__(self):
        """
        Initialize the CMT Preprocess component implementation
        """
        
    # Service's entry point definition
    @config.safeRun
    def entryPoint(self, body):
        """
        Generate a CMT input for a posterior CMT calculation
        """
        # Read the input catalog from file
        with open(self.fileMapping["configCMT"], 'r') as f:
            inputParameters = json.load(f)

        # TODO: This part should be done by the workflow manager
                    
        # Retrieve the event's complete information 
        event = ucis4eq.dal.database.EQEvents.find_one({"_id": ObjectId(body['event'])})
        
        # Add the current event
        inputParameters.update({
                                "event": {
                                    "_id": body['event'],
                                    "alerts": event['alerts'],
                                    }
                               })
        
        return jsonify(result = inputParameters, response = 201)

@staticDataMap.build
class CMTCalculation(microServiceABC.MicroServiceABC):
    
    # Attibutes 
    setup = {}             # Setup for the CMT calculation
    event = None           # Input event
    
    # Initialization method
    def __init__(self):
        """
        Initialize the CMT statistical component implementation
        """
                    
    # Service's entry point definition
    @config.safeRun
    def entryPoint(self, body):
        """
        Calculate a CMT approximation from historical earthquake events
        """
        # Read the input catalog from file
        catalogName="SPUD_QUAKEML_bundle_2019-10-31"
        self.cat = obspy.read_events(self.fileMapping[catalogName])
                
        # Configure the component
        self.setup = body['setup']
        
        # Check input parameters 
        if self.setup['k']['min'] > self.setup['k']['max']:
            raise Exception('k-min value must be >= k-max')
            
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
                hEvents.append(Event(e.origins[1]['latitude'],
                                     e.origins[1]['longitude'],
                                     e.origins[1]['depth'],
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
        #print('self.event.depth',self.event.depth,flush=True)
        for e in hEvents:             
            #print('i=',i,flush=True)
            sphereDist = haversine((e.lat, e.lon), (self.event.lat, self.event.lon)) * 1000
            #print('e.depth',e.depth,flush=True)  ## TODOOOOOOO Check UNITS
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
            #print('distSorted[:,1] <= threshold',distSorted[:,1],' <= ' ,threshold)
            distFiltered = distSorted[np.where(distSorted[:,1] <= threshold)]
            #print("distFiltered", distFiltered)      
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
        
        AuxNodalPlanes = []
        contNodalPlanes = -1
        # Build the list of CMTs for the current events
        cmts = {"Median": self.event.toJSON()}
        aux_plane_median = aux_plane(self.event.strike, self.event.dip, self.event.rake)
        AuxNodalPlanes.append(Event(0.0,0.0,0.0,0.0,aux_plane_median[0],aux_plane_median[1],aux_plane_median[2]))  
        contNodalPlanes += 1
        e = AuxNodalPlanes[contNodalPlanes]
        cmts.update({"Median_AuxPlane" : e.toJSON()})
        for i in range(0,self.setup['output']['focalmechanisms']):
            #hEvents[distFiltered[0:self.setup['output']['focalmechanisms'], 0]]:
            name = "k-" + str(i+1) +  ""             
            e = hEvents[int(distFiltered[i, 0])]
            #print("[" + name + "]"+ " --> " + str(e))
            cmts.update({name: e.toJSON()})
            aux_plane_k = aux_plane(distFiltered[i, 4],distFiltered[i, 5],distFiltered[i, 6])
            AuxNodalPlanes.append(Event(distFiltered[i,9],distFiltered[i,10],distFiltered[i,8],distFiltered[i,7],aux_plane_k[0],aux_plane_k[1],aux_plane_k[2]))  
            contNodalPlanes += 1
            e = AuxNodalPlanes[contNodalPlanes]
            cmts.update({"k-" + str(i+1) + "_AuxPlane" : e.toJSON()})           
            
        ########################################    
        # Cluster results 
        X_results = np.zeros((k,4))
        distancesEvents = np.zeros(k)
        cont = -1
        dataCoordinatesCentroidEvent = (self.event.lat,self.event.lon) 
        profEvent = self.event.depth
        #print('profEvent',profEvent,flush=True)
        hEventsCluster = []
         
        for kk in range(0,k):
            if vecMagNeig[kk] != 0:
                cont += 1
                X_results[cont,0] = vecStrikeNeig[kk]
                X_results[cont,1] = vecDipNeig[kk]
                X_results[cont,2] = vecRakeNeig[kk]                  
                distEpicentral =  haversine(dataCoordinatesCentroidEvent, (vecLatNeig[kk],vecLonNeig[kk]))
                #print('distEpicentral',distEpicentral)
                #print('vecDepNeig[kk]',vecDepNeig[kk])
                #print('profEvent/1000',profEvent/1000,flush=True)
                distancesEvents[cont] = np.sqrt(distEpicentral**2 + ((profEvent/1000) - (vecDepNeig[kk]/1000))**2)
                #print('distancesEvents[cont]',distancesEvents[cont],flush=True)
                X_results[cont, 3] = distancesEvents[cont] 
                #print('X_results[cont,:]',  X_results[cont,:],flush=True)
        
        ## DBSCAN hyperparameters 
        nearest_neighbors = NearestNeighbors(n_neighbors=2)
        neighbors = nearest_neighbors.fit(X_results[0:cont+1,:])
        distances, indices = neighbors.kneighbors(X_results[0:cont+1,:])
        distances = np.sort(distances[:,1], axis=0)
        i = np.arange(len(distances))
        knee = KneeLocator(i, distances, S=1, curve='convex', direction='increasing', interp_method='polynomial')
        clustering = DBSCAN(eps = distances[knee.knee], min_samples=2).fit(X_results[0:cont+1,:])
        labels = clustering.labels_
        #print('labels',labels,flush=True)
        counts = np.bincount(labels[labels >= 0])
        top_labels = np.argsort(-counts)[:2]
        n_clusters_ = len(set(labels)) 
        #print('n_clusters_',n_clusters_,flush=True)
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
            #print('contTmpIni',contTmpIni,flush=True)
            #print('contTmpFin',contTmpFin,flush=True)  
            #for ij in np.arange(contTmpIni,contTmpFin+1):
            #  print('X_resultsSortCluster[int(ij),:]',X_resultsSortCluster[int(ij),:],flush=True) 
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
            ## Mean Clustering Solutions
            #contClustMean = contClustMean + 1
            #hEventsCluster.append(Event(VecCentroides[jj,0],
             #                    VecCentroides[jj,1],
             #                   VecCentroides[jj,2],    
             #                   0.0,
             #                    VecTempClusterMean[jj,0],
             #                    VecTempClusterMean[jj,1],
             #                    VecTempClusterMean[jj,2]
             #                    )
             #                )
            #name = "ClustMean-" + str(jj+1) +  ""
            #e = hEventsCluster[int(contClustMean)]            
            #print("[" + name + "]"+ " --> " + str(e))
            #cmts.update({name: e.toJSON()})        
            #######
            
            ## Median Clustering Solution
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
            
            ## AuxPlanes_Median Clustering Solution
            aux_plane_Clust = aux_plane(VecTempClusterMedian[jj,0],VecTempClusterMedian[jj,1],VecTempClusterMedian[jj,2])
            AuxNodalPlanes.append(Event(VecCentroides[jj,0],VecCentroides[jj,1],VecCentroides[jj,2],0.0,aux_plane_Clust[0],aux_plane_Clust[1],aux_plane_Clust[2]))             
            contNodalPlanes += 1
            e = AuxNodalPlanes[contNodalPlanes]
            cmts.update({"ClustMedian-" + str(jj+1) + "_AuxPlane" : e.toJSON()})
          
        print('cmts',cmts,flush=True)               
           
        # Return the JSON file!!!!
        
        return cmts
      
