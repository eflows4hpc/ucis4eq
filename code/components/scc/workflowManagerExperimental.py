#!/usr/bin/env python3

# Workflow Manager
# This module is part of the Smart Center Control (SSC) solution

# Author:  Juan Esteban Rodríguez, Josep de la Puente
# Contact: juan.rodriguez@bsc.es, josep.delapuente@bsc.es

# ###############################################################################
#       BSD 3-CLAUSE, aka BSD NEW, aka BSD REVISED, aka MODIFIED BSD LICENSE

# Copyright 2023,2024 Josep de la Puente, Juan Esteban Rodriguez

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
# 3. Neither the name(s) of the copyright holder(s) nor the name(s) of its
# contributor(s) may be used to endorse or promote products derived from this
# software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER(S) AND CONTRIBUTOR(S) “AS
# IS” AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER(S) OR CONTRIBUTOR(S) BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# ###############################################################################
# Module imports
# System
import requests
import json

# Third parties
from flask import jsonify
from dask.distributed import Client, progress

# Internal
from ucis4eq.misc import config, microServiceABC


# TODO Remove this
import time
import random

def inc(x):
    time.sleep(random.random())
    return x + 1

def double(x):
    time.sleep(random.random())
    return 2 * x

def add(x, y):
    time.sleep(random.random())
    return x + y

# ###############################################################################
# Methods and classes
        
class DaskWorkflowManager(microServiceABC.MicroServiceABC):

    # Initialization method
    def __init__(self):
        """
        Initialize the sourceType component implementation    
        """
        # Set the microServices URL
        self.urls = {}
        
        self.urls["microServices"] = "http://127.0.0.1:5000"
        self.urls["thirdParties"] = "http://127.0.0.1:5002"
        
        # Select the database
        self.db = config.database
        
        # Event ID
        self.eid = None
        
        # Set the Dask client
        self.client = Client()

    # Service's entry point definition
    @config.safeRun
    def entryPoint(self, body):
        """
        Workflow manager based on the Dask scheduler
        """
        # Just a naming convention
        event = body
        
        zs = []
        for i in range(25):
            x = self.client.submit(inc, i)     # x = inc(i)
            y = self.client.submit(double, x)  # y = inc(x)
            z = self.client.submit(add, x, y)  # z = inc(y)
            zs.append(z)
            
        total = self.client.submit(sum, zs)
        
        #print(total, flush=True)
        
        print(total.result(), flushh=True)
                    
        # Obtain the Event Id. (useful during all the workflow livecycle)
        # TODO: This task belong to the branch "Urgent computing" (It runs in parallel)
        
        #r  = self.client.submit(self._request, "http://127.0.0.1:5000", "eventCountry", event)
        
        #foo = self.client.submit(config.checkPostRequest, r)
        
        #event['country'] = r.json()['result']
                            
        # Return list of Id of the newly created item
        return jsonify(result = "Event notified", response = 201)
        #return jsonify(result = "Event with UUID " + str(body['uuid']) + " notified for region " + str(region['id']), response = 201)
        
    # Request wrapper for simplification
    def _request(self, url, service, data):
        """
        Request wrapper for simplification
        """
                
        #return requests.post(url + "/eventCountry", json=data)

         
            
