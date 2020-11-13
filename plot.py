#!/usr/bin/env python3
# coding: utf-8

import pandas as pd
import matplotlib.pyplot as plt
import argparse

SMALL_SIZE=12
MEDIUM_SIZE=16
BIGGER_SIZE=8

plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default='GTK')
    parser.add_argument('-c', '--config', default='Release', choices=['Release', 'Debug'])

    return parser.parse_args()

def port_str(port, config):
    return '%s-%s' % (port, config)

def read_df(port='gtk', config='release'):
    
    filename = port_str(port, config).lower()
    df = pd.read_csv("%s.csv" % filename, parse_dates=['date'])
    df = df[df['date'] > '2019-01-01']
    df.set_index('date', inplace=True)
    return df

def main():
    args = parse_args()

    df = read_df(args.port, args.config)
    plot_expected(df, args.port, args.config)
    plot_unexpected(df, args.port, args.config)

def plot_unexpected(df, port, config):
    fig, ax = plt.subplots(facecolor='white', figsize=(5, 5), dpi=160)
    df[['num_regressions', 'num_flaky']].rolling(50).mean().plot(ax=ax)
    plt.title("%s - Regressions and flakies" % port_str(port, config))
    plt.xlabel('Date')
    plt.ylabel('Number of tests')
    # FIXME Parametrize these ticks
    ax.set_xticks(['2019-01', '2019-07', '2020-01', '2020-07'])
    ax.legend(['Regressions', 'Flakies'], loc='center right', bbox_to_anchor=(1.5, 0.5))
    ax.grid(True, linestyle='-.')
    fig = ax.get_figure()
    fig.savefig('%s-regr-flaky.png' % port_str(port, config), transparent=True, bbox_inches="tight")

def plot_expected(df, port, config):
    fig, ax = plt.subplots(facecolor='white', figsize=(5, 5), dpi=160)
    df[['fixable', 'skipped', 'num_passes']].rolling(50).mean().plot(ax=ax)
    plt.title("%s - Passes, skips and known failures" % port_str(port, config))
    plt.xlabel('Date')
    plt.ylabel('Number of tests')
    ax.set_xticks(['2019-01-01', '2019-07-01', '2020-01-01', '2020-07-01'])
    ax.legend(['Fixable', 'Skipped', 'Passing'], loc='center right', bbox_to_anchor=(1.5, 0.5))
    ax.grid(True, linestyle='-.')
    fig = ax.get_figure()
    fig.savefig('%s-skip-fix-pass.png' % port_str(port, config), transparent=True, bbox_inches="tight")


if __name__ == "__main__":
    main()
