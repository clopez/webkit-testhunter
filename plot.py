#!/usr/bin/env python3
# coding: utf-8
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

"""Plot Layout tests results over time"""

import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt

SMALL_SIZE = 12
MEDIUM_SIZE = 16
BIGGER_SIZE = 8

plt.rc("font", size=SMALL_SIZE)  # controls default text sizes
plt.rc("axes", titlesize=SMALL_SIZE)  # fontsize of the axes title
plt.rc("axes", labelsize=MEDIUM_SIZE)  # fontsize of the x and y labels
plt.rc("xtick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
plt.rc("ytick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
plt.rc("legend", fontsize=SMALL_SIZE)  # legend fontsize
plt.rc("figure", titlesize=BIGGER_SIZE)  # fontsize of the figure title


def parse_args():
    """Parse command line args"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--port",
        default="Unknown",
        choices=("GTK", "WPE"),
        help="Name of the port being processed",
    )
    parser.add_argument(
        "-c",
        "--config",
        default="Unknown",
        choices=("Release", "Debug"),
        help="Configuration of the port being processed",
    )
    parser.add_argument(
        "-d",
        "--directory",
        default=os.getcwd(),
        help="Output directory. Defaults to the current one",
    )

    parser.add_argument("filename", help="File to be processed.")

    args = parser.parse_args()
    filename = args.filename.lower()

    if args.port == "Unknown" and args.config == "Unknown":
        try:
            basename, _ = os.path.splitext(filename)
            port, config = basename.split("-")
            args.port = port.upper()
            args.config = config.capitalize()
            print(
                "Guessed port '%s' and configuration '%s' from filename"
                % (args.port, args.config)
            )
        except ValueError:  # No '-' in the name, for example
            print("Could not guess port and config")

    return args


def port_str(port, config):
    """Standard identifier for a port/config pair"""
    return "%s-%s" % (port, config)


def read_df(filename):
    """Read the initial data for the given port and config"""
    df = pd.read_csv(filename, parse_dates=["date"])
    df = df[df["date"] > "2019-01-01"]
    df.set_index("date", inplace=True)
    return df


def main():
    """Main script routine"""

    args = parse_args()

    df = read_df(args.filename)
    plot_expected(df, args.port, args.config)
    plot_unexpected(df, args.port, args.config)


def plot_unexpected(df, port, config):
    """Plot the unexpected results

    The unexpected results are grouped in regressions (failures, timeouts,
    crashes) not yet gardened, and in Flakies (tests that fails on the first run
    and passes on a retry).
    """
    # This fig size generates an image with height of 767 pixels
    # The width varies due to the ax.lengends call below to move the
    # legend bots to outside the chart
    fig, ax = plt.subplots(facecolor="white", figsize=(5, 5), dpi=160)
    df[["num_regressions", "num_flaky"]].rolling(50).mean().plot(ax=ax)
    plt.title("%s - Regressions and flakies" % port_str(port, config))
    plt.xlabel("Date")
    plt.ylabel("Number of tests")
    # FIXME Parametrize these ticks
    ax.set_xticks(["2019-01", "2019-07", "2020-01", "2020-07"])
    ax.legend(["Regressions", "Flakies"], loc="center right", bbox_to_anchor=(1.5, 0.5))
    ax.grid(True, linestyle="-.")
    fig = ax.get_figure()
    fig.savefig(
        "%s-regr-flaky.png" % port_str(port, config),
        transparent=True,
        bbox_inches="tight",
    )


def plot_expected(df, port, config):
    """Plot the expected results

    The expected results are grouped in passes, skips and known failures. The last
    are crashes, flakies, timeouts and failures already gardened.
    """
    fig, ax = plt.subplots(facecolor="white", figsize=(5, 5), dpi=160)
    df[["fixable", "skipped", "num_passes"]].rolling(50).mean().plot(ax=ax)
    plt.title("%s - Passes, skips and known failures" % port_str(port, config))
    plt.xlabel("Date")
    plt.ylabel("Number of tests")
    # FIXME Parametrize these ticks
    ax.set_xticks(["2019-01-01", "2019-07-01", "2020-01-01", "2020-07-01"])
    ax.legend(
        ["Fixable", "Skipped", "Passing"], loc="center right", bbox_to_anchor=(1.5, 0.5)
    )
    ax.grid(True, linestyle="-.")
    fig = ax.get_figure()
    fig.savefig(
        "%s-skip-fix-pass.png" % port_str(port, config),
        transparent=True,
        bbox_inches="tight",
    )


if __name__ == "__main__":
    main()
