#!/bin/bash

git clone https://github.com/cfpb/collab.git

mv collab/collab/local_settings_template.py collab/collab/local_settings.py

echo "INSTALLED_APPS += ('form_builder', )" >> collab/collab/local_settings.py

pip install -r collab/requirements.txt
pip install -r collab/requirements-test.txt

cd collab
ln -s ../src/form_builder
