#!/usr/bin/env python3
#
# Slip generation
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
import uuid
import random
from bson.json_util import dumps

# Third parties
from flask import jsonify

# Internal
import ucis4eq
import ucis4eq.dal as dal
from ucis4eq.misc import config, microServiceABC, scriptABC
from ucis4eq.dal import staticDataMap

################################################################################
# Methods and classes

class SlipGenSubmision(scriptABC.ScriptABC):
    
    # Build the submission script
    def build(self, image, path, args, resources):
        # Obtain Header 
        self._getHeader()

        # Obtain Slurm rules
        r = resources
        
        # TODO: Change this depending of the target environment queue system
        self._getSlurmRules(r['wtime'], r["nodes"], r["tasks"], 
                            r["tasks-per-node"], r["qos"])

        # Additional instructions
        self.lines.append("module load singularity")
        self.lines.append("")

        # Build command
        cmd = []
        cmd.append("singularity exec --bind $PWD:/workspace " + image + " /opt/scripts/launcher.sh " 
                   + args)

        self.lines.append(" ".join(cmd))

        # Save the script to disk
        return self._saveScript(path)

class SlipGenSubmision():
         
    # Job submission
    def submit(self):
        pass

@staticDataMap.build
class SlipGenGP(microServiceABC.MicroServiceABC):
        
    # Mai-Beroza relations
    def _MaiBerozaRelations(self, mw, lat, lon, depth):
        
        log_Mo = (mw*1.5)+9.05
        
        relations = {}
        
        relations['FAULT_LENGTH'] = 10**(-6.13 + (0.39*log_Mo))
        relations['FAULT_WIDTH'] = 10**(-5.05 + (0.32*log_Mo))
        relations['DEPTH_TO_TOP'] =  depth/1000 - (relations['FAULT_WIDTH']/2)
        relations['LAT_TOP_CENTER'] = lat
        relations['LON_TOP_CENTER'] = lon
        relations['HYPO_ALONG_STK'] = 0.0
        relations['HYPO_DOWN_DIP'] = relations['FAULT_WIDTH']/2

        return relations

    # Service's entry point definition
    @config.safeRun
    def entryPoint(self, body):
        """
        Call the Graves-Pitarka slip generator
        """
        # Initialization
        result = {}

        # Creating the repository instance for data transfer    
        # TODO: Select the repository from the DB 'Resources' document
        dataRepo = dal.repositories.create('BSCDT', **dal.config)
        
        # Generate an UUID for the current slip generation
        self.uuid = str(uuid.uuid1())
        result['id'] = self.uuid
        
        # Create local directories
        path =  ucis4eq.workSpace + "/scratch/outdata/" + result['id'] + "/"
        cmt = body['CMT']
        
        os.makedirs(path, exist_ok=True)
        
        # Create the input parameter for slip-gen
        image = self.filePing['slipgen.singularity']

        # Read the input catalog from file
        region = ucis4eq.dal.database.Regions.find_one({"id": body['region']})
        setup = region['GPSetup']
            
        # Define Source file
        source = path + result['id'] + ".src"
        
        # Generate GP source file
        srcParams = self._MaiBerozaRelations(body['magnitude'], body['latitude'], 
                                  body['longitude'], body['depth'] )

        srcParams['MAGNITUDE'] = body['magnitude']                                     
        srcParams['STRIKE'] = cmt['strike']                        
        srcParams['RAKE'] = cmt['rake']
        srcParams['DIP'] = cmt['dip']
        
        srcParams['DWID'] = setup['dwid']
        srcParams['DLEN'] = setup['dlen']
        srcParams['CORNER_FREQ'] = setup['corner_freq']
        
        srcParams['SEED'] = random.randint(1, 9999999)

        with open(source, 'w') as fd:
            for key in srcParams.keys():
                fd.write(key + ' = ' + str(srcParams[key]) + '\n')
        
        # Include an initial slip distribution
        initSlip = ""
        if "initSlip" in cmt.keys():
            initSlip = " -i " + \
                        os.path.basename(self.fileMapping[cmt['initSlip']]) \
                        + " -a 1.0"
                
        # Start running the triggering system 
        #args = "-o " + result['id'] + " -v " + self.fileMapping[setup['model']] + " -s " + source + " -i " + self.fileMapping["initSlip21june2000"] + " -a 0.99 > /dev/null 2>&1"
        args = "-o . " + " -v " \
                + os.path.basename(self.fileMapping[setup['model']]) \
                + " -s " + os.path.basename(source) + initSlip \
                + "> /dev/null 2>&1"
        

        # Generate Submission script
        # TODO: This is hardcoded by right now but should be parametrized
        resources = {'wtime': 360, 'nodes': 1, 'tasks': 1, 'tasks-per-node': 1, 
                     'qos': 'debug'}             
                     
        script = SlipGenSubmision(uuid=self.uuid).build(image, path, args, resources)
    
        # Create the remote working directory
        workpath = self.uuid + "/" + "slipgen"
        dataRepo.mkdir(workpath)
        
        # Transfer source, script, model and init slip (if there is one)
        dataRepo.uploadFile(workpath, script)
        dataRepo.uploadFile(workpath, source)
        if "initSlip" in cmt.keys():        
            dataRepo.uploadFile(workpath, self.fileMapping[cmt['initSlip']])
            
        dataRepo.uploadFile(workpath, self.fileMapping[setup['model']])
                            
        # Return list of Id of the newly created item
        # TODO: Return the SRF in plain text 
        return jsonify(result = result, response = 201)

        # TODO: Instead of running the GP rupture generator, build the submission script
        #os.system("/bin/bash -c '/root/scripts/launcher.sh " + args + "'")
        #
        ## Read the generated SRF
        #with open(path + result['id'] + ".srf", encoding="utf-8") as f:
        #    #result['slipmodel'] = f.readlines();
        #    result['slipmodel'] = f.read().splitlines()
