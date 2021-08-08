import urllib.request
import urllib.parse
import time
import sys
import threading
import queue


# HOW TO USE
#==================================================================================================
# Arguments: load, number of threads, key to input values, URL ( in this order )
# Ex: 100000 20 h http://127.0.0.1:8080/v1/dup-check 
# -> will input 100000 data
# -> will process with 20 threads
# -> will input data to Hash_Value column (since it is referred to as 'h' in the URL)
# -> URL
# Latency / Load tester for services using flask URL arguments to input data into Google Datastore


# Variables
load = sys.argv[1]
thread = sys.argv[2]
key = sys.argv[3]
url = sys.argv[4]

loadn = int(load)
threadn = int(thread)

work = loadn // threadn

total = 0

# Intro
print('Data load : ' + load)

# Main function
def test_check(load_start, load_end, key, q):

    total_time = 0

    for i in range(load_start, load_end): 

        data = {}
        data[key] = str(i)
        url_values = urllib.parse.urlencode(data)
        full_url = url + '?' + url_values

        start = time.perf_counter()
        data = urllib.request.urlopen(full_url)
        end = time.perf_counter() - start
        total_time += end
        print('Test ' + str(i + 1) + ' : ' + '{:.6f}s'.format(end))

    q.put(total_time)

# Queue declaration
q = queue.Queue()

# Thread creation
t_list = []

for i in range(threadn):
    s = i * (work)
    e = (i + 1) * (work)
    t_list.append(threading.Thread(target=test_check, args=(s, e, key, q)))

for t in t_list:
    t.start()

for t in t_list:
    t.join()

# Output production
i = 1
while not q.empty():
    result = q.get()
    print("Time " + str(i) + " : " + str(result))
    print("Time " + str(i) + " average : " + str(result / work))
    total += result
    i += 1

# Result printed
print("Total time : " + str(total))
print("Total Average time : " + str(total / loadn))
print("Average running time for each thread : " + str(total / threadn))

 