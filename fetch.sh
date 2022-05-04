#!/bin/bash
#  Carlos Alberto Lopez Perez <clopez@igalia.com>
set -eu

fatal() {
    echo "Fatal: $@"
    exit 1
}

usage () {
   local exit_code="$1"

   echo "fetch.sh [BOT] ..."
   echo "Retrieves tests data from a set of bots. In case no bot is set, data is retrieved from all bots."
   echo ""
   echo "ARGUMENTS:"
   echo -e "\tBOT\tgtk-release, gtk-debug, wpe-release, wpe-debug, gtk-release-old, gtk-release-wk2, gtk-release-wayland"

   exit $exit_code
}

urlencode () {
    python -c "import urllib; print urllib.quote(\"${@}\")"
}

print_revision_from_json_results () {
    python -c "import json, os; json_data=open(\"${1}\").read().split('ADD_RESULTS(')[1].split(');')[0]; print(json.loads(json_data)['revision'])"
}


webkitresultsurl="http://build.webkit.org/results"

# The GTK test bot is now "GTK Linux 64-bit Release (Tests)".
# The others were the names of this test bot in the past.
# We fetch all the data from the actual test bot as also the past ones, to have a complete history
declare -A webkitbots_map
webkitbots_map=(
   ["gtk-release-old"]="GTK-Linux-64-bit-Release"
   ["gtk-release-wk2"]="GTK-Linux-64-bit-Release-WK2-Tests"
   ["gtk-release"]="GTK-Linux-64-bit-Release-Tests"
   ["gtk-debug"]="GTK-Linux-64-bit-Debug-Tests"
   ["gtk-release-wayland"]="GTK-Linux-64-bit-Release-Wayland-Tests"
   ["gtk-release-gtk4"]="GTK-Linux-64-bit-Release-GTK4-Tests"
   ["gtk-release-skip-failing"]="GTK-Linux-64-bit-Release-Skip-Failing-Tests"
   ["wpe-release"]="WPE-Linux-64-bit-Release-Tests"
   ["wpe-debug"]="WPE-Linux-64-bit-Debug-Tests"
)
webkitbots_keys=()
for each in "${!webkitbots_map[@]}"; do
   webkitbots_keys+=( "$each" )
done
webkitbots_values=()
for each in "${webkitbots_map[@]}"; do
   webkitbots_values+=( "$each" )
done

if [[ $# -gt 0 ]]; then
   # Check any of the arguments is help.
   for arg in "$@"; do
      if [[ "$arg" == "-h" || "$arg" == "--help" ]]; then
         usage 0
      fi
   done

   # Parse arguments.
   webkitbots_values=()
   for arg in "$@"; do
      if [[ ! " ${webkitbots_keys[@]} " =~ " $arg " ]]; then
         echo "Error: Invalid argument: '$arg'"
         exit 1
      fi
      webkitbots_values+=( "${webkitbots_map[$arg]}" )
   done
fi

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
    curl -L -s "${webkitresultsurl}/${webkitbot}/" | grep -P "href=\"[^\"]+/"| cut -d\" -f2 | grep -v  "\.\./" | sort | uniq | while read resultsdir; do
        downloadurl="${webkitresultsurl}/${webkitbot}/${resultsdir}full_results.json"
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
                revision="$(print_revision_from_json_results ${tempjsonresultfile})"
                echo -n "r${revision}... "
                # Sanity checks
                echo "${buildnum}" | grep -Pq "^[0-9]+$" || fatal "Buildnum should be numeric and I got buildnum \"${buildnum}\" for ${downloadurl}"
                echo "${revision}" | grep -Pq "^[0-9]+$" || fatal "Revision should be numeric and I got revision \"${revision}\" for ${downloadurl}"
                mv "${tempjsonresultfile}" "full_results_r${revision}_b${buildnum}.json"
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
