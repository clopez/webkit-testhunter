#!/usr/bin/env python3

import json
import argparse
import csv

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-o', '--output', type=str, default='out.csv', help="Output file")
    parser.add_argument("filenames", type=str, nargs="+", help="Files to process")

    return parser.parse_args()

def main():
    args = parse_args()

    files = []

    for filename in args.filenames:
        print("Reading", filename)
        with open(filename) as handle:
            raw_data = handle.read()[len("ADD_RESULTS["):-len("];")]
            data = json.loads(raw_data)
            del(data['tests'])
            files.append(data)

    with open(args.output, 'w', newline='') as csvfile:
        fieldnames = list(files[0].keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for entry in files:
            print("Saving revision", entry['revision'])
            writer.writerow(entry)

if __name__ == "__main__":
    main()