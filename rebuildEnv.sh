#!/bin/bash
deactivate; rm -rf venv/; virtualenv venv -p python3; source venv/bin/activate; pip install -r requirements.txt
