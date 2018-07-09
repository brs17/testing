#!/usr/bin/python3

import re
import time
import statistics
import json
import multiprocessing
from subprocess import check_output, Popen, PIPE
from os import path, makedirs
from psutil import cpu_percent

WARMUP_INTERVAL = 1
SAMPLE_INTERVAL = 1
STRESS_TIME = 3
SAMPLE_COUNT = STRESS_TIME
TESTDIR = 'testresults/'


def clear_screen():
    print('\x1b[H\x1b[2J', end='')


def read_cputemp():
    return check_output(['sensors']).decode()


def read_cpuclock():
    return check_output(['grep', '-i', 'MHz', '/proc/cpuinfo']).decode()


def read_cpuutil(): #returns: [0.0, 10.0, 9.1, 0.0, 9.1, 9.1, 0.0, 0.0]
    return cpu_percent(interval=0.1, percpu=True)


def read_memusage():
    memusage = Popen(['free', '-k'], stdout=PIPE)
    return check_output(['grep', 'Mem'], 
            stdin=memusage.stdout).decode()


def read_gputemps():
    nvidia = Popen(['nvidia-smi', '-q'], stdout=PIPE)
    return check_output(['grep', 'GPU Current Temp'], 
            stdin=nvidia.stdout).decode()


def read_gpupower():
    nvidia = Popen(['nvidia-smi', '-q'], stdout=PIPE)
    return check_output(['grep', 'Power Draw'], stdin=nvidia.stdout).decode()


def read_gpuutil():
    nvidia = Popen(['nvidia-smi', '-q'], stdout=PIPE)
    return check_output(['grep', 'Gpu'], stdin=nvidia.stdout).decode()


def read_gpufan():
    nvidia = Popen(['nvidia-smi', '-q'], stdout=PIPE)
    return check_output(['grep', 'Fan'], stdin=nvidia.stdout).decode()

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


def iter_cpuclock(text):
    for line in text.splitlines():
        if ':' in line:
            (label, tail) = line.split(':')
            if tail:
                print("printing label: ", label)
                print("printing tail: ", tail)
            else:
                print("dumb")
            yield (label, tail)

def iter_cpuutil(text):
    corenum = 0
    for i in text:
        label = "Core: " + str(corenum)
        tail = i
        corenuma += 1
        yield (label, tail)


def iter_memusage(text):
    for line in text.splitlines():
        if ':' in line and line.startswith('Mem:'):
            (label, tail) = line.split(':')
            m = re.split('\s+',tail)
            if m: #check if regex match exists
                temp = float(m[3])
            else:   #make sure something happens
                temp = float(0)
            yield (label, temp)


def iter_gputemps(text):
    for line in text.splitlines():
        if ':' in line:
            (label, tail) = line.split(':')
            if tail:
                temp = float(m.group(1))
            else:
                temp = float(0)
            yield (label, temp)


def iter_gpupower(text):
    for line in text.splitlines():
        if ':' in line:
            (label, tail) = line.split(':')
            if tail:
                temp = float(m.group(1))
            else:
                temp = float(0)
            yield (label, temp)


def iter_gpuutil(text):
    for line in text.splitlines():
        if ':' in line:
            (label, tail) = line.split(':')
            if tail:
                temp = float(m.group(1))
            else:
                temp = float(0)
            yield (label, temp)


def iter_gpufan(text):
    for line in text.splitlines():
        if ':' in line:
            (label, tail) = line.split(':')
            if tail:
                temp = float(m.group(1))
            else:
                temp = float(0)
            yield (label, temp)


def parse_temps(text):
    return dict(iter_temps(text))


def parse_cpuclock(text):
    return dict(iter_cpuclock(text))


def parse_cpuutil(text):
    return dict(iter_cpuutil(text))


def parse_memusage(text):
    return dict(iter_memusage(text))


def parse_gputemps(text):
    return dict(iter_gputemps(text))


def parse_gpupower(text):
    return dict(iter_gpupower(text))


def parse_gpuutil(text):
    return dict(iter_gpuutil(text))


def parse_gpufan(text):
    return dict(iter_gpufan(text))


def get_temps():
    return parse_temps(read_cputemp())


def get_cpuclock():
    return parse_cpuclock(read_cpuclock())


def get_cpuutil():
    return parse_cpuutil(read_cpuutil())


def get_memusage():
    return parse_memusage(read_memusage())


def get_gputemps():
    return parse_gputemps(read_gputemps())


def get_gpupower():
    return parse_gpupower(read_gpupower())


def get_gpuutil():
    return parse_gpuutil(read_gpuutil())


def get_gpufan():
    return parse_gpufan(read_gpufan())

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


def analyze_cpuclock(raw):
    combined = []
    summary = {}
    for (k, v) in raw.items():
        print("printing v: ", v)
        combined.append(statistics.mean(v))
        summary[k] = summarize_temp(v)
    summary['_combined'] = summarize_temp(combined)
    return summary


def record_temps(count=SAMPLE_COUNT, interval=SAMPLE_INTERVAL):
    raw = dict((k, []) for k in get_temps())
    for i in range(count):
        time.sleep(interval)
        text = read_cputemp()
        clear_screen()
        print(text)
        print('[sample {} of {}]'.format(i + 1, count))
        for (k, v) in parse_temps(text).items():
            raw[k].append(v)
    return raw

def record_cpuclock(count=SAMPLE_COUNT, interval=SAMPLE_INTERVAL):
    raw = dict((k, []) for k in get_cpuclock())
    for i in range(count):
        time.sleep(interval)
        text = read_cpuclock()
        clear_screen()
        print(text)
        print('[sample {} of {}]'.format(i + 1, count))
        for (k, v) in parse_cpuclock(text).items():
            raw[k].append(v)
    return raw


def record_cpuutil(count=SAMPLE_COUNT, interval=SAMPLE_INTERVAL):
    raw = dict((k, []) for k in get_cpuutil())
    for i in range(count):
        time.sleep(interval)
        text = read_cpuutil()
        clear_screen()
        print(text)
        print('[sample {} of {}]'.format(i + 1, count))
        for (k, v) in parse_cpuutil(text).items():
            raw[k].append(v)
    return raw


def record_memusage(count=SAMPLE_COUNT, interval=SAMPLE_INTERVAL):
    raw = dict((k, []) for k in get_memusage())
    for i in range(count):
        time.sleep(interval)
        text = read_memusage()
        clear_screen()
        print(text)
        print('[sample {} of {}]'.format(i + 1, count))
        for (k, v) in parse_memusage(text).items():
            raw[k].append(v)
    return raw

def record_gputemps(count=SAMPLE_COUNT, interval=SAMPLE_INTERVAL):
    raw = dict((k, []) for k in get_gputemps())
    for i in range(count):
        time.sleep(interval)
        text = read_gputemps()
        clear_screen()
        print(text)
        print('[sample {} of {}]'.format(i + 1, count))
        for (k, v) in parse_gputemps(text).items():
            raw[k].append(v)
    return raw


def record_gpupower(count=SAMPLE_COUNT, interval=SAMPLE_INTERVAL):
    raw = dict((k, []) for k in get_gpupower())
    for i in range(count):
        time.sleep(interval)
        text = read_gpupower()
        clear_screen()
        print(text)
        print('[sample {} of {}]'.format(i + 1, count))
        for (k, v) in parse_gpupower(text).items():
            raw[k].append(v)
    return raw


def record_gpuutil(count=SAMPLE_COUNT, interval=SAMPLE_INTERVAL):
    raw = dict((k, []) for k in get_gpuutil())
    for i in range(count):
        time.sleep(interval)
        text = read_gpuutil()
        clear_screen()
        print(text)
        print('[sample {} of {}]'.format(i + 1, count))
        for (k, v) in parse_gpuutil(text).items():
            raw[k].append(v)
    return raw


def record_gpufan(count=SAMPLE_COUNT, interval=SAMPLE_INTERVAL):
    raw = dict((k, []) for k in get_gpufan())
    for i in range(count):
        time.sleep(interval)
        text = read_gpufan()
        clear_screen()
        print(text)
        print('[sample {} of {}]'.format(i + 1, count))
        for (k, v) in parse_gpufan(text).items():
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
    raw = record_cpuclock()
    dump_raw(custname, raw)
    summary = analyze_temps(raw)
    dump_summary(custname, summary)
    print_summary(summary)


custname = input("What would you like to call this test?\n")

p = start_cpustress()
q = start_gpustress()
wait_for_warmup()
run()
