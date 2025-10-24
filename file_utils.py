
from pathlib import Path


def is_float(n):   
    if isinstance(n, int):
        return False
    if("." not in n): 
        #print(n)
        return False
    try:        
        float(n)        
        return True    
    except:        
        return False

def is_int(n):   
    try:        
        int(n)        
        return True    
    except:        
        return False

def load_parameters(filename):
    print("load_parameters: " +filename)
    parameters = {}
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if not line:  # skip empty lines
                continue
            if line.startswith("#"):
                continue
            if "=" not in line: # skip invalid lines
                continue
            key, value = line.split('=')
            key = key.strip()
            value = value.strip()
            variable_type = "string"
            if not value: # skip empty configuration parameters
                continue
            if(is_float(value)):
                value = float(value)    
                variable_type = "float"
            else:
                if(is_int(value)):
                    value = int(value)
                    variable_type = "int"
            parameters[key] = value
            print(str(key)+ " = "+ str(value) + " ["+ variable_type+ "]")
    return parameters

def get_files(directory):
    path = Path(directory)
    file_list = sorted(path.glob("*"))
    return file_list
