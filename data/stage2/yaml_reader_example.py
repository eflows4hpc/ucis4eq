import yaml

with open('input_definition_dt0.001.yaml') as f:
    data = yaml.full_load(f)
    

with open("example.dt0.001.srf", "w") as f:
   f.write(data['rupture'])
