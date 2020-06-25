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
                hEvents.append( Event(e.origins[0]['latitude'],
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
        vectorDistances = np.zeros((len(hEvents), 7))

        # Calculate Euclidean distances
        i = 0
        for e in hEvents:

            sphereDist = haversine((e.lat, e.lon), (self.event.lat, self.event.lon)) * 1000
            depthDist = (e.depth - self.event.depth)
            
            euclideanDist = np.sqrt(sphereDist**2 + depthDist**2)
            
            # Store the calculated information
            vectorDistances[i, :] = [i, euclideanDist, sphereDist, depthDist, 
                                     e.strike, e.dip, e.rake
                                    ]
            i=i+1

        # Sort by the distance by 'euclideanDist' field
        distSorted = vectorDistances[vectorDistances[:,1].argsort()]
        
        # Increase distance threshold till the minimum k-neighbors be reached
        kmin = self.setup['k']['min']
        growthrate = self.setup['distance']['growthrate']
        threshold = self.setup['distance']['threshold']
        
        while True:

            # Sort and filter with the new threshold value
            distFiltered = distSorted[np.where(distSorted[:,1] <= threshold)]
            distFiltered = distFiltered[0:self.setup['k']['max'], :]
            
            k = len(distFiltered)
            
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
        
        # Return the JSON file!!!!
        return cmts
