import requests
import time

current = 0
last = 0

while True:
    time.sleep(5)
    r = requests.get('http://127.0.0.1:8080/packetgen/monitor')
    current = r.json().get('byte_count')

    kbps_str = str((current - last) * 8 / 1024.0 / 5.0) + ' Kbps'
    mbps_str = str((current - last) * 8 / 1024.0 / 1024.0 / 5.0) + ' Mbps'

    print mbps_str + ', ' + kbps_str

    # print r.json()
    last = r.json().get('byte_count')

# while True:
#     time.sleep(5)
#     r  = requests.get('http://127.0.0.1:8080/packetgen/monitor')
#     current = r.json().get('packet_count')
#
#     pkt_diff = str((current - last) / 5.0)
#
#     print pkt_diff
#
#     # print r.json()
#     last = r.json().get('packet_count')
