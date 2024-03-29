#!/usr/bin/env python3

import pytest
import os
import json

CURDIR = os.path.dirname(os.path.abspath(__file__))

def test_json_files_are_sanitized():
    resultsbasedir = os.path.join(CURDIR, "..", "jsonresults")
    for bot in os.listdir(resultsbasedir):
        jsonresults = os.listdir(os.path.join(resultsbasedir, bot))
        jsonresults.sort()
        for jsonresult in jsonresults:
            if jsonresult.startswith("full_results_") and jsonresult.endswith('.json'):
                json_file_path = os.path.realpath(os.path.join(resultsbasedir, bot, jsonresult))
                print ('Checking %s ' % json_file_path)
                revision_from_filename = jsonresult.split("full_results_")[1].split(".json")[0].split('_')[0]
                # Read file
                json_file = open(json_file_path)
                file_data = json_file.read()
                json_file.close()
                # Clean and parse it
                json_data = file_data.split('ADD_RESULTS(')[1].split(');')[0]
                # Parse it
                try:
                    json_parsed = json.loads(json_data)
                except:
                    raise Exception ('WARNING: Exception parsing file: %s ' % json_file_path)

                # Check that revision on filename matches revision on json data
                if json_parsed['revision'] != revision_from_filename or len(revision_from_filename) < 8 or not revision_from_filename.endswith('@main'):
                    raise ValueError ('WARNING: Parsed revision %s is different than expected one %s for file %s'
                                     %(json_parsed['revision'], revision_from_filename, json_file_path))


if __name__ == '__main__':
    sys.exit(test_json_files_are_sanitized())
