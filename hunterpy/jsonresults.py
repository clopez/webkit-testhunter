import os
import sys
import json
import math
import time
from collections import OrderedDict
from multiprocessing import Pool

from hunterpy.definitions import bots, NOERROR, UNKNOWN
from hunterpy.utils import OptionalColorText


class ResultsParser():

    def __init__(self, bot_name, number_of_process, limit_to_last_n_results=None, print_progress=True, print_debug=False, use_color=True):
        self.bot_parsed_results = {}
        self.bot_key_name = bot_name
        self.number_of_process = number_of_process
        self.print_progress = print_progress
        self.print_debug = print_debug
        self.start_at_revision = 1
        self.limit_to_last_n_results = limit_to_last_n_results
        self.maybe_color = OptionalColorText(use_color)
        #self.list_of_json_results_files = self._get_list_of_json_result_files()
        if self.limit_to_last_n_results:
            print ('INFO: Search limited to the last %s known revisions. Pass --all or --depth to search deeper.' % self.maybe_color.bold(self.limit_to_last_n_results))
            self._maybe_recalculate_start_at_revision()


    def _write_progress_message(self, text):
        sys.stderr.write("\r\033[K") # reset line
        sys.stderr.write(text)
        sys.stderr.flush()


    def _get_revision_start_end(self, json_result_files):
        for jsonresult in json_result_files:
            if jsonresult.startswith("full_results_") and jsonresult.endswith('.json'):
                rev_start = int(jsonresult.split("full_results_")[1].split(".json")[0].split('_')[0].rstrip("@main"))
                break
        for jsonresult in json_result_files[::-1]:
            if jsonresult.startswith("full_results_") and jsonresult.endswith('.json'):
                try:
                    rev_end = int(jsonresult.split("full_results_")[1].split(".json")[0].split('_')[0].rstrip("@main"))
                except ValueError:
                    print(jsonresult)
                    raise
                break
        if self.start_at_revision > rev_start:
            rev_start = self.start_at_revision
        return rev_start, rev_end

    def _maybe_recalculate_start_at_revision(self):
        # This assumes the json result file names have the right revision number in and ordered by that
        # The pytest check should ensure that without having to check now at runtime
        if self.limit_to_last_n_results:
            max_rev = 1
            for bot in bots[self.bot_key_name]:
                bot_dir = os.path.join('jsonresults', bot) # fixme: use (readlink -f) with python trick to get an abs path
                if not os.path.isdir(bot_dir):
                    continue
                json_result_files = os.listdir(bot_dir)
                json_result_files.sort()
                rev_start, rev_end = self._get_revision_start_end(json_result_files)
                if rev_end > max_rev:
                    max_rev = rev_end
                min_rev = max_rev - self.limit_to_last_n_results
                if min_rev < 1:
                    min_rev = 1
                if min_rev > self.start_at_revision:
                    self.start_at_revision = min_rev


    def _parse_json_result(self, result_file):
        # Read file
        json_file = open(result_file)
        json_data = json_file.read()
        json_file.close()
        # Clean it
        json_data = json_data.split('ADD_RESULTS(')[1]
        json_data = json_data.split(');')[0]
        # Parse it (exceptions handled in callers)
        return json.loads(json_data)

    def _get_revision_and_buildnumber_for_result(self, result_file):
        revision, buildnumber = result_file.split('full_results_')[1].split('.json')[0].split('_')
        revision = int(revision.rstrip('@main'))
        buildnumber = int(buildnumber.strip('b'))
        return revision, buildnumber

    def _search(self, tests_to_search, bot_name, json_result_files, shouldprint_progress=False):
        ret = {}
        if shouldprint_progress:
            rev_start, rev_end = self._get_revision_start_end(json_result_files)
            count = 0
            percent_search = 0
            threshold = len(json_result_files)/100

        for test in tests_to_search:
            ret[test] = OrderedDict() ## is really needed (or even a good idea) an orderreddict here?

        for jsonresult in json_result_files:
            if shouldprint_progress:
                count += 1
                if count >= threshold:
                    count = 1
                    percent_search += 1
                    if percent_search > 98 :
                        self._write_progress_message('Searching: [%s@main-%s@main][%s] done' % (rev_start, rev_end, bot_name))
                    else:
                        self._write_progress_message('Searching: [%s@main-%s@main][%s] %s%%' % ((rev_start, rev_end, bot_name, percent_search)))

            revision, buildnumber = self._get_revision_and_buildnumber_for_result(jsonresult)

            if revision < self.start_at_revision:
                if self.print_debug: print ('Skipping file %s because its rev number %s is lower than start_at_revision %s\n' % (jsonresult, revision, self.start_at_revision))
                continue

            try:
                json_parsed = self._parse_json_result(os.path.join('jsonresults', bot_name, jsonresult))
            except json.JSONDecodeError:
                if self.print_debug: print ('WARNING: Exception caused by file: %s Ignoring file.' % os.path.join('jsonresults', bot_name, jsonresult))
                continue

            if self.print_debug and revision in ret[test]:
                print ('WARNING: Data for revision %d duplicated. Picking last\n' % revision)

            keytest = json_parsed['tests']

            for test in tests_to_search:
                ret[test][revision] = {}
                test_path_parts = test.split('/')
                try:
                    for test_path_part in test_path_parts:
                        keytest = keytest[test_path_part]
                except KeyError:
                    # This test didn't failed (or wasn't ran) on this rev.
                    if json_parsed['interrupted']:
                        # If the whole set of tests didn't finished, mark it as unknown.
                        if self.print_debug: print ("On revision %s the test set didn't finished." % (revision))
                        ret[test][revision]['result'] = UNKNOWN
                    else:
                        # Otherwise, mark it as noerror.
                        ret[test][revision]['result'] = NOERROR
                    continue

                ret[test][revision]['result'] = keytest['actual']
                if 'expected' in keytest:
                    ret[test][revision]['expected'] = keytest['expected']
        return ret  # returns dict[tests][revisions]


    def _recursive_test_path_value_finder(self, dict_data, tests, revision, current_test_path=None):
        for dict_key in dict_data:
            if not current_test_path:
                test_path = dict_key
            else:
                test_path = current_test_path + "/" + dict_key
            if set(['expected', 'actual']).issubset(dict_data[dict_key].keys()):
                if test_path not in tests:
                    tests[test_path] = OrderedDict() #fixme?
                # In case of several runs for the same revision we are picking just the last
                tests[test_path][revision] = {}
                tests[test_path][revision]['result'] = dict_data[dict_key]['actual']
                tests[test_path][revision]['expected'] = dict_data[dict_key]['expected']
                # IMPLEMENT:
                # translate values and simplify them -> "[TEXT|IMAGE+TEXT|AUDIO]==FAIL"
                # we need some tests for the functions, implement those with predefined set of revs
                #tests[test_path][revision]['result'] = self._translate_result_values_to_set(dict_data[dict_key]['actual'])
                #tests[test_path][revision]['expected'] = self._translate_result_values_to_set(dict_data[dict_key]['expected'])
            else:
                self._recursive_test_path_value_finder(dict_data[dict_key], tests, revision, test_path)
        return tests


    def get_list_of_failed_tests_at_last_n_runs(self, number_of_last_n_results_to_check=1):
            last_rev = 0
            failed_tests = {}
            revisions_with_runs = []
            for bot_name in bots[self.bot_key_name]:
                if not self._bot_has_jsonresults(bot_name):
                    continue
                json_result_files = self._get_sorted_list_of_jsonresults(bot_name)
                rev_start, rev_end = self._get_revision_start_end(json_result_files)
                if rev_end > last_rev:
                    last_rev = rev_end
                    last_bot = bot_name
                    last_json_result_files = json_result_files
            assert(len(last_json_result_files) > number_of_last_n_results_to_check)

            for result in reversed(last_json_result_files):
                revision, buildnumber = self._get_revision_and_buildnumber_for_result(result)
                try:
                    json_parsed = self._parse_json_result(os.path.join('jsonresults', last_bot, result))
                    tests_data = json_parsed['tests']
                    failed_tests = self._recursive_test_path_value_finder(tests_data, failed_tests, revision)
                    revisions_with_runs.insert(0, revision)
                except json.JSONDecodeError:
                    if self.print_debug: print ('WARNING: Exception caused by file: %s. Continuing to next result' % result_file)
                    continue
                if len(revisions_with_runs) >= number_of_last_n_results_to_check:
                    break
            return revisions_with_runs, failed_tests


    def _merge_results(self, search_results):
        for test in search_results:
            for revision, test_results in search_results[test].items():
                self.bot_parsed_results[test][revision] = test_results

    def get_available_revisions_with_results(self, report_only_finished=True):
        raise NotImplementedError

    def get_list_of_tests_with_unexpected_results_at_revision(self, revision):
        raise NotImplementedError

    def _bot_has_jsonresults(self, bot_name):
        bot_dir = os.path.join('jsonresults', bot_name) # fixme: use (readlink -f) with python trick to get an abs path
        if not os.path.isdir(bot_dir):
            return False
        json_result_files = []
        for file in os.listdir(bot_dir):
            if file.startswith('full_results_') and file.endswith('.json'):
                return True
        return False

    def _get_sorted_list_of_jsonresults(self, bot_name):
        bot_dir = os.path.join('jsonresults', bot_name) # fixme: use (readlink -f) with python trick to get an abs path
        assert(os.path.isdir(bot_dir))
        json_result_files = []
        for file in os.listdir(bot_dir):
            if file.startswith('full_results_') and file.endswith('.json'):
                json_result_files.append(file)
        json_result_files.sort()
        assert(len(json_result_files) > 1)
        return json_result_files

    # FIXME: instead of for test in test_to_search pass the list of tests to search() to make the looking fo files more efficient and change how the dict is returned
    def get_results_for_tests(self, tests_to_search):
        assert (isinstance(tests_to_search, list))
        #if self.bot_parsed_results:
        #    return self.bot_parsed_results
        # fixme: the return of tuples below to fix above

        # Early init of the entries due to merge usage
        for test in tests_to_search:
            self.bot_parsed_results[test] = OrderedDict() ## is really needed (or even a good idea) an orderreddict here?
            test_path_parts = test.split('/')
            if len(test_path_parts) < 2 or '.' not in test_path_parts[len(test_path_parts) - 1]:
                raise ValueError('Test should be in the format path/test.html. Only one test accepted as parameter (no wildcards or directories)')

        for bot_name in bots[self.bot_key_name]:
            if not self._bot_has_jsonresults(bot_name):
                continue
            json_result_files = self._get_sorted_list_of_jsonresults(bot_name)
            rev_start, rev_end = self._get_revision_start_end(json_result_files)
            if self.start_at_revision > rev_end:
                if self.print_debug: print('Skipped bot: [%s@main-%s@main][%s] (start_at_revision great than last result for bot)' % (rev_start, rev_end, bot_name))
                continue
            if self.number_of_process == 1:
                self._merge_results(self._search(tests_to_search, bot_name, json_result_files, self.print_progress))
            else:
                # Split job in several workers.
                pool = Pool(processes=self.number_of_process)
                size = len(json_result_files)
                stride = int(math.ceil(size/self.number_of_process))
                results = list()
                for i in range(0, self.number_of_process):
                    start, end = i*stride, (i+1)*stride
                    if end > size:
                        end = size
                    results.append(pool.apply_async(self._search, (tests_to_search, bot_name, json_result_files[start:end])))
                # Join workers and merge results.
                pool.close()
                if self.print_progress:
                    while True:
                        complete_count = sum(1 for x in results if x.ready())
                        if complete_count == self.number_of_process:
                            self._write_progress_message('Searching: [%s@main-%s@main][%s] done' % (rev_start, rev_end, bot_name))
                            break
                        self._write_progress_message('Searching: [%s@main-%s@main][%s] %s%%' %(rev_start, rev_end, bot_name, int(complete_count*100/self.number_of_process)))
                        time.sleep(0.25)
                pool.join()
                for each in results:
                    self._merge_results(each.get())

            for test in tests_to_search: # FIXME! (this foor loop is wrong for flakyhunter)
                if len(tests_to_search) != 1:
                    print ("\n\nWARNING: foor loop for multiple tests still not fixed\n\n") # see above
                self._write_progress_message("") # reset write progress message
                if len(self.bot_parsed_results[test]) == 0:
                    raise RuntimeError('ERROR: No revisions fetched for bot: %s Please run the fetch script.' % self.bot_key_name)
                keys = list(self.bot_parsed_results[test].keys())
                keys.sort()
                minrev, maxrev = keys[0], keys[len(keys) - 1]
                startrev = max(minrev, self.start_at_revision)
                if startrev > maxrev:
                    raise RuntimeError('The starting revision %d@main is great than the last revision with data %d@main\nPlease fetch more data before continuing...' %(startrev, maxrev))

        return startrev, minrev, maxrev, self.bot_parsed_results


# This class has helpers for interpreting the parsed results (not the reults from the raw json file)
class ResultsInterpreter():

    @staticmethod
    def is_result_for_test_unexpected(test_data_result_and_expected):
        if set(['expected', 'result']).issubset(test_data_result_and_expected.keys()):
            for test_result in test_data_result_and_expected['result'].split(" "):
                if ( (test_result not in test_data_result_and_expected['expected']) and # we check also for "[TEXT|IMAGE+TEXT|AUDIO]==FAIL"
                    ( (test_result not in ('TEXT', 'IMAGE+TEXT', 'AUDIO')) or ('FAIL' not in test_data_result_and_expected['expected']) ) ):
                    return True
        return False

