import psutil

psutil.cpu_times()

INTERVAL = 5
COUNT = 60

print "Each measurement time interval:", INTERVAL
print "Total measurement count:", COUNT
print "Total Time:", INTERVAL * COUNT, "second"
print "Start >>\n"

for x in range(COUNT):
    print "CPU usage: ", psutil.cpu_percent(interval=INTERVAL)

# for x in range(60):
#     print "CPU usage per CPU: ", psutil.cpu_percent(interval=INTERVAL, percpu=True)
