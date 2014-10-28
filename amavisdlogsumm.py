#!/usr/bin/env python3

import argparse
import codecs
import operator
import re
import sys
from datetime import datetime, timedelta

timestamp_format = '%b %d %H:%M:%S'

line_pattern = re.compile(r"""
        (?P<timestamp>\w+\s+\d+\s+\d+:\d+:\d+)\s+   # timestamp: Oct  8 07:02:22
        (?P<hostname>\w+)\s+                        # hostname: mx1
        (?P<service>\w+[/-]?)+                      # service: amavis
        (?P<service_id>.\d+.):\s+                   # service_id [12345]
        (?P<details>.*)                             # log details: everything else
        """, re.X)

error_pattern = re.compile(r"""
        (?P<amavisq>.(\d+[-]?)+.)\s+                # amavis queue
        [(][!][)]                                   # (!)
        """, re.X)
continue_pattern = re.compile(r"""
        (?P<amavisq>.(\d+[-]?)+.)\s+                # amavis queue
        [.]{3}                                      # ...
        """, re.X)
log_pattern = re.compile(r"""
        (?P<amavisq>.(\d+[-]?)+.)\s+                # amavis queue
        (?P<action>\w+\s*[\w-]+[:]?)\s+             # Passed, Blocked, INFO:
        .*
        """, re.X)
action_pattern = re.compile(r'^(Passed|Blocked)')
info_pattern = re.compile(r'^INFO:')

action_summary = {}
action_summary_by_hour = {}
info_summary = []
error_summary = []
startup_logs = []

def main():
    parser = argparse.ArgumentParser(description='%(prog)s - Produce AMaViSd-new logfile summary')
    parser.add_argument('-d', '--day', choices=['today', 'yesterday'])
    parser.add_argument('--startup-detail', action='store_true')
    parser.add_argument('logfiles', nargs='+')
    args = parser.parse_args()

    # parse all logs, today or yesterday
    log_day = None
    if args.day == 'today':
        log_day = datetime.today()
    elif args.day == 'yesterday':
        log_day = datetime.today() - timedelta(1)

    process(log_day, args)
    print_summary(log_day, args)

def process(log_day, args):
    for logfile in args.logfiles:
        for line in codecs.open(logfile, 'r', encoding='Windows-1252'):
            #print(line.strip())
            match = line_pattern.match(line)
            parts = match.groupdict()
            if parts['service'] != 'amavis':
                continue
            log_date = datetime.strptime(parts['timestamp'], timestamp_format)
            if log_day:
                if not (log_day.month == log_date.month and log_day.day == log_date.day):
                    continue
            if continue_pattern.match(parts['details']):
                continue
            if error_pattern.match(parts['details']):
                error_summary.append(parts['details'])
                continue
            details_match = log_pattern.match(parts['details'])
            if not details_match:
                # Anything not matched should be startup logs.
                startup_logs.append(parts['details'])
                continue
            details = details_match.groupdict()
            action = details['action']
            if action_pattern.match(action):
                # grand totals
                action_summary[action] = action_summary.get(action, 0) + 1
                # per hour totals
                day = '%s %s' % (log_date.month, log_date.day)
                day_summary = action_summary_by_hour.get(day, {})
                hour_summary = day_summary.get(log_date.hour, {})
                hour_summary[action] = hour_summary.get(action, 0) + 1
                day_summary[log_date.hour] = hour_summary
                action_summary_by_hour[day] = day_summary
            elif info_pattern.match(action):
                info_summary.append(parts['details'])

def print_summary(log_day, args):
    # Print report
    if log_day:
        print('amavis log summaries for %s' % log_day.strftime('%b %d'))
    else:
        print('amavis log summaries')

    print('')
    print('Grand Totals')
    print('------------')
    print('')

    # Find the total processed.
    total_processed = 0
    for value in action_summary.values():
        total_processed += value

    # Find the length of the longest value.
    values = [str(value) for value in action_summary.values()]
    padding = len(max(values, key=len))
    # The * in the %*s lets us add padding.
    print('%*d   total processed' % (padding, total_processed))
    for key, value in sorted(action_summary.items()):
        if key.startswith('Blocked'):
            # Show percentage of total processed.
            percent_blocked = float(value)/total_processed * 100
            print('%*d   %s (%.1f%%)' % (padding, value, key, percent_blocked))
        else:
            print('%*d   %s' % (padding, value, key))

    print('')
    print('Per-Hour Summary')
    print('----------------')
    print('%-9s %9s %9s' % ('time', 'blocked', 'passed'))
    for k, v in action_summary_by_hour.items():
        for hour, data in v.items():
            print('%02d00-%02d00 %9d %9d' % (hour, hour+1, data['Blocked SPAM'], data['Passed CLEAN']))
    #print(action_summary_by_hour)
    print('')

    print('')
    if info_summary:
        print('INFO messages')
        print('-------------')
        for m in info_summary:
            print(m)
    else:
        print('INFO messages: none')

    print('')
    if error_summary:
        print('(!) messages')
        print('------------')
        for m in error_summary:
            print(m)
    else:
        print('(!) messages: none')

    print('')
    if args.startup_detail:
        print('startup details')
        print('---------------')
        for log in startup_logs:
            print(log)
    else:
        print('startup details: none')

if __name__ == '__main__':
    main()

# Notes:
# ------
# amavisd-new starts where awk $6 starts with 'starting.'
# Find last instance of 'Module Amavis::Conf' and use awk $5 to get startup info.
# Blocked X or Passed Y is spam or not spam with various possibilities for X and Y.
# Ignore lines where awk $7 starts with '...'
# Errors: lines where awk $7 starts with '(!)'
# Info: lines where awk $7 starts with 'INFO'

# Example:
# Oct  8 07:02:21 mx1 amavis[13087]: starting. /usr/sbin/amavisd-new at mx1.domain amavisd-new-2.7.1 (20120429), Unicode aware, LANG="en_US.UTF-8"
# Oct  8 07:02:22 mx1 amavis[13096]: Net::Server: Group Not Defined.  Defaulting to EGID '117 117'
# Oct  8 07:02:22 mx1 amavis[13096]: Net::Server: User Not Defined.  Defaulting to EUID '108'
# Oct  8 07:02:22 mx1 amavis[13096]: Module Amavis::Conf        2.303
# Oct  8 07:02:22 mx1 amavis[13096]: Module Archive::Zip        1.30
# [...]
# Oct  8 07:02:22 mx1 amavis[13096]: Deleting db files __db.002,__db.003,__db.001,nanny.db,snmp.db in /var/lib/amavis/db
# Oct  8 07:02:22 mx1 amavis[13096]: Creating db in /var/lib/amavis/db/; BerkeleyDB 0.54, libdb 5.3
# Oct  8 07:02:27 mx1 amavis[13102]: (13102-01) Passed CLEAN {RelayedOpenRelay}, [209.18.93.165]:27081 [209.18.93.165] <username@good-sample.com> -> <username@example.com>, Queue-ID: 0C715DC1E04, Message-ID: <0.0.1.3B3.1CFE3007B590009.2E58B@mail.server>, mail_id: ZWh2rFEvUS0W, Hits: -1.888, size: 22465, queued_as: 66450DC2DEC, dkim_sd=rmagnet:good-sample.com, 2471 ms
# Oct  8 07:02:54 mx1 amavis[13102]: (13102-02-5) Blocked SPAM {DiscardedOpenRelay,Quarantined}, [198.52.240.237]:51464 [198.52.240.237] <username@bad-sample.com> -> <username@example.com>, quarantine: X/spam-XEPcvjbxeoHT.gz, Queue-ID: 3DAAEDC2DEC, Message-ID: <3624575649972759977.640589511.JavaMail.java@mode.bad-sample.com>, mail_id: XEPcvjbxeoHT, Hits: 7.433, size: 8116, 6146 ms
# Oct  7 06:21:36 mx1 amavis[7156]: (07156-04) (!)do_unzip: p003, unsupported compr. method: 9
# Oct  8 08:23:48 mx1 amavis[18584]: (18584-10) INFO: unfolded 1 illegal all-whitespace continuation lines

