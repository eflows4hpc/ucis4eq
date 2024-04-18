#!/usr/bin/env python3

# Abstract factory for accessing storage repositories
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

from pymongo import MongoClient
import os
import json

from flask import jsonify

import ucis4eq
import ucis4eq.dal as dal
from ucis4eq.dal import staticDataAccess
from ucis4eq.misc import config, microServiceABC

# ###############################################################################
# Methods and classes

class DAL(microServiceABC.MicroServiceABC):
    
    # Initialization method
    def __init__(self):
        """
        Initialize the DAL service
        """

    # Service's entry point definition
    @config.safeRun
    def entryPoint(self, repositoryName = dal.repository):
            
        repository = staticDataAccess.repositories.create(repositoryName, **dal.config)
        
        # Create a directory for DAL documents 
        workSpace = ucis4eq.workSpace + "/DAL/"
        os.makedirs(workSpace, exist_ok=True)    
        
        # Download the file from the repository
        rpath = dal.config[repositoryName]["datamapping"]
        rfile = os.path.basename(rpath)
        lpath = workSpace + rfile
        
        repository.downloadFile(rpath, lpath)

        # Alias for the static data mapping and DB
        db = dal.database
        
        # Create collection (Remove previous one)
        db[dal.StaticDataMappingDocument].drop()
        col = self._createCollection(db, lpath,
                dal.StaticDataMappingDocument)
        
        # Obtain the set of documents needed by the UCIS4EQ before start serving
        dalDocs = { "used_by": {"$eq": "DALService"} }
        docs = col.find(dalDocs)
        
        for doc in docs:
            repo, repoSettings = staticDataAccess.repositories.selectFrom(doc['repositories'],
                    repositoryName)
            rpath = repoSettings['path']
            rfile = os.path.basename(rpath)
            lpath = workSpace + rfile
                
                
            # Download the file from the repository
            if not os.path.exists(lpath):
                print("Downloading file: " + lpath, flush=True)
                repository.downloadFile(rpath, lpath)

            # Create collection
            col = self._createCollection(db, lpath)

        # Return success
        return jsonify(result = {}, response = 201)

    def _createCollection( self, db, documentsPath, collectionName=None):
        """
        This method will create a collection of documents in the given MongoDB
        """
        
        # Obtain the collection name if not provided
        if not collectionName:
            collectionName = os.path.splitext(os.path.basename(documentsPath))[0]
            
        # Define the collection
        collection = db[collectionName]
        
        # Insert all registries
        if documentsPath.endswith(".json"):

            try:
                with open(documentsPath, "r", encoding="utf-8") as f:
                    fdata = json.load(f)
            except ValueError:
                raise Exception('Decoding JSON file ' + documentsPath + ' has failed')
                        
            # Get the set of collections already set in DAL
            list = collection.distinct( "id" )

            if "documents" in fdata:
                ## Insert the new ones
                for item in fdata['documents']:
                    if not item['id'] in list:
                        collection.insert_one(item)
            else:
                ## Insert the new ones
                for item in fdata['docFuments']:
                    if not item['id'] in list:
                        collection.insert_one(item)

        return collection
