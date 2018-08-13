#!/usr/bin/python3

import re
import time
import statistics
import json
import multiprocessing
from subprocess import check_output, Popen, PIPE
from os import path, makedirs
from psutil import cpu_percent

WARMUP_INTERVAL = 90
SAMPLE_INTERVAL = 1
STRESS_TIME = 600
GATHER_TIME = 60
SAMPLE_COUNT = STRESS_TIME
TESTDIR = 'testresults/' 


def clear_screen():
    print('\x1b[H\x1b[2J', end='')


def read_sensors():
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
            if label in ('temp1', 'temp2', 'Package id 0'):
                continue
            m = re.match('\s*\+(\d+)', tail)
            if m: #check if regex match exists
                temp = float(m.group(1))
            else:   #make sure something happens
                temp = float(0)
            yield (label, temp)


def iter_cpuclock(text):
    corenum =  0
    for line in text.splitlines():
        #print("line: ", line)
        if ':' in line:
            label = "Core " + str(corenum)
            tail = line.split(':')
            tail = tail[1].lstrip(' ')
            corenum += 1
            yield (label, tail)


def iter_cpuutil(text):
    corenum = 0
    for i in text:
        label = "Core: " + str(corenum)
        tail = i
        corenum += 1
        yield (label, tail)


def iter_memusage(text):
    for line in text.splitlines():
        if ':' in line and line.startswith('Mem:'):
            (label, tail) = line.split(':')
            m = re.split('\s+',tail)
            if m: #check if regex match exists
                temp = (float(m[2])/float(m[1]))*100
            else:   #make sure something happens
                temp = float(0)
            yield (label, temp)


def iter_gputemps(text):
    for line in text.splitlines():
        if ':' in line:
            (label, tail) = line.split(':')
            label = label.strip()
            tail = tail.split(' ')
            if tail:
                temp = float(tail[1])
            else:
                temp = float(0)
            yield (label, temp)


def iter_gpupower(text):
    for line in text.splitlines():
        if ':' in line:
            (label, tail) = line.split(':')
            label = label.strip()
            tail = tail.strip().split(' ')[0]
            if tail:
                temp = float(tail)
            else:
                temp = float(0)
            yield (label, temp)


def iter_gpuutil(text):
    for line in text.splitlines():
        if ':' in line:
            (label, tail) = line.split(':')
            label = label.strip()
            tail = tail.split(' ')
            if tail:
                temp = float(tail[1])
            else:
                temp = float(0)
            yield (label, temp)


def iter_gpufan(text):
    for line in text.splitlines():
        if ':' in line:
            (label, tail) = line.split(':')
            label = label.strip()
            if tail:
                temp = float(tail[:-1])
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
    return parse_temps(read_sensors())


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
    maxav = []
    meanav = []
    medianav = []
    minav = []
    for core in items:
        maxav.append(max(core))
        meanav.append(statistics.mean(core))
        medianav.append(statistics.median(core))
        minav.append(min(core))
    try:
        stdev = statistics.stdev(items)
    except statistics.StatisticsError:
        stdev = 0 
    except TypeError:
        stdev=0
    return {
        'max': max(maxav),
        'mean': statistics.mean(meanav),
        'median': statistics.median(medianav),
        'min': min(minav),
        'stdev': stdev,
    }


def analyze_temps(raw, j):
    combined = []
    summary = {}
    #print("analyze items: ", raw)
    for (k, v) in raw.items():
        appendage = v
        if "CPU" in k:
            appendage = statistics.mean(v)
        combined.append(appendage)
        #summary[k] = summarize_temp(v)
    summary[j] = summarize_temp(combined)
    return summary


def record_temps(q, count, interval=SAMPLE_INTERVAL):
    print(multiprocessing.current_process().name, " starting")
    raw = dict((k, []) for k in get_temps())
    for i in range(count):
        time.sleep(interval)
        text = read_sensors()
        clear_screen()
        #print(text)
        print('[sample {} of {}]'.format(i + 1, count))
        for (k, v) in parse_temps(text).items():
            raw[k].append(v)
    raw = dict(CPU_Temp=raw)
    q.put(raw)
    print(multiprocessing.current_process().name, " ending")

def record_cpuclock(q, count, interval=SAMPLE_INTERVAL):
    print(multiprocessing.current_process().name, " starting")
    raw = dict((k, []) for k in get_cpuclock())
    for i in range(count):
        time.sleep(interval)
        text = read_cpuclock()
        clear_screen()
        #print(text)
        print('[sample {} of {}]'.format(i + 1, count))
        for (k, v) in parse_cpuclock(text).items():
            raw[k].append(int(float(v)))
    raw = dict(CPU_Clockspeed=raw)
    q.put(raw)
    print(multiprocessing.current_process().name, " ending")


def record_cpuutil(q, count, interval=SAMPLE_INTERVAL):
    print(multiprocessing.current_process().name, " starting")
    raw = dict((k, []) for k in get_cpuutil())
    for i in range(count):
        time.sleep(interval)
        text = read_cpuutil()
        clear_screen()
        #print(text)
        print('[sample {} of {}]'.format(i + 1, count))
        for (k, v) in parse_cpuutil(text).items():
            raw[k].append(v)
    raw = dict(CPU_Utilization=raw)
    q.put(raw)
    print(multiprocessing.current_process().name, " ending")


def record_memusage(q, count, interval=SAMPLE_INTERVAL):
    print(multiprocessing.current_process().name, " starting")
    raw = dict((k, []) for k in get_memusage())
    for i in range(count):
        time.sleep(interval)
        text = read_memusage()
        clear_screen()
        #print(text)
        print('[sample {} of {}]'.format(i + 1, count))
        for (k, v) in parse_memusage(text).items():
            raw[k].append(v)
    raw = dict(Memory_Utilization=raw)
    q.put(raw)
    print(multiprocessing.current_process().name, " ending")

def record_gputemps(q, count, interval=SAMPLE_INTERVAL):
    print(multiprocessing.current_process().name, " starting")
    raw = dict((k, []) for k in get_gputemps())
    for i in range(count):
        time.sleep(interval)
        text = read_gputemps()
        clear_screen()
        print('[sample {} of {}]'.format(i + 1, count))
        for (k, v) in parse_gputemps(text).items():
            raw[k].append(v)
    raw = dict(GPU_Temps=raw)
    q.put(raw)
    print(multiprocessing.current_process().name, " ending")


def record_gpupower(q, count, interval=SAMPLE_INTERVAL):
    print(multiprocessing.current_process().name, " starting")
    raw = dict((k, []) for k in get_gpupower())
    for i in range(count):
        time.sleep(interval)
        text = read_gpupower()
        clear_screen()
        #print(text)
        print('[sample {} of {}]'.format(i + 1, count))
        for (k, v) in parse_gpupower(text).items():
            raw[k].append(v)
    raw = dict(GPU_Power=raw)
    q.put(raw)
    print(multiprocessing.current_process().name, " ending")


def record_gpuutil(q, count, interval=SAMPLE_INTERVAL):
    print(multiprocessing.current_process().name, " starting")
    raw = dict((k, []) for k in get_gpuutil())
    for i in range(count):
        time.sleep(interval)
        text = read_gpuutil()
        clear_screen()
        #print(text)
        print('[sample {} of {}]'.format(i + 1, count))
        for (k, v) in parse_gpuutil(text).items():
            raw[k].append(v)
    raw = dict(GPU_Utilization=raw)
    q.put(raw)
    print(multiprocessing.current_process().name, " ending")



def record_gpufan(q, count, interval=SAMPLE_INTERVAL):
    print(multiprocessing.current_process().name, " starting")
    raw = dict((k, []) for k in get_gpufan())
    for i in range(count):
        time.sleep(interval)
        text = read_gpufan()
        clear_screen()
        #print(text)
        print('[sample {} of {}]'.format(i + 1, count))
        for (k, v) in parse_gpufan(text).items():
            raw[k].append(v)
    raw = dict(GPU_Fan=raw)
    q.put(raw)
    print(multiprocessing.current_process().name, " ending")
    

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
    with open(filename, 'a') as fp:
        json.dump(summary, fp, indent=4, sort_keys=True)


def print_summary(summary):
    clear_screen()
    for key in sorted(summary):
        print('{}:'.format(key))
        for (k, v) in sorted(summary[key].items()):
            print('    {}: {:.1f}'.format(k, v))


def start_cpustress():
    cmd = ['stress-ng', '-c', str(multiprocessing.cpu_count()), '--vm', \
            str(2), '--vm-bytes', str('80%'), '-t', str(WARMUP_INTERVAL + STRESS_TIME)]
    print(cmd)
    return Popen(cmd)


def start_gpustress():
    cmd = ['./gpu_burn', str(WARMUP_INTERVAL + STRESS_TIME)]
    print(cmd)
    return Popen(cmd)


def wait_for_warmup():
    print('Waiting {} seconds for warmup...'.format(WARMUP_INTERVAL))
    time.sleep(WARMUP_INTERVAL)


def storeresults(raw, custnameraw):
    dump_raw(custnameraw, raw)


def storesummary(raw, custname, j):
    summary = analyze_temps(raw, j)
    dump_summary(custname, summary)
    print_summary(summary)


def run(count, initname):
    a = multiprocessing.Queue()
    b = multiprocessing.Queue()
    c = multiprocessing.Queue()
    d = multiprocessing.Queue()
    e = multiprocessing.Queue()
    f = multiprocessing.Queue()
    g = multiprocessing.Queue()
    h = multiprocessing.Queue()
    Q = [a,b,c,d,e,f,g,h]
    custnameraw = ''
    start_ts = int(time.time())
    print('Start at {}'.format(start_ts))
    ctemp = multiprocessing.Process(name='ctemp', target=record_temps, args=(a,count))
    cclock = multiprocessing.Process(name='clclock', target=record_cpuclock, args=(b,count))
    cutil = multiprocessing.Process(name='cutil',target=record_cpuutil, args=(c,count))
    musage = multiprocessing.Process(name='musage',target=record_memusage, args=(d,count))
    gtemps = multiprocessing.Process(name='gtemps',target=record_gputemps, args=(e,count))
    gpower = multiprocessing.Process(name='gpower',target=record_gpupower, args=(f,count))
    gutil = multiprocessing.Process(name='gutil',target=record_gpuutil, args=(g,count))
    gfan = multiprocessing.Process(name='gfan',target=record_gpufan, args=(h,count))

    ctemp.start()
    cclock.start()
    cutil.start()
    musage.start()
    gtemps.start()
    gpower.start()
    gutil.start()
    gfan.start()
    
    ctemp.join() 
    cclock.join()
    cutil.join()
    musage.join()
    gtemps.join()
    gpower.join()
    gutil.join()
    gfan.join()
    
    raw = dict()
    for spec in Q:
        raw.update(spec.get())
    for i in raw:
        custnameraw += initname + custname + '-' + i
        storeresults(raw[i], custnameraw)
        storesummary(raw[i], initname + custname, i)
        custnameraw = ''
    return True
    
custname = input("What would you like to call this test?\n")
curdate = time.localtime()
custname = "{}-{}-{}-{}-{}:{}:{}".format(custname, str(curdate[0]), str(curdate[1]), str(curdate[2]), str(curdate[3]), str(curdate[4]), str(curdate[5]))

gathval = False
print("Gathering idle stats\n")
gathval = run(GATHER_TIME, 'init-')    #run to gather idle specs
print("Idle stats gathered={}\n".format(gathval))
p = start_cpustress()
q = start_gpustress()
doneval = False
regname = ''
try:
    wait_for_warmup()
    doneval = run(SAMPLE_COUNT, regname)
finally:
    if doneval is True:
        p.terminate()
        q.terminate()
        p.wait()
        q.wait()
