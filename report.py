#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Copyright 2020 Igalia S.L.
#  Lauro Moura <lmoura@igalia.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""Consolidate json test run stats into a single csv file"""

import json
import argparse
import csv


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-o", "--output", type=str, default="out.csv", help="Output file"
    )
    parser.add_argument("filenames", type=str, nargs="+", help="Files to process")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print progress information"
    )
    parser.add_argument(
        "-f",
        "--full-parse",
        action="store_true",
        help="Parse the entire json file, without trying to skip the tests",
    )

    return parser.parse_args()


def parse_files(files, verbose, full_parse):
    """Generator to parse each file individually

    If full_parse is false, it'll try to skip the huge "tests" field, jumping
    straight to the test run totals.
    """
    for filename in files:
        if verbose:
            print("Reading", filename)
        with open(filename) as handle:
            # The json files are wrapped in "ADD_RESULTS[<json payload>]"
            raw_data = handle.read()[len("ADD_RESULTS[") : -len("];")]
            if not full_parse:
                idx = raw_data.find('"skipped":')
                raw_data = "{" + raw_data[idx:]
            data = json.loads(raw_data)
            if "tests" in data:
                del data["tests"]
            yield data


def main():
    """Main script function"""
    args = parse_args()

    with open(args.output, "w", newline="") as csvfile:
        files = parse_files(args.filenames, args.verbose, args.full_parse)

        try:
            first = next(files)
        except StopIteration:
            if args.verbose:
                print("No entries found.")
            return

        fieldnames = list(first.keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerow(first)

        for entry in files:
            if args.verbose:
                print("Saving revision", entry["revision"])
            writer.writerow(entry)


if __name__ == "__main__":
    main()
