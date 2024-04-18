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
# System
import sys
import traceback
import json
import yaml
from bson.json_util import dumps

# Third parties
from flask import jsonify

# Internal
from ucis4eq.misc import config, microServiceABC
import ucis4eq as ucis4eq
from ucis4eq.dal import staticDataMap, dataStructure

################################################################################
# Methods and classes

@staticDataMap.build
class InputParametersBuilder(microServiceABC.MicroServiceABC):

    # Initialization method
    def __init__(self):
        """
        Initialize the CMT statistical component implementation
        """

        # Select the database
        self.db = ucis4eq.dal.database

        # Set input parameters for the wrapper categories
        self.general = {}
        self.source = {}
        self.geometry = {}
        self.rupture = {}
        self.receivers = {}

    # Service's entry point definition
    @microServiceABC.MicroServiceABC.runRegistration
    def entryPoint(self, body):
        """
        Build the set of simulation parameters
        """
        # Initialize inputP dict
        inputP = {}
                        
        # Select target machine
        machine = body['resources']
        
        # Set repository
        self.setMainRepository(machine['repository'])        
        
        # Create the data structure
        regionName = body['region']['id']
        dformat =  body['region']['file_structure']
        dataFormat = dataStructure.formats[dformat]()
        dataFormat.prepare(regionName)    
        
        # Select an available ensamble
        receiversFileName = body['region']['path'] + "/" + dataFormat.getPathTo('receivers') + \
                            "/receivers.json"
                            
        # Read the input from file 
        with open(receiversFileName, 'r') as f:
            receivers = json.load(f)
        
        # Create the data structure
        regionName = body['region']['id'] + "_DATA"
        dataFormat = dataStructure.formats[dformat]()
        dataFormat.setMainRepository(machine['repository'])
        dataFormat.prepare(regionName)
        
        # Build the set of parameters in a YAML
        # TODO
        self.general['fmax_in_hz'] = body['setup']['freq']
        self.general['generate_mesh'] = "no"
        self.general['overwrite_mesh_path'] = "no"

        self.geometry['coordinates'] = {} 
        self.geometry['coordinates']['max_latitude']  = body['region']['max_latitude']
        self.geometry['coordinates']['max_longitude'] = body['region']['max_longitude']
        self.geometry['coordinates']['min_latitude']  = body['region']['min_latitude']
        self.geometry['coordinates']['min_longitude'] = body['region']['min_longitude']        
        self.geometry['coordinates']['depth_in_m']    = body['region']['depth_in_m']        
        self.geometry['region_ID'] = body['region']['id']
    
        paths = {}
        
        paths['mesh_precomputed'] = dataFormat.getPathTo('meshes', [str(body['setup']['freq']), ".h5"])
        paths['mesh_onthefly'] = ""
        paths['velocity_model'] = dataFormat.getPathTo('velocity_model')
        if not paths['velocity_model']:
            paths['velocity_model'] = "csem"
            
        paths['topography'] = dataFormat.getPathTo('topography', ["topography"])
        paths['bathymetry'] = dataFormat.getPathTo('bathymetry')

        # MPC in the case of precomputed meshes you don't actaully need the topo and bathy files,
        # as the mesh already includes them. It is worth to have them for reproducibility, but we just
        # add this as a warning here rather than making it a blocking point for simulations.
        if not paths['topography'] and paths['mesh_precomputed']:
            print("WARNING: the topography file was not found, "
                  "but the precomputed mesh is assumed to include the topography.")
            paths['topography'] = " "

        if not paths['bathymetry'] and paths['mesh_precomputed']:
            print("WARNING: the bathymetry file was not found, "
                  "but the precomputed mesh is assumed to include the bathymetry.")
            paths['bathymetry'] = " "

        self.geometry['filepaths'] = paths
    
        if (body['ensemble'] == "statisticalCMT") or (body['ensemble'] == "onlyOne") :
            self.source['magnitude'] = body['event']["magnitude"]
            self.source['longitude'] = body['event']["longitude"]
            self.source['latitude'] = body['event']["latitude"]
            self.source['depth'] = body['event']["depth"]
            self.source['strike'] = body["CMT"]["strike"]
            self.source['rake'] = body["CMT"]["rake"]
            self.source['dip'] = body["CMT"]["dip"]
        elif body['ensemble'] == "seisEnsMan":
            self.source['magnitude'] = body['CMT']["magnitude"]
            self.source['longitude'] = body['CMT']["longitude"]
            self.source['latitude'] = body['CMT']["latitude"]
            self.source['depth'] = body['CMT']["depth"]
            self.source['strike'] = body["CMT"]["strike"]
            self.source['rake'] = body["CMT"]["rake"]
            self.source['dip'] = body["CMT"]["dip"]
        else:
            raise Exception("not recognized ensemble")

        self.rupture['filename'] = body["rupture"]

        for receiverType in receivers.keys():
            if not receiverType == "id" and not receiverType == "_id":
                self.receivers[receiverType] = receivers[receiverType]

        # Prepare YAML sections
        inputP = self.general
        inputP["geometry"] = self.geometry
        inputP["CMT_source"] = self.source
        inputP["rupture"] = self.rupture
        inputP["receivers"] = self.receivers    

        # Return list of Id of the newly created item
        return jsonify(result = inputP, response = 201)
