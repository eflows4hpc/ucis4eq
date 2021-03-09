#!/usr/bin/env python3
#
# Abstract factory for accessing storage repositories
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

################################################################################
# Module imports
#from __future__ import annotations
import os
from abc import ABC, abstractmethod

import ucis4eq
import ucis4eq.dal as dal
from ucis4eq.misc import config, microServiceABC

################################################################################
# Methods and classes
        
class StaticDataMap():
    "Static data file mapping"
    
    def __init__(self, name):
        """
        Initialization
        """
        
        # Obtain data from an external repository
        col = dal.database[dal.StaticDataMappingDocument]
        query = { "used_by": {"$eq": name} } 
        docs = col.find(query)
            
        # Files map
        self._values = {}
        for doc in docs:
            self._values[doc['id']] = doc
            
        # Instantiated repositories    
        self.repos = {}
        
        # Base path for downloads
        self.workSpace = ucis4eq.workSpace + name + "/"
        
        # Create a directory where download data
        os.makedirs(self.workSpace, exist_ok=True)
        

    def __getitem__(self, name):
        
        # Select the document to obtain
        doc = self._values[name]
                
        # Check if the current repository was created
        repoName, repoSettings = dal.repositories.selectFrom(doc['repositories'])
        
        if not repoName in self.repos.keys():                            
            # Find the repository type
            col = dal.database["Repositories"]
            query = { "id": {"$eq": repoName} } 
            repoSetting = col.find_one(query)
            
            # Store the current repository object
            self.repos[repoName] = dal.repositories.create(repoSetting['type'], **dal.config)
        
        # Handle remote and local paths
        rpath = repoSettings['path']
        lpath = self.workSpace + os.path.basename(rpath)

        # Download the file from the repository (only if it doesn't exist)
#        if not os.path.exists(lpath):            
        # Download the file            
        self.repos[repoName].downloadFile(rpath, lpath)
            
        # Return the file path
        return lpath

    def __iter__(self):
        return iter(self._values)

    def keys(self):
        return self._values.keys()

    def items(self):
        return self._values.items()

    def values(self):
        return self._values.values()
        
def build(cls):
    "Static data file mapping"
    class BuildStaticDataMap(cls):

        def __init__(self, *args, **kargs):
            
            # Initialize base class
            super(BuildStaticDataMap, self).__init__(*args, **kargs)
            
            # Obtain the basename class name 
            className = self.__class__.__bases__[0].__name__
                                
            # Build the file mapping
            self.fileMapping = StaticDataMap(className)
        

    return BuildStaticDataMap
