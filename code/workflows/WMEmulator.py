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
import argparse
import requests
import json

################################################################################
# Temporal Workflow manager simulator 
################################################################################

# Arguments parser
def parser():

    # Parse the arguments
    parser = argparse.ArgumentParser(
        prog='workflow_manager',
        description='Temporal workflow manager emulator')
    parser.add_argument('events', help='JSON containing a set of AAS events')

    args = parser.parse_args()

    # Check the arguments
    if not os.path.isfile(args.events):
      raise Exception("The events file '"+args.events+ "' doesn't exist")

    # Return them
    return args

# Main Method
def main():
    try:
        # Call the parser
        args = parser()

        # Read the events file (readed by the AAS)
        with open(args.events, 'r') as f:
            events = json.load(f)
            
        # Event dispatcher
        r = requests.post("http://127.0.0.1:5000/eventsDispatcher", json=events)
        
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
            

    except Exception as error:
        print("Exception in code:")
        print('-'*80)
        traceback.print_exc(file=sys.stdout)
        print('-'*80)    
    

################################################################################
# Run the program
if __name__ == "__main__":
    main()    
