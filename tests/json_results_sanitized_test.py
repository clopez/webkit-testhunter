#!/usr/bin/env python3

import pytest
import os
import sys
sys.path.append("..")
import imp
import json
curdir = os.path.dirname(os.path.abspath(__file__))
wktesthunter = imp.load_source('wktestunter', os.path.join(curdir,'..','wktesthunter'))
from wktesthunter import *

def test_json_files_are_sanitized():
    resultsbasedir = os.path.join(curdir, "..", "jsonresults")
    for bot in os.listdir(resultsbasedir):
        jsonresults = os.listdir(os.path.join(resultsbasedir, bot))
        jsonresults.sort()
        for jsonresult in jsonresults:
            if jsonresult.startswith("full_results_") and jsonresult.endswith('.json'):
                json_file_path = os.path.realpath(os.path.join(resultsbasedir, bot, jsonresult))
                print ("Checking %s " % json_file_path)
                revision = jsonresult.split("full_results_")[1].split(".json")[0].split('_')[0]
                revision=int(revision.strip('r'))
                # Read file
                json_file=open(json_file_path)
                json_data=json_file.read()
                json_file.close()
                # Clean it
                json_data=json_data.split('ADD_RESULTS(')[1]
                json_data=json_data.split(');')[0]
                # Parse it
                try:
                    json_parsed = json.loads(json_data)
                except:
                    raise Exception ("WARNING: Exception parsing file: %s " % json_file_path)

                # Check that revision on filename matches revision on json data
                if int(json_parsed['revision']) != revision:
                    raise ValueError ("WARNING: Parsed revision %s don't match expected one %d for file %s"
                                     %(json_parsed['revision'], revision, json_file_path))


if __name__ == '__main__':
    sys.exit(test_json_files_are_sanitized())
