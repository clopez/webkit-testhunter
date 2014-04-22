#!/bin/bash
#  Carlos Alberto Lopez Perez <clopez@igalia.com>
set -eu
webkitresultsurl="http://build.webkit.org/results"
webkitbot="GTK%20Linux%2064-bit%20Release"
prefix=$(echo ${webkitbot}|sed "s/%20/_/g")
cd jsonresults
curl -s "${webkitresultsurl}/${webkitbot}/" | grep "href=" | grep -Po 'r[0-9]+%20%28[0-9]+%29' | sort | uniq | while read buildurl; do
	revision=$(echo "${buildurl}"|awk -F'%20' '{print $1}')
	buildnum=$(echo "${buildurl}"|awk -F'%28' '{print $2}'|awk -F'%29' '{print $1}')
	filedownload="${prefix}_full_results_${revision}_b${buildnum}.json"
	downloadurl="${webkitresultsurl}/${webkitbot}/${buildurl}/full_results.json"
	tries=1
	while true; do
		if test -f "${filedownload}" && grep -qP "^ADD_RESULTS\(.*\);$" "${filedownload}" ; then
			# got it right
			echo -n "."
			break
		fi
		if [[ ${tries} -gt 3 ]]; then
			echo -e "\nERROR: After ${tries} tries I was unable to fetch resource: ${downloadurl}"
			rm -f "${filedownload}"
			break
		fi
		#echo "Downloading results for revision $revision buildnum $buildnum ..."
		[[ ${tries} -eq 1 ]] && echo
		echo -n "${revision}... "
		rm -f "${filedownload}"
		curl -s "${downloadurl}" -o "${filedownload}"
		tries=$(( ${tries} + 1 ))
	done
done
