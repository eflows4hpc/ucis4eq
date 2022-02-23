"""This is init module."""

################################################################################
# Module imports
from pymongo import MongoClient
import json
from . import staticDataAccess as SDA
from . import webDavRepository as WebDavRepo
from . import SSHRepository as SSHRepo
from . import localRepository as LocalRepo

# Define the supported list of repositories
repositories = SDA.SDAProvider()

# Register each data repository
repositories.registerBuilder('BSC_B2DROP', WebDavRepo.BSCB2DROPRepositoryBuilder())
repositories.registerBuilder('BSC_DT', SSHRepo.BSCDTRepositoryBuilder())
repositories.registerBuilder('ETH_DAINT', SSHRepo.ETHDAINTRepositoryBuilder())
repositories.registerBuilder('LOCAL', LocalRepo.LocalRepositoryBuilder())

# Start a Mongo client
mongoDB = MongoClient('localhost', 27017)

# Database Name
database = mongoDB['UCIS4EQ']

# Define entry point document for static mapping
StaticDataMappingDocument = "StaticDataMapping"
repository = "BSC_B2DROP" 

# Load DAL setting for all services so all services can access to repositories
config = None
try:
    with open("/opt/DAL.json", 'r') as f:
        config = json.load(f)
except:
    print("WARNING: There is not information available for accessing data repositories, check /opt/DAL.json file.")
