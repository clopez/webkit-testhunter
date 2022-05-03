#!/bin/bash
#  Carlos Alberto Lopez Perez <clopez@igalia.com>
set -eu

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
    webkitbot="$(urlencode "${webkitbot}")"
    curl -L -s "${webkitresultsurl}/${webkitbot}/" | grep "href=" | grep -Po 'r[0-9]+%20%28[0-9]+%29' | awk -F'%29' '{print $1}' | sort | uniq | while read buildurl; do
        revision="${buildurl%%\%*}"
        buildnum="${buildurl##*\%28}"
        filedownload="full_results_${revision}_b${buildnum}.json"
        downloadurl="${webkitresultsurl}/${webkitbot}/${buildurl}%29/full_results.json"
        tries=1
        while true; do
            if grep -qx "${revision}_b${buildnum}" "${alreadytried}"; then
                echo -n "."
                break
            fi
            if test -f "${filedownload}" && grep -qP "^ADD_RESULTS\(.*\);$" "${filedownload}" ; then
                # got it right
                echo -n ":"
                echo "${revision}_b${buildnum}" >> "${alreadytried}"
                break
            fi
            if [[ ${tries} -gt 3 ]]; then
                httpcode="$(curl -L -w "%{http_code}" -s "${downloadurl}" -o /dev/null)"
                if [[ "${httpcode}" == "404" ]]; then
                    echo "${revision}_b${buildnum}" >> "${alreadytried}"
                fi
                echo -e "\nERROR: After ${tries} tries I was unable to fetch resource: ${downloadurl}. HTTP Error code was: ${httpcode}"
                rm -f "${filedownload}"
                break
            fi
            #echo "Downloading results for revision $revision buildnum $buildnum ..."
            [[ ${tries} -eq 1 ]] && echo
            echo -n "${revision}... "
            rm -f "${filedownload}"
            curl -L -s "${downloadurl}" -o "${filedownload}"
            tries=$(( ${tries} + 1 ))
        done
    done
    cd ..
done
