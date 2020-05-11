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
import requests
import json

# Third parties
from flask import jsonify

# Internal
from ucis4eq.misc import config
from ucis4eq.scc import microServiceABC

################################################################################
# Methods and classes

class workflowManagerEmulator(microServiceABC.MicroServiceABC):

    # Initialization method
    def __init__(self):
        """
        Initialize the sourceType component implementation    
        """
        
        # Select the database
        self.db = config.database

    # Service's entry point definition
    def entryPoint(self, body):
        """
        Temporal workflow manager emulator
        """
        try:
            # Just a naming convention
            events = body
                
            # Event dispatcher
            r = requests.post("http://127.0.0.1:5000/eventsDispatcher", json=events)
            nevents = len(r.json()['result'])
            # For each received alert
            for e in r.json()['result']:
                # Calculate the CMT input parameters
                r = requests.post("http://127.0.0.1:5000/precmt", json={'event': e})
                result = r.json()['result']
                
                event = result['event']
                setup = {'setup': result['setup'], 'repositories': result['repositories']}
        
                # Compute CMTs for each pair event-alert (earthquake - Agency notification)
                for a in event['alerts']:
                    input = {}
                    input.update(setup)
                    input.update({"event": event['alerts'][a]})
                    r = requests.post("http://127.0.0.1:5000/cmt", json=input)
                    
                    event['alerts'][a].update({"CMT":r.json()})
                    
                    alert = event['alerts'][a]
                    print(json.dumps(alert))
                
                    # Determine the appropiate source for this event
                    # TODO: Define the input parameters that we need for this step 
                    r = requests.post("http://127.0.0.1:5000/sourceType", json={})
                    source  = r.json()['result'] 
                    
                    # TODO: Compute source 
                    #   Option 1:  Graves-Pitarka generated source  (SRF)
                    #   Option 2:  Punctual source (Tensors plain text file)
                    r = requests.post("http://127.0.0.1:5000/punctualSource", json=alert)
                    result = r.json()['result']
                    
                    # TODO: Call Salvus system (or other)
                    
                    
                    # TODO: Post-process output by generating:
                    #   - Spectral acceleration (By ranges calculated)
                    #   - Rot50 (calculated from two orthogonal horizontal components, 
                    #     and azimuthally independent)
                                
            # Return list of Id of the newly created item
            return jsonify(result = str(nevents) + " events notified", response = 201)
                
        except Exception as error:
            # Error while trying to create the resource
            # Add message for debugging purpose
            print("Exception in code:")
            print('-'*80)
            traceback.print_exc(file=sys.stdout)
            print('-'*80)
            return jsonify(result = {}, response = 501)
