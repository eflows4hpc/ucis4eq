#!/usr/bin/env python3

# RESTful server for event treatment
# This module is part of the Automatic Alert System (AAS) solution

# Author: Juan Esteban Rodríguez
# Contributor: Josep de la Puente <josep.delapuente@bsc.es>

# ###############################################################################
#       BSD 3-CLAUSE, aka BSD NEW, aka BSD REVISED, aka MODIFIED BSD LICENSE

# Copyright 2023,2024 Juan Esteban Rodriguez

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
import sys
import json
import ast
import traceback
from functools import wraps

from flask import Flask, request, jsonify

# Load Salvus service implemented components
from ucis4eq.scc.salvus import SalvusPrepare, SalvusRun, SalvusPost,\
    SalvusPlots, SalvusPing, SalvusPostSwarm

# ###############################################################################
# Dispatcher App creation
# ###############################################################################
salvusServiceApp = Flask(__name__)


def postRequest(fn):
    # POST request decorator

    @wraps(fn)
    def wrapped(*args, **kwargs):
        """
        Function to dispatch new events.
        """
        # Create new events
        try:
            #print("INFO: Received JSON: " + str(request.get_json()))
            body = ast.literal_eval(json.dumps(request.get_json()))
        except:
            # Bad request as request body is not available
            # MPC: add info message for debugging purposes
            print("Error in JSON request. Received the following JSON: " + str(request.get_json()))
            traceback.print_exc()
            return "Error in JSON request format " + str(request.get_json()), 400

        # Call the decorated method passing it the input JSON
        return fn(body)

    return wrapped


@salvusServiceApp.route("/")
def get_initial_response():
    # Base roor of the micro-services Hub
    """Welcome message for the API."""
    # Message to the user
    message = {
        'apiVersion': 'v1.0',
        'status': '200',
        'message': 'Welcome to the UCIS4EQ Salvus service for PD1'
    }
    # Making the message looks good
    resp = jsonify(message)
    # Returning the object
    return resp

# ###############################################################################
# Services definition
# ###############################################################################


# Generate input parameters for Salvus
@salvusServiceApp.route("/SalvusPrepare", methods=['POST'])
@postRequest
def SalvusPrepareService(body):
    """
    Call component implementing this service
    """

    return SalvusPrepare().entryPoint(body)


@salvusServiceApp.route("/SalvusRun", methods=['POST'])
@postRequest
def SalvusRunService(body):
    # Call Salvus for a trial
    """
    Call component implementing this service
    """

    return SalvusRun().entryPoint(body)


# Call Salvus post-processing
@salvusServiceApp.route("/SalvusPost", methods=['POST'])
@postRequest
def SalvusPostService(body):
    """
    Call component implementing this service
    """
    return SalvusPost().entryPoint(body)


# Call Salvus post-processing
@salvusServiceApp.route("/SalvusPostSwarm", methods=['POST'])
@postRequest
def SalvusPostSwarmService(body):
    """
    Call component implementing this service
    """
    return SalvusPostSwarm().entryPoint(body)


# Call Salvus post-processing
@salvusServiceApp.route("/SalvusPlots", methods=['POST'])
@postRequest
def SalvusPlotsService(body):
    """
    Call component implementing this service
    """
    return SalvusPlots().entryPoint(body)


# Call Salvus post-processing
@salvusServiceApp.route("/SalvusPing", methods=['POST'])
@postRequest
def SalvusPingService(body):
    """
    Call component implementing this service
    """
    return SalvusPing().entryPoint(body)

# ###############################################################################
# Start the micro-services aplication
# ###############################################################################

if __name__ == '__main__':
    # Running app in debug mode
    salvusServiceApp.run(host="0.0.0.0", debug=True, port=5003)
