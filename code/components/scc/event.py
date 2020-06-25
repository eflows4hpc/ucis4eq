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

from bson.json_util import dumps
from bson import ObjectId

# Third parties
from flask import jsonify

# Internal
from ucis4eq.misc import config
from ucis4eq.scc import microServiceABC

################################################################################
# Methods and classes

class EventRegistration(microServiceABC.MicroServiceABC):

    # Initialization method
    def __init__(self):
        """
        Initialize the eventDispatcher component implementation    
        """
        
        # Select the database
        self.db = config.database

    # Service's entry point definition
    @config.safeRun
    def entryPoint(self, body):
        """
        Deal with a new earthquake event
        """
        # Insert each source
        record_created = self.db.EQSources.insert(body['sources'])
        
        records = []
        # Store the set of events
        field = {}
        field['alerts'] = body['alerts']
        field['sources_id'] = record_created
        field['uuid'] = body['uuid']
        event = self.db.EQEvents.insert(field)

        # Return list of Id of the newly created item
        return jsonify(result = str(event), response = 201)            
            
class EventRegion(microServiceABC.MicroServiceABC):

    # Initialization method
    def __init__(self):
        """
        Initialize the eventDispatcher component implementation    
        """
        
        # Select the database
        self.db = config.database
        
        # Initialize output results
        self.regions = {}

    # Service's entry point definition
    @config.safeRun
    def entryPoint(self, body):
        """
        Figure out the region which the incoming EQ event belong 
        """                    
        # Retrieve the event's complete information 
        eid = body['event']

        # Build the pipeline for obtaining the AVG of the set of alerts
        avgPosPipeline = [
            { 
              "$match" : {
                "_id": ObjectId(eid)
              }
            },
            {
              "$unwind": "$alerts"
            },
            {
              "$group": {
                "_id": ObjectId(eid),
                "avgLatitude": { "$avg": "$alerts.latitude" },
                "avgLongitude": { "$avg": "$alerts.longitude" }
              }
            }
         ]

        # It assumed that just one result is obtained
        for event in self.db['EQEvents'].aggregate(avgPosPipeline):
            # Build the pipeline for obtaining the regon from a concrete given 
            # event
            regionPipeline = [
               { 
                 "$project" : {
                    "_id" : {
                        "$toString": "$_id"
                    },
                    "id": 1,
                    "mlat" : "$model.geometry.min_latitude",
                    "Mlat" : "$model.geometry.max_latitude",
                    "mlon" : "$model.geometry.min_longitude",
                    "Mlon" : "$model.geometry.max_longitude" 
                 }
               },
               { 
                 "$match" : {
                   "$and" : [
                    {"mlat": {"$lte": event["avgLatitude"]}},
                    {"Mlat": {"$gte": event["avgLatitude"]}},
                    {"mlon": {"$lte": event["avgLongitude"]}},
                    {"Mlon": {"$gte": event["avgLongitude"]}}
                   ]
                 }
               }
            ]
            
            #for region in self.db['Regions'].aggregate(regionPipeline): 
            self.regions = list(self.db['Regions'].aggregate(regionPipeline))
        
        region = None
        if self.regions:
            region = self.regions[0]
        
        # Return list of Id of the newly created item
        return jsonify(result = region, response = 201)
