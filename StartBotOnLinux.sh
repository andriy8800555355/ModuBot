#!/bin/bash

# Directory of the script
script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate the virtual environment
source "$script_dir/Linux/bin/activate"

# Change directory to where your app.py is located
cd "$script_dir"

# Start your app.py script
python app.py

# Deactivate the virtual environment
deactivate

