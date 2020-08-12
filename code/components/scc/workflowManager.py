#!/usr/bin/env python3
#
# Workflow Manager
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
import requests
import json

# Third parties
from flask import jsonify

# Internal
from ucis4eq.misc import config
from ucis4eq.scc import microServiceABC

################################################################################
# Methods and classes
        
class WorkflowManagerEmulator(microServiceABC.MicroServiceABC):

    # Initialization method
    def __init__(self):
        """
        Initialize the sourceType component implementation    
        """
        
        # Select the database
        self.db = config.database
        self.eid = None

    # Service's entry point definition
    @config.safeRun
    def entryPoint(self, body):
        """
        Temporal workflow manager emulator
        """
        # Just a naming convention
        event = body
        
        # Obtain the Event Id. (useful during all the workflow livecycle)
        # TODO: This task belong to the branch "Urgent computing" (It runs in parallel)

        r = requests.post("http://127.0.0.1:5000/eventCountry", json=event)
        config.checkPostRequest(r)
        event['country'] = r.json()['result']
        
        # Calculate the event priority
        # TODO: This task belong to the branch "Urgent computing" (It runs in parallel)
        r = requests.post("http://127.0.0.1:5000/indexPriority", json=event)
        config.checkPostRequest(r)   
        #print(r.json()['result'],flush=True)
             
        # Obtain the Event Id. (useful during all the workflow livecycle)
        r = requests.post("http://127.0.0.1:5000/eventRegistration", json=event)
        config.checkPostRequest(r)
        self.eid = r.json()['result']
        
        # Obtain the region where the event occured
        r = requests.post("http://127.0.0.1:5000/eventRegion", json={'event': self.eid})
        config.checkPostRequest(r)
        region = r.json()['result']
        
        # Check the region
        if not region:
            raise Exception("There is not enough information for simulating the EQ in region")
        
        # Calculate the CMT input parameters
        r = requests.post("http://127.0.0.1:5000/precmt", json={'event': self.eid})
        config.checkPostRequest(r)

        precmt = r.json()['result']
            
        event = precmt['event']
        setup = {'setup': precmt['setup'], 'repositories': precmt['repositories']}

        # Compute CMTs for each pair event-alert (earthquake - Agency notification)
        for a in event['alerts']:
            input = {}
            input.update(setup)
            input.update({"event": a})
            r = requests.post("http://127.0.0.1:5000/cmt", json=input)
            config.checkPostRequest(r)

            cmt = r.json()['result']
            #print(cmt, flush=True)
            
            a.update({"CMT":cmt})
            
            #alert = event['alerts'][a]
            #print(json.dumps(alert))
        
            # Determine the appropiate source for this event
            # TODO: Define the input parameters that we need for this step 
            r = requests.post("http://127.0.0.1:5000/sourceType", json={})
            config.checkPostRequest(r)

            sourceType  = r.json()['result']
                
            # Compute source
            # TODO: Select the correct way according to the received source type 

            # For each CMT in the alert
            for cmt in a['CMT'].keys():
                input = {}
                                    
                # Create a local alert
                lalert = a.copy()
                lalert['CMT'] = a['CMT'][cmt]
                
                input["event"] = lalert
                
                # Add the UUID 
                input["uuid"] = body['uuid'] + "." + cmt 
                
                #   Option 1:  Graves-Pitarka generated source  (SRF)
                r = requests.post("http://127.0.0.1:5002/Graves-Pitarka", json=lalert)
                config.checkPostRequest(r)

                input["rupture"] = r.json()['result']['slipmodel']

                #   Option 2:  Punctual source (Tensors plain text file)
                # TODO: The call is right but no results are returned yet 
                #r = requests.post("http://127.0.0.1:5000/punctualSource", json=alert)
                #config.checkPostRequest(r)

                #result = r.json()['result']
                
                #print(json.dumps(input["event"]), flush=True)
                
                # Append the region
                input["region"] = region
                
                # Generate the input parameter file for phase 2 in YAML format
                r = requests.post("http://127.0.0.1:5000/inputParametersBuilder", json=input)
                config.checkPostRequest(r)

                        
                # Call Salvus system (or other)        
                # TODO
                
                # Post-process output by generating:
                #   - Spectral acceleration (By ranges calculated)
                #   - Rot50 (calculated from two orthogonal horizontal components, 
                #     and azimuthally independent)                    
                # TODO
                            
        # Return list of Id of the newly created item
        return jsonify(result = "Event with UUID " + str(body['uuid']) + " notified for region " + str(region['id']), response = 201)
