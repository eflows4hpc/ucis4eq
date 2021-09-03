"""This is init module."""

################################################################################
# Module imports

import json

from ucis4eq.misc.factory import Provider 
from . import localRunner as LocalRunner
from . import slurmRunner as SlurmRunner

# Create the launcher's registry
launchers = Provider()

# Register each data repository
launchers.registerBuilder('LOCAL', LocalRunner.LocalRunnerBuilder())
launchers.registerBuilder('MN4', SlurmRunner.MN4RunnerBuilder())

# Load computational sites setting
config = None
with open("/opt/Sites.json", 'r') as f:
    config = json.load(f)
