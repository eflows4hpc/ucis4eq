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

from pycompss.api.parameter import *
from pycompss.api.http import http
from pycompss.api.api import compss_wait_on, compss_barrier
from pycompss.api.task import task
from pycompss.api.on_failure import on_failure

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
        lalert["rupture"] = r.json()['result']

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

        # Call Salvus post (or other)
        r = requests.post(url + ":5003/SalvusPost", json=sim)
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
            with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:
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
                setup = {'setup': precmt}

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
                            lalert['event'] = input['event'].copy()
                            lalert['id'] = self.eid
                            lalert['trial'] = input['base'] + "/trial_" + tags
                            lalert['CMT'] = input['event']['CMT'][cmt]
                            lalert['domain'] = input['domain']
                            lalert['resources'] = input['resources']

                            if 'seed' in a.keys():
                                lalert['event']['seed'] = a['seed']

                            futures.append(executor.submit(WorkflowManagerEmulator.compute, lalert, self.url))

                            #break  ## Avoid to run 66 times this (swarm runs)
                        #break  ## Avoid to run 66 times this (swarm runs)
                    #break


                print("Waiting for results", flush=True)
                for future in concurrent.futures.as_completed(futures):
                    data = future.result()

            # Post-process output by generating:
            r = requests.post(self.url + ":5003/SalvusPlots", json=input)
            config.checkPostRequest(r)

            # Set the event with SUCCESS state
            r = requests.post(self.url + ":5000/eventSetState",
                               json={'id': self.eid, 'state': "SUCCESS"})
            config.checkPostRequest(r)
            self.eid = r.json()['result']

        # Return list of Id of the newly created item
        return jsonify(result = "Event with UUID " + str(body['uuid']) + " notified for region " + str(domain['region']), response = 201)


class PyCommsWorkflowManager(microServiceABC.MicroServiceABC):

    # Initialization method
    def __init__(self):
        """
        Initialize -the workflow manager
        """

    # Service's entry point definition
    @config.safeRun
    def entryPoint(self, body):
        """
        PyCOMPSs workflow manager
        """

        print("__ Running PyCOMPSs workflow __")
        event = body
        #print(body)

        # Set event's name
        basename = "event_" + event['uuid']

        # Obtain the Event Id. (useful during all the workflow livecycle)
        eid = register_event(event)

        ensemble = 'statisticalCMT'
        if 'ensemble' in body:
            ensemble = body['ensemble']

        # Obtain the region where the event occured
        region = get_region(eid)

        # Obtain the setup depending on the incoming event
        setup = get_setup(eid,ensemble)

        # Wait for future to check if continue or abort
        region = compss_wait_on(region)
        setup = compss_wait_on(setup)

        if not region:
            eid = set_event_state(eid, "REJECTED")

            # MPC: improve error message about which EQ is not simulated
            # MPC: try to always print info from IRIS for consistency unless not available

            IRIS_idx = next((index for (index, d) in enumerate(event['alerts']) if d["agency"] == "IRIS"), None)

            if IRIS_idx:
                print_info = event['alerts'][IRIS_idx]
            else:
                print_info = event['alerts'][0]

            error_message = f" \n WARNING: There is not enough information for simulating the following event: \n " \
                             f"Time: {print_info['time']}, \n " \
                             f"Description: {print_info['description']}, \n " \
                             f"Latitude: {print_info['latitude']:.1f}, \n " \
                             f"Longitude: {print_info['longitude']:.1f}, \n " \
                             f"Magnitude: {print_info['magnitude']} \n"

            return error_message, 500

            #raise Exception("There is not enough information for simulating the EQ in region")
        else:

            # Calculate computational resources for the given domain
            resources = compute_resources(eid, region)

            # Obtain rupture generator's setup
            gpsetup = graves_pitarka_setup(eid, region, setup)

            # Wait for GP Setup
            gpsetup = compss_wait_on(gpsetup)

            if ensemble == "seisEnsMan":
                print("__ Reading SeisEnsMan data __")            	
            	# Read the json that has the outputs of SeisEnsMan
                inputsSeisEnsMan = input_seisensman(eid, region, resources, setup)
                inputsSeisEnsMan = compss_wait_on(inputsSeisEnsMan) 		
	        # Compute and launch a simulation per each input given in the SeisEnsMan json
                all_results = []
                for alert in event['alerts']:
                    for i in range(len(inputsSeisEnsMan)):
                        # For each GP defined trial
                        for slip in range(1, gpsetup['trials']+1):
                            # Set the trial path
                            path = basename + "/trial_" + ".".join(["seisEnsMan"+str(i), "slip"+str(slip)])
                            data_seisEnsMan = inputsSeisEnsMan[i]['data']		
		            
                            # Call Graves-Pitarka's rupture generator for seisensman
                            all_results.append(launch_simulation(eid, alert, path, data_seisEnsMan, region, gpsetup, resources, ensemble))
            else: 		   # setup["source_ensemble"] == "statisticalCMT"
		# Calculate the CMT input parameters
                precmt = build_cmt_input(eid, region, resources, setup)		
                # Compute alerts
                all_results = []
                for alert in event['alerts']:	
                    # Calculating CMTs
                    cmts = calculate_cmt(alert, eid, region, precmt)
                    # Wait for calculated CMTs
                    cmts = compss_wait_on(cmts)	
                    # For each calculated or provided CMT
                    for cmt in cmts.keys():
                        # For each GP defined trial
                        for slip in range(1, gpsetup['trials']+1):
                            # Set the trial path
                            path = basename + "/trial_" + ".".join([cmt, "slip"+str(slip)])	
                            all_results.append(launch_simulation(eid, alert, path, cmts[cmt], region, gpsetup, resources, ensemble))
                            # break
                        # break
                    # break

            result = launch_post_swarm(eid, region, basename, resources, all_results)

            # Set the event with SUCCESS state
            result = compss_wait_on(result)
            eid = set_event_state(eid, "SUCCESS")

        # Wait for the workflow to finish
        compss_barrier(no_more_tasks=True)

        # Return list of Id of the newly created item
        return jsonify(result = "Event with UUID " + str(body['uuid']), response = 201)

def launch_simulation(eid, alert, path, data, region, gpsetup, resources, ensemble):
    HPC_RUN_PYCOMPSS=bool(os.environ.get("HPC_RUN_PYCOMPSS", "False"))
    if HPC_RUN_PYCOMPSS:
        rupture = path + "/scratch/outdata/rupture/rupture.srf"
        # Call input parameters builder
        inputs = build_input_parameters( eid, alert, data, rupture, region, resources, gpsetup, ensemble)
        # Call Graves-Pitarka's rupture generator
        result = run_simulation(eid, alert, path, data, region, gpsetup, inputs, resources, ensemble)
    else:
        # Call Graves-Pitarka's rupture generator
        rupture = compute_graves_pitarka(eid, alert, path, data, region, gpsetup, resources, ensemble)
        # Call input parameters builder
        inputs = build_input_parameters(eid, alert, data, rupture, region, resources, gpsetup, ensemble)
        # Build the Salvus input parameter file (remotely)
        salvus_inputs = build_salvus_parameters( eid, path, inputs, resources)
        # Build the Salvus input parameter file (remotely)
        salvus_result = run_salvus( eid, path, salvus_inputs,resources)
        # Call Salvus post
        result = run_salvus_post(eid, salvus_result, path, resources)
    return result

def launch_post_swarm(eid, region, basename, resources, all_results):
    HPC_RUN_PYCOMPSS=bool(os.environ.get("HPC_RUN_PYCOMPSS", "False"))
    if HPC_RUN_PYCOMPSS:
        result = post_simulation(eid, region, basename, resources, all_results)
    else:
        # Call postprocessing swarm
        output_swarm = run_salvus_post_swarm(eid, basename, resources)

        # General post-processing for generating plots
        result = run_salvus_plots(eid, output_swarm, region, basename, resources)
    return result

#@on_failure(management='IGNORE', returns=0)
@http(request="POST", resource="eventRegistration", service_name="microServices",
      payload="{{event}}", produces='{"result" : "{{return_0}}" }')
@task(returns=1)
def register_event(event):
    """
    """
    pass

#@on_failure(management='IGNORE', returns=0)
@http(request="POST", resource="eventRegion", service_name="microServices",
      payload='{ "id" : {{event_id}} }',
      produces='{"result" : "{{return_0}}" }')
@task(returns=1)
def get_region(event_id):
    """
    """
    pass

#@on_failure(management='IGNORE', returns=0)
@http(request="POST", resource="eventSetup", service_name="microServices",
      payload='{ "id" : {{event_id}}, "ensemble" : "{{ensemble}}" }',
      produces='{"result" : "{{return_0}}" }')
@task(returns=1)
def get_setup(event_id, ensemble):
    """
    """
    pass

#@on_failure(management='IGNORE', returns=0)
@http(request="POST", resource="eventSetState", service_name="microServices",
      payload='{ "id" : {{event_id}}, "state": "{{state}}" }',
      produces='{"result" : "{{return_0}}" }')
@task(returns=1)
def set_event_state(event_id, state):
    """
    """
    pass

#@on_failure(management='IGNORE', returns=0)
@http(request="POST", resource="cmtSeisEnsMan", service_name="microServices",
      payload='{ "id" : {{event_id}}, "region": {{region}}, \
                 "resources": {{resources}}, "setup": {{setup}} }',
      produces='{"result" : "{{return_0}}" }')
@task(returns=1)
def input_seisensman(event_id, region, resources, setup):
    """
    """
    pass

#@on_failure(management='IGNORE', returns=0)
@http(request="POST", resource="precmt", service_name="microServices",
      payload='{ "id" : {{event_id}}, "region": {{region}}, \
                 "resources": {{resources}}, "setup": {{setup}} }',
      produces='{"result" : "{{return_0}}" }')
@task(returns=1)
def build_cmt_input(event_id, region, resources, setup):
    """
    """
    pass

#@on_failure(management='IGNORE', returns=0)
#, "base" : {{base_name}}, "resources" : {{resources}}
@http(request="POST", resource="cmt", service_name="microServices",
      payload='{ "event" : {{alert}}, "id" : {{event_id}}, \
                 "region" : {{region}}, "setup" : {{precmt}} }',
      produces='{"result" : "{{return_0}}"}')
@task(returns=1)
def calculate_cmt(alert, event_id, region, precmt):
    """
    """
    pass

#@on_failure(management='IGNORE', returns=0)
@http(request="POST", resource="computeResources", service_name="microServices",
      payload='{ "id" : {{event_id}}, "region": {{region}} }',
      produces='{"result" : "{{return_0}}" }')
@task(returns=1)
def compute_resources(event_id, region):
    """
    """
    pass

#@on_failure(management='IGNORE', returns=0)
@on_failure(management ='CANCEL_SUCCESSORS')
@http(request="POST", resource="preGraves-Pitarka", service_name="slipgen",
      payload='{ "id" : {{event_id}}, "region": {{region}}, "setup": {{setup}} }',
      produces='{"result" : "{{return_0}}" }')
@task(returns=1)
def graves_pitarka_setup(event_id, region, setup):
    """
    """
    pass

#@on_failure(management='IGNORE', returns=0)
@http(request="POST", resource="Graves-Pitarka", service_name="slipgen",
      payload='{ "event" : {{alert}}, "id" : {{event_id}}, "CMT" : {{cmt}}, \
                 "trial" : "{{path}}", "region": {{region}}, "setup" : {{setup}}, \
                 "resources" : {{resources}} , "ensemble" : "{{ensemble}}" }',
      produces='{"result" : "{{return_0}}"}')
@task(returns=1)
def compute_graves_pitarka(event_id, alert, path, cmt, region, setup, resources, ensemble):
    """
    """
    pass

#@on_failure(management='IGNORE', returns=0)
@http(request="POST", resource="inputParametersBuilder", service_name="microServices",
      payload='{ "id" : {{event_id}}, "event" : {{alert}}, "CMT" : {{cmt}}, \
                 "rupture" : {{rupture}}, "region" : {{region}}, \
                 "resources" : {{resources}}, "setup" : {{setup}}, "ensemble" : "{{ensemble}}" }',
      produces='{"result" : "{{return_0}}"}')
@task(returns=1)
def build_input_parameters(event_id, alert, cmt, rupture, region, resources, setup, ensemble):
    """
    """
    pass

#@on_failure(management='IGNORE', returns=0)
@on_failure(management ='CANCEL_SUCCESSORS')
@http(request="POST", resource="SalvusPrepare", service_name="salvus",
      payload='{ "id" : {{event_id}}, "trial" : "{{trial}}", \
                 "input" : {{input}}, "resources" : {{resources}} }',
      produces='{"result" : "{{return_0}}"}')
@task(returns=1)
def build_salvus_parameters(event_id, trial, input, resources):
    """
    """
    pass

#@on_failure(management='IGNORE', returns=0)
@on_failure(management ='CANCEL_SUCCESSORS')
@http(request="POST", resource="SalvusRun", service_name="salvus",
      payload='{ "id" : {{event_id}}, "trial" : "{{trial}}", \
                 "input" : {{input}}, "resources" : {{resources}} }',
      produces='{"result" : "{{return_0}}"}')
@task(returns=1)
def run_salvus(event_id, trial, input, resources):
    """
    """
    pass

#@on_failure(management='IGNORE', returns=0)
@on_failure(management ='CANCEL_SUCCESSORS')
@http(request="POST", resource="SalvusPost", service_name="salvus",
      payload='{ "id" : {{event_id}}, "trial" : "{{trial}}", \
                 "resources" : {{resources}} }',
      produces='{"result" : "{{return_0}}"}')
@task(returns=1)
def run_salvus_post(event_id, salvus_result, trial, resources):
    """
    """
    pass

#@on_failure(management='IGNORE', returns=0)
@on_failure(management ='CANCEL_SUCCESSORS')
@http(request="POST", resource="SalvusPostSwarm", service_name="salvus",
      payload='{ "id" : {{event_id}}, "base" : "{{base}}", "resources" : {{resources}} }',
      produces='{"result" : "{{return_0}}"}')
@task(returns=1)
def run_salvus_post_swarm(event_id, base, resources):
    """
    """
    pass

#@on_failure(management='IGNORE', returns=0)
@on_failure(management ='CANCEL_SUCCESSORS')
@http(request="POST", resource="SalvusPlots", service_name="salvus",
      payload='{ "id" : {{event_id}}, "region" : {{region}}, "base" : "{{base}}", \
                 "resources" : {{resources}} }',
      produces='{"result" : "{{return_0}}"}')
#@task(returns=1, results=COLLECTION_IN)
@task(returns=1)
def run_salvus_plots(event_id, salvus_post_results, region, base, resources):
    """
    """
    pass    
    

# @on_failure(management='IGNORE')
@http(request="POST", resource="simulation-run", service_name="simulation",
      payload='{ "event" : {{alert}}, "id" : "{{event_id}}", "CMT" : {{cmt}}, \
                 "trial" : "{{trial}}", "region": {{region}}, "setup" : {{setup}}, \
                 "input" : {{input}}, "resources" : {{resources}}, "ensemble" : "{{ensemble}}"  }',
      produces='{"result" : "{{return_0}}"}')
@task(returns=1)
def run_simulation(event_id, alert, trial, cmt, region, setup, input, resources, ensemble):
    """
    """
    pass


# @on_failure(management='IGNORE')
@http(request="POST", resource="simulation-post", service_name="simulation",
      payload='{ "id" : "{{event_id}}", "region" : {{region}}, "base" : "{{base}}", \
                 "resources" : {{resources}} }',
      produces='{"result" : "{{return_0}}"}')
@task(returns=1, all_results=COLLECTION_IN)
def post_simulation(event_id, region, base, resources, all_results):
    """
    """
    pass

