#!/usr/bin/env python3

# Input builder (Interphasing phase 1 and phase 2)
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

# Third parties
from flask import jsonify

# Internal
from ucis4eq.misc import microServiceABC
import ucis4eq.launchers as launchers
import ucis4eq as ucis4eq
import ucis4eq.dal as dal

# ###############################################################################
# Methods and classes

class ComputeResources(microServiceABC.MicroServiceABC):

    # Initialization method
    def __init__(self):
        """
        Initialize the CMT statistical component implementation
        """
        
        # Select the database
        self.db = ucis4eq.dal.database        

        # Default site's setup
        self.type = 'LOCAL'

    # Service's entry point definition
    @microServiceABC.MicroServiceABC.runRegistration        
    def entryPoint(self, body):
        """
        Calculate the computational resources and site
        """
        
        # Decide what site to use among the availables
        resource = None

        resources = list(self.db.Resources.find({}, {'_id': False}).sort('order', 1))
        for site in resources:
            if site['id'] in launchers.config:
                resource = site
                break

        tmp = resource['id']
        conf = launchers.config[tmp]
        conf.update(resource)
        # Create a launcher to obtain the Setup
        launcher = launchers.launchers.create(tmp, **launchers.config)

        if launcher.setup:
            resource['setup'] = launcher.setup
            
        # TODO: Calculate resources (e.g  #nodes and #cores)

        # Return list of Id of the newly created item
        return jsonify(result = resource, response = 201)
