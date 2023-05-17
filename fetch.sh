#!/bin/bash
set -eu

WEBKIT_RESULTS_URL="http://build.webkit.org/results"

# The GTK test bot is now "GTK Linux 64-bit Release (Tests)".
# The others were the names of this test bot in the past.
# We fetch all the data from the actual test bot as also the past ones, to have a complete history
declare -A webkitbots_map
webkitbots_map=(
   ["gtk-release"]="GTK-Linux-64-bit-Release-Tests"
   ["gtk-debug"]="GTK-Linux-64-bit-Debug-Tests"
   ["gtk-release-wayland"]="GTK-Linux-64-bit-Release-Wayland-Tests"
   ["gtk-release-gtk4"]="GTK-Linux-64-bit-Release-GTK4-Tests"
   ["gtk-release-skip-failing"]="GTK-Linux-64-bit-Release-Skip-Failing-Tests"
   ["wpe-release"]="WPE-Linux-64-bit-Release-Tests"
   ["wpe-debug"]="WPE-Linux-64-bit-Debug-Tests"
)

webkitbots_values=("${webkitbots_map[@]}")

fatal () {
    echo "Fatal: $@"
    exit 1
}

usage () {
   local exit_code="$1"
   local program_name=$(basename "$0")

   echo "$program_name [BOT] ..."
   echo "Retrieves tests data from a set of bots. In case no bot is set, data is retrieved from all bots."
   echo ""
   echo "ARGUMENTS:"
   echo -e "\tBOT\t${!webkitbots_map[@]}"

   exit $exit_code
}

urlencode () {
    python -c "import urllib; print urllib.quote(\"${@}\")"
}

urldecode () {
    python -c "import urllib; print urllib.unquote(\"${@}\")"
}

print_revision_from_json_results () {
    python -c "import json, os; json_data=open(\"${1}\").read().split('ADD_RESULTS(')[1].split(');')[0]; print(json.loads(json_data)['revision'])"
}

json_result_test_has_revision_key () {
    python -c "import json, os, sys; jd=json.loads(open(\"${1}\").read().split('ADD_RESULTS(')[1].split(');')[0]); exit_code = 0 if 'revision' in jd.keys() else 1; sys.exit(exit_code)"
}

json_result_test_run_was_interrupted () {
    python -c "import json, os, sys; jd=json.loads(open(\"${1}\").read().split('ADD_RESULTS(')[1].split(');')[0]); exit_code = 0 if 'interrupted' in jd.keys() and jd['interrupted'] else 1; sys.exit(exit_code)"
}

fetch_bot_results () {
    local webkitbot="$1"

    curl -L -s "${WEBKIT_RESULTS_URL}/${webkitbot}/" | grep -P "href=\"[^\"]+/"| cut -d\" -f2 | grep -v  "\.\./" | sort -u
}

parse_args () {
    local values=()
    for arg in $@; do
        if [[ "$arg" == "-h" || "$arg" == "--help" ]]; then
            usage 0
        elif [[ "$arg" == -* ]]; then
            fatal "Unrecognized option: '$arg'"
        # Is a valid bot identifier?
        elif [[ " ${!webkitbots_map[@]} " =~ " $arg " ]]; then
            values+=( "${webkitbots_map[$arg]}" )
        else
            fatal "Invalid argument: '$arg'"
        fi
    done
    # Override default webkitbots_values.
    if [[ ${#values[@]} -gt 0 ]]; then
        webkitbots_values=("${values[@]}")
    fi
}

parse_args $@

alreadytried=".cache_already_tried"
islegacybot=".is_legacy_bot"
cd jsonresults
for webkitbot in "${webkitbots_values[@]}"; do
    test -d "${webkitbot}" || mkdir "${webkitbot}"
    cd "${webkitbot}"
    if test -f "${islegacybot}"; then
        echo -e "\nFetching results for bot ${webkitbot} skipped because this bot is not longer active and we already have all the results for it fetched."
        echo -e "If this is not the case, then please remove the file $(pwd)/${islegacybot} and run this script again."
        cd ..
        continue
    else
        echo -e "\nFetching results for bot: ${webkitbot}"
    fi
    test -f "${alreadytried}" || touch "${alreadytried}"
    tempjsonresultfile="$(mktemp)"
    webkitbot="$(urlencode "${webkitbot}")"
    fetch_bot_results "$webkitbot" | while read resultsdir; do
        downloadurl="${WEBKIT_RESULTS_URL}/${webkitbot}/${resultsdir}full_results.json"
        tries=1
        while true; do
            if grep -qx "${resultsdir}" "${alreadytried}"; then
                echo -n "."
                break
            fi
            if test -f "${tempjsonresultfile}" && grep -qP "^ADD_RESULTS\(.*\);$" "${tempjsonresultfile}" ; then
                # Get the revision number from the json data and move the file to its place.
                # Is important that the file in disk is stored as "r${revision}_b${buildnumber}" because the
                # python wktesthunter code assumes that the revision on the filename is right.
                buildnum="$(echo ${resultsdir}| awk -F'%28' '{print $2}'|awk -F'%29' '{print $1}')"
                if json_result_test_has_revision_key "${tempjsonresultfile}"; then
                    revision="$(print_revision_from_json_results ${tempjsonresultfile})"
                else
                    # If the test run deadlocks then it may lack the revision in the json data.
                    # Workaround the problem by guessing the revision number from the URL
                    # But also ensure that the test is marked as interrupted in that case
                    # See example:
                    # Original URL http://build.webkit.org/results/WPE-Linux-64-bit-Debug-Tests/257598%40main%20%284216%29/full_results.json
                    # Saved as: jsonresults/WPE-Linux-64-bit-Debug-Tests/full_results_257598@main_b4216.json
                    # Logs: https://build.webkit.org/#/builders/14/builds/4216
                    if json_result_test_run_was_interrupted "${tempjsonresultfile}"; then
                        revision="$(urldecode $(echo ${resultsdir} | awk -F'%20' '{print $1}'))"
                        echo -e "\nWARNING: Revision ${revision} guessed from the URL because it is not in the json data from ${downloadurl}"
                    else
                        echo -e "\FATAL: ${downloadurl} has no revision data and test run was not interrupted. This is unexpected."
                        exit 1
                    fi
                fi
                # Sanity checks
                echo "${buildnum}" | grep -Pq "^[0-9]+$" || fatal "Buildnum should be numeric and I got buildnum \"${buildnum}\" for ${downloadurl}"
                echo "${revision}" | grep -Pq "^[0-9]+@main$" || fatal "Revision should be in the format: number@main and I got revision \"${revision}\" for ${downloadurl}"
                echo -n "${revision}... "
                mv "${tempjsonresultfile}" "full_results_${revision}_b${buildnum}.json"
                # store the resultsdir on the cache to not retry this download
                echo -n ":"
                echo "${resultsdir}" >> "${alreadytried}"
                break
            fi
            if [[ ${tries} -gt 3 ]]; then
                httpcode="$(curl -L -w "%{http_code}" -s "${downloadurl}" -o /dev/null)"
                if [[ "${httpcode}" == "404" ]]; then
                    echo "${resultsdir}" >> "${alreadytried}"
                fi
                echo -e "\nERROR: After ${tries} tries I was unable to fetch resource: ${downloadurl}. HTTP Error code was: ${httpcode}"
                break
            fi
            #echo "Downloading results for revision $revision buildnum $buildnum ..."
            [[ ${tries} -eq 1 ]] && echo
            rm -f "${tempjsonresultfile}"
            curl -L -s "${downloadurl}" -o "${tempjsonresultfile}"
            tries=$(( ${tries} + 1 ))
        done
    done
    cd ..
done
