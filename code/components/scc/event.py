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
import os
import traceback
import json
import requests
import math

from shapely.geometry import mapping, shape
from shapely.prepared import prep
from shapely.geometry import Point

from bson.json_util import dumps
from bson import ObjectId
from urllib.request import urlopen

# Third parties
from flask import jsonify

# Internal
from ucis4eq.misc import config, microServiceABC
import ucis4eq as ucis4eq
from ucis4eq.dal import staticDataMap
import ucis4eq.dal as dal

################################################################################
# Methods and classes
class EventRegistration(microServiceABC.MicroServiceABC):

    # Initialization method
    def __init__(self):
        """
        Initialize the eventDispatcher component implementation    
        """
        
        # Select the database
        self.db = ucis4eq.dal.database

    # Service's entry point definition
    @config.safeRun
    def entryPoint(self, body):
        """
        Deal with a new earthquake event
        """
        # Insert each source
        record_created = self.db.TriggerInfo.insert(body['sources'])
        records = []
        # Store the set of events
        field = {}
        field['alerts'] = body['alerts']
        field['sources_id'] = record_created
        field['uuid'] = body['uuid']
        field['state'] = 'LAUNCHED'
        event = self.db.Requests.insert(field)
        
        print("Request Id. [" + str(event) + "] registered for event [" + \
             field['uuid'] + "]", flush=True)

        # Return list of Id of the newly created item
        return jsonify(result = str(event), response = 201)
        
        
################################################################################
# Methods and classes
class EventSetState(microServiceABC.MicroServiceABC):

    # Initialization method
    def __init__(self):
        """
        Initialize the eventDispatcher component implementation    
        """
        
        # Select the database
        self.db = ucis4eq.dal.database

    # Service's entry point definition
    @config.safeRun
    def entryPoint(self, body):
        """
        Update the status of an earthquake event
        """

        event = self.db.Requests.update({'_id': ObjectId(body['id'])},
            {'$set': {"state": body['state']}})

        # Return list of Id of the newly created item
        return jsonify(result = str(event), response = 201)

class EventDomains(microServiceABC.MicroServiceABC):

    # Initialization method
    def __init__(self):
        """
        Initialize the eventDispatcher component implementation    
        """
        
        # Select the database
        self.db = ucis4eq.dal.database
        
        # Initialize output results
        self.domains = {}

    # Service's entry point definition
    @microServiceABC.MicroServiceABC.runRegistration
    def entryPoint(self, body):
        """
        Figure out the set of domains which the incoming EQ event belong
        """                    
        # Retrieve the event's complete information 
        rid = body['id']
        
        # Build the pipeline for obtaining the AVG of the set of alerts
        avgPosPipeline = [
            { 
              "$match" : {
                "_id": ObjectId(rid)
              }
            },
            {
              "$unwind": "$alerts"
            },
            {
              "$group": {
                "_id": ObjectId(rid),
                "avgLatitude": { "$avg": "$alerts.latitude" },
                "avgLongitude": { "$avg": "$alerts.longitude" }
              }
            }
         ]

        # It assumed that just one result is obtained
        for event in self.db['Requests'].aggregate(avgPosPipeline):
            # Build the pipeline for obtaining the regon from a concrete given 
            # event
            regionPipeline = [
               {
                 "$project" : {
                    "_id" : {
                        "$toString": "$_id"
                    },
                    "id": 1,
                    "region": 1,
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
            self.domains = list(self.db['Domains'].aggregate(regionPipeline))
                
        region = None
        if self.domains:
            region = self.domains[0]
                    
        # Return list of Id of the newly created item
        return jsonify(result = self.domains, response = 201)

@staticDataMap.build
class EventCountry(microServiceABC.MicroServiceABC):

    # Initialization method
    def __init__(self):
        """
        Initialize the eventDispatcher component implementation    
        """
         
    # Service's entry point definition
    @microServiceABC.MicroServiceABC.runRegistration
    def entryPoint(self, body):
        """
        Figure out the country which the incoming EQ event belong 
        """
        
        alert = body['alerts'][0];
        country = self._getPlace(alert['latitude'], alert['longitude'])

        # Return list of Id of the newly created item
        return jsonify(result = country, response = 201)
        
    def _getPlace(self, lat, lon):
                
        ###################################################
        # TODO: This is not a good solution at all, please check!!!!!!!!!1
        ###################################################
        
        # TODO: Download the countries.geojson to save in local 
        # data = requests.get("https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson").json()
        with open(self.fileMapping["countries"], 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(data)
        
        countries = {}
        for feature in data["features"]:
            geom = feature["geometry"]
            country = feature["properties"]["ADMIN"]
            countries[country] = prep(shape(geom))
            
            
        def get_country(lon, lat):
          point = Point(lon, lat)
          for country, geom in countries.items():
              if geom.contains(point):
                  return country
        
        country = get_country(lon, lat)
        if not country: 
          raise Exception("Ouch! No country was found")
              
        return country.upper()
      
      
class EventEPSG(microServiceABC.MicroServiceABC):

    # Initialization method
    def __init__(self):
        """
        Initialize the eventDispatcher component implementation    
        """

    # Service's entry point definition
    @microServiceABC.MicroServiceABC.runRegistration
    def entryPoint(self, body):
        """
        Figure out the country which the incoming EQ event belong 
        """
        
        alert = body['alerts'][0];
        epsg = self._getEPSG(alert['longitude'],alert['latitude'])
        print(epsg, flush = True)
        # Return list of Id of the newly created item
        return jsonify(result = epsg, response = 201)
        
    def _getEPSG(self, longitude, latitude):   
      
    
      # Special zones for Svalbard and Norway
      # Source: https://gis.stackexchange.com/questions/365584/convert-utm-zone-into-epsg-code
        def getZones(longitude, latitude) :
            
            if (latitude >= 72.0 and latitude < 84.0 ) :
                if (longitude >= 0.0  and longitude <  9.0) :
                      return 31              
            if (longitude >= 9.0  and longitude < 21.0):
                  return 33
            if (longitude >= 21.0 and longitude < 33.0):
                  return 35
            if (longitude >= 33.0 and longitude < 42.0) :
                  return 37
            return (math.floor((longitude + 180) / 6) ) + 1 
    

        def findEPSG(longitude, latitude) :
            
            zone = getZones(longitude, latitude)
            #zone = (math.floor((longitude + 180) / 6) ) + 1  # without special zones for Svalbard and Norway         
            epsg_code = 32600
            epsg_code += int(zone)
            if (latitude < 0): # South
                epsg_code += 100    
            return epsg_code
              
              
        return(findEPSG(longitude,latitude))
      
      
      
      
      
