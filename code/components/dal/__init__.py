"""This is init module."""

################################################################################
# Module imports
from pymongo import MongoClient
import json
from . import staticDataAccess as SDA
from . import b2dropRepository as B2DropRepo
from . import BSCDTRepository as BSCDTRepo
from . import localRepository as LocalRepo

# Define the supported list of repositories
repositories = SDA.SDAProvider()

# Register each data repository
repositories.registerBuilder('B2DROP', B2DropRepo.B2DropRepositoryBuilder())
repositories.registerBuilder('BSCDT', BSCDTRepo.BSCDTRepositoryBuilder())
repositories.registerBuilder('LOCAL', LocalRepo.LocalRepositoryBuilder())

# Start a Mongo client
mongoDB = MongoClient('localhost', 27017)

# Database Name
database = mongoDB['UCIS4EQ']

# Define entry point document for static mapping
StaticDataMappingDocument = "StaticDataMapping"

# Load DAL setting for all services so all services can access to repositories
config = None
try:
    with open("/opt/DAL.json", 'r') as f:
        config = json.load(f)
except:
    print("WARNING: There is not information available for accessing data repositories, check /opt/DAL.json file.")
