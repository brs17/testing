#!/usr/bin/python3

import re
import time
import statistics
import json
import multiprocessing
from subprocess import check_output, Popen
from os import path, makedirs

WARMUP_INTERVAL = 1
SAMPLE_INTERVAL = 1
STRESS_TIME = 3
SAMPLE_COUNT = STRESS_TIME
TESTDIR = '../testresults/'


def clear_screen():
    print('\x1b[H\x1b[2J', end='')


#NOTE:perhaps something like this if setup.sh didn't exist
#def read_sensors():
#    try:
#        output = check_output(['sensors']).decode()
#    except FileNotFoundError:
#        print("sensors is not installed, installing...")
#        check_output(["sudo", "apt-get", "install", "lm-sensors"])
#        output = check_output(['sensors']).decode()
#    return output
def read_sensors():
    return check_output(['sensors']).decode()


def iter_temps(text):
    for line in text.splitlines():
        if ':' in line and not line.startswith('Adapter:'):
            (label, tail) = line.split(':')
            if label in ('temp1', 'temp2'):
                continue
            m = re.match('\s*\+(\d+)', tail)
            if m: #check if regex match exists
                temp = float(m.group(1))
            else:   #make sure something happens
                temp = float(0)
            yield (label, temp)


def parse_temps(text):
    return dict(iter_temps(text))


def get_temps():
    return parse_temps(read_sensors())


def summarize_temp(items):
    return {
        'max': max(items),
        'mean': statistics.mean(items),
        'median': statistics.median(items),
        'min': min(items),
        'stdev': statistics.stdev(items),
    }


def analyze_temps(raw):
    combined = []
    summary = {}
    for (k, v) in raw.items():
        combined.append(statistics.mean(v))
        summary[k] = summarize_temp(v)
    summary['_combined'] = summarize_temp(combined)
    return summary


def record_temps(count=SAMPLE_COUNT, interval=SAMPLE_INTERVAL):
    raw = dict((k, []) for k in get_temps())
    for i in range(count):
        time.sleep(interval)
        text = read_sensors()
        clear_screen()
        print(text)
        print('[sample {} of {}]'.format(i + 1, count))
        for (k, v) in parse_temps(text).items():
            raw[k].append(v)
    return raw


def dump_raw(custname, raw):
    if not path.exists(TESTDIR):
        makedirs(TESTDIR)
    filename = TESTDIR + 'temps-{}-raw.json'.format(custname)
    with open(filename, 'x') as fp:
        json.dump(raw, fp, indent=4, sort_keys=True)

def dump_summary(custname, summary):
    if not path.exists(TESTDIR):
        makedirs(TESTDIR)
    filename = TESTDIR + 'temps-{}-summary.json'.format(custname)
    with open(filename, 'x') as fp:
        json.dump(summary, fp, indent=4, sort_keys=True)


def print_summary(summary):
    clear_screen()
    for key in sorted(summary):
        print('{}:'.format(key))
        for (k, v) in sorted(summary[key].items()):
            print('    {}: {:.1f}'.format(k, v))


def start_cpustress():
    print("cputesting")
    return 0


def start_gpustress():
    print("gputesting")
    return 0


def wait_for_warmup():
    print('Waiting {} seconds for warmup...'.format(WARMUP_INTERVAL))
    time.sleep(WARMUP_INTERVAL)


def run():
    start_ts = int(time.time())
    print('Start at {}'.format(start_ts))
    raw = record_temps()
    dump_raw(custname, raw)
    summary = analyze_temps(raw)
    dump_summary(custname, summary)
    print_summary(summary)

custname = input("What would you like to call this test?\n")
curdate = time.localtime()
custname = custname + '-' + str(curdate[0]) + '-' + str(curdate[1]) + '-' + str(curdate[2])

p = start_cpustress()
q = start_gpustress()
wait_for_warmup()
run()

