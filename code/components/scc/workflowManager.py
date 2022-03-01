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
import uuid
import concurrent.futures
import time
import os

# Third parties
from flask import jsonify

# Internal
import ucis4eq
from ucis4eq.misc import config, microServiceABC

################################################################################
# Methods and classes

class WorkflowManagerEmulator(microServiceABC.MicroServiceABC):

    # Initialization method
    def __init__(self):
        """
        Initialize the sourceType component implementation
        """

        # Obtain UCIS4EQ Services URL 
        localhost = "http://127.0.0.1"
        self.url = os.getenv("UCIS4EQ_LOCATION", localhost)
        if self.url == "":
            self.url = localhost
            

    @staticmethod
    def compute(lalert, url):
        r = requests.post(url + ":5002/Graves-Pitarka", json=lalert)
        config.checkPostRequest(r)
        lalert["rupture"] = r.json()['result']['rupture']

        # Generate the input parameter file for phase 2 in YAML format
        r = requests.post(url + ":5000/inputParametersBuilder", json=lalert)
        config.checkPostRequest(r)
        stage2InputP = r.json()['result']

        # TODO:
        # Call a service in charge of deciding the simulator code (HUB)

        # Build the Salvus input parameter file (remotely)
        sim = {}
        sim["id"] = lalert['id']
        sim["trial"] = lalert['trial']
        sim["input"] = stage2InputP
        sim["resources"] = lalert['resources']
        r = requests.post(url + ":5003/SalvusPrepare", json=sim)
        config.checkPostRequest(r)
        sim["input"] = r.json()['result']

        # Call Salvus system (or other)
        r = requests.post(url + ":5003/SalvusRun", json=sim)
        config.checkPostRequest(r)

        return lalert

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

        #r = requests.post(self.url + ":5000/eventCountry", json=event)
        #config.checkPostRequest(r)
        #event['country'] = r.json()['result']

        # Calculate the event priority
        # TODO: This task belong to the branch "Urgent computing" (It runs in parallel)
        #r = requests.post(self.url + ":5000/indexPriority", json=event)
        #config.checkPostRequest(r)
        #print(r.json()['resgult'],flush=True)

        # Obtain the Event Id. (useful during all the workflow livecycle)
        r = requests.post(self.url + ":5000/eventRegistration", json=event)
        config.checkPostRequest(r)
        self.eid = r.json()['result']
        
        # Obtain the region where the event occured
        r = requests.post(self.url + ":5000/eventDomains", json={'id': self.eid})
        config.checkPostRequest(r)
        domains = r.json()['result']        
        
        # Check the region
        if not domains:
            # Set the event with SUCCESS state
            r = requests.post(self.url + ":5000/eventSetState", 
                               json={'id': self.eid, 'state': "REJECTED"})
            config.checkPostRequest(r)
            self.eid = r.json()['result']
                        
            raise Exception("There is not enough information for simulating the EQ in region")
    
        # For each found domain
        for domain in domains:
            input = {}
            
            # Creating the pool executor
            with concurrent.futures.ProcessPoolExecutor(max_workers=1) as executor:
                futures = []

                # Calculate the CMT input parameters
                r = requests.post(self.url + ":5000/precmt", json={'id': self.eid, 'region': domain['region']})
                config.checkPostRequest(r)
                precmt = r.json()['result']
                
                # Obtain region information
                r = requests.post(self.url + ":5000/eventGetRegion", json={'id': domain['region']})
                config.checkPostRequest(r)
                region = r.json()['result']                

                event = precmt['event']
                setup = {'setup': precmt, 'catalog': domain['region']}

                r = requests.post(self.url + ":5000/computeResources", json={'id': self.eid, 'domain': domain})
                config.checkPostRequest(r)
                compResources = r.json()['result']
                
                # Compute CMTs for each pair event-alert (earthquake - Agency notification)
                input = {'id': self.eid, 'base': "event_" + body['uuid']}
                input.update(setup)

                # Append the region
                input["domain"] = domain
                input["resources"] = compResources

                for a in event['alerts']:

                    input['event'] = a

                    r = requests.post(self.url + ":5000/cmt", json=input)
                    config.checkPostRequest(r)

                    cmt = r.json()['result']
                    
                    # TODO Remove this line for enabling statistical CMTs
                    cmt = {}
                    
                    if "cmt" in a.keys():
                        cmt.update(a["cmt"])

                    input['event'].update({"CMT":cmt})

                    #alert = event['alerts'][a]
                    #print(json.dumps(alert))

                    # Determine the appropiate source for this event
                    # TODO: Define the input parameters that we need for this step
                    r = requests.post(self.url + ":5000/sourceType", json={'id': self.eid})
                    config.checkPostRequest(r)

                    sourceType  = r.json()['result']

                    # Compute source
                    # TODO: Select the correct way according to the received source type

                    # For each CMT in the alert
                    for cmt in input['event']['CMT'].keys():

                        # For each GP defined trial
                        for slip in range(1, region['GPSetup']['trials']+1):
                            # Set the trial path
                            tags = ".".join([domain['id'], cmt, "slip"+str(slip)])

                            # Create a local alert
                            lalert = {}
                            lalert = input['event'].copy()
                            lalert['id'] = self.eid
                            lalert['trial'] = input['base'] + "/trial_" + tags
                            lalert['CMT'] = input['event']['CMT'][cmt]
                            lalert['domain'] = input['domain']
                            lalert['resources'] = input['resources']                            
                            
                            if 'seed' in a.keys():
                                lalert['seed'] = a['seed']

                            futures.append(executor.submit(WorkflowManagerEmulator.compute, lalert, self.url))
                            
                            break  ## Avoid to run 66 times this (swarm runs)
                        break  ## Avoid to run 66 times this (swarm runs)
                    break

                print("Waitting for results", flush=True)
                for future in concurrent.futures.as_completed(futures):
                    data = future.result()
                                            
            # Post-process output by generating:
            input['trial'] = lalert['trial']
            r = requests.post(self.url + ":5003/SalvusPost", json=input)
            config.checkPostRequest(r)
            
            # Set the event with SUCCESS state
            r = requests.post(self.url + ":5000/eventSetState", 
                               json={'id': self.eid, 'state': "SUCCESS"})
            config.checkPostRequest(r)
            self.eid = r.json()['result']        
        
        # Return list of Id of the newly created item
        return jsonify(result = "Event with UUID " + str(body['uuid']) + " notified for region " + str(domain['region']), response = 201)
