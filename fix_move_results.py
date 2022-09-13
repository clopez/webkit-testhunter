#!/usr/bin/env python3

import pytest
import os
import json
import sys
from k import revids

CURDIR = os.path.dirname(os.path.abspath(__file__))

VALID_COMMANDFILES = ["newfixed.sh", "newfixed.sh", "newempty.sh", "oldsvn.sh", "keyerrors.sh"]

for command_file in VALID_COMMANDFILES:
    if os.path.exists(command_file):
        os.remove(command_file)
    if os.path.exists("do_diff_"+command_file):
        os.remove("do_diff_"+command_file)


def write_new_updated_result(oldrevision, newrevision, filedata, bot, old_file_name, command_file_name):
    resultsbasedir = os.path.join(CURDIR, "jsonresults")
    filename_ending = "_".join(old_file_name.split("_")[3:])
    assert(filename_ending.startswith("b")) # buildnumber
    assert(filename_ending.endswith(".json"))
    new_file_name = "full_results_%s_%s" %(newrevision, filename_ending)
    print ("[%s] Move from %s to %s" %(bot, old_file_name, new_file_name))
    #json_file_path = os.path.join(resultsbasedir, bot, jsonresult)
    assert(command_file_name in VALID_COMMANDFILES)

    previous_path = os.path.join(resultsbasedir, bot, old_file_name)
    new_path = os.path.join(resultsbasedir, bot, new_file_name)
    with open(command_file_name, "a") as command_file_object:
        command_file_object.write("git rm %s\n" % previous_path)
        command_file_object.write("git add %s\n" % new_path)
    with open("do_diff_"+command_file_name, "a") as command_file_object:
        command_file_object.write('diff -u <(sed "s/,/,\\n/g" %s) <(sed "s/,/,\\n/g" %s)\n' % (previous_path, new_path))
    filedata_parts = filedata.split('"revision"')
    assert(len(filedata_parts) == 2)
    new_file_data = '%s"revision":"%s"});' %(filedata_parts[0], newrevision)
    #print(new_file_data)
    newfiledata_parts = new_file_data.split('"revision"')
    assert(len(newfiledata_parts) == 2)
    #print(filedata_parts[1])
    #print(newfiledata_parts[1])
    destination_dir = os.path.dirname(new_path)
    if not os.path.isdir(destination_dir):
        os.makedirs(destination_dir)
    assert(not os.path.isfile(new_path))
    with open(new_path, "w") as newfile_handle:
        newfile_handle.write(new_file_data)


def test_json_files_are_sanitized():
    resultsbasedir = os.path.join(CURDIR, "jsonresults")
    for bot in os.listdir(resultsbasedir):
        jsonresults = os.listdir(os.path.join(resultsbasedir, bot))
        jsonresults.sort()
        for jsonresult in jsonresults:
            if jsonresult.startswith("full_results_") and jsonresult.endswith('.json'):
                json_file_path = os.path.realpath(os.path.join(resultsbasedir, bot, jsonresult))

                revision_from_filename = jsonresult.split("full_results_")[1].split(".json")[0].split('_')[0]
                # Read file
                json_file = open(json_file_path)
                file_data = json_file.read()
                json_file.close()
                # Clean it
                json_data = file_data.split('ADD_RESULTS(')[1].split(');')[0]
                # Parse it
                try:
                    json_parsed = json.loads(json_data)
                except:
                    raise Exception ('WARNING: Exception parsing file: %s ' % json_file_path)


                revision_from_data = json_parsed['revision']

                # Old SVN numbers
                if revision_from_data.isnumeric():
                    krevision = "r%s" % revision_from_data
                    if krevision == revision_from_filename:
                        try:
                            kid = revids[krevision]
                            print ("Moving from %s to %s" %(krevision, kid))
                            write_new_updated_result(revision_from_data, kid, file_data, bot, jsonresult, "oldsvn.sh")
                        except KeyError:
                            with open("keyerrors.sh", "a") as command_file_object:
                                command_file_object.write("git rm %s\n" % json_file_path)
                            print ("KeyError at %s" %krevision)
                    else:
                        raise ValueError ('WARNING: Parsed revision %s is different than expected one %d for file %s'
                                         %(json_parsed['revision'], revision, json_file_path))
                elif revision_from_data == "None":
                    assert(revision_from_filename.startswith('r'))
                    revision_from_filename = revision_from_filename.lstrip('r')
                    assert(revision_from_filename.endswith('@main'))
                    print ('Fill empty revision with value _None_ from data "%s" with value from file "%s"' %(revision_from_data, revision_from_filename))
                    write_new_updated_result(revision_from_data, revision_from_filename, file_data, bot, jsonresult, "newempty.sh")
                else:
                    print ('Have revision with value from data "%s" and from file "%s"' %(revision_from_data, revision_from_filename))
                    write_new_updated_result(revision_from_data, revision_from_data, file_data, bot, jsonresult, "newfixed.sh")

if __name__ == '__main__':
    sys.exit(test_json_files_are_sanitized())
