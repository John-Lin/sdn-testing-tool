from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.ofproto.ether import ETH_TYPE_ARP
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4
from ryu.lib.packet import udp
from ryu.ofproto import ether
from ryu.lib import pcaplib

import os
import copy

BROADCAST = 'ff:ff:ff:ff:ff:ff'
TARGET_MAC_ADDRESS = '00:00:00:00:00:00'

def arp_reply(src_mac, src_ip, target_mac, target_ip):
    # Creat an empty Packet instance
    pkt = packet.Packet()

    pkt.add_protocol(ethernet.ethernet(ethertype=ETH_TYPE_ARP,
                                       dst=target_mac,
                                       src=src_mac))

    pkt.add_protocol(arp.arp(opcode=arp.ARP_REPLY,
                             src_mac=src_mac,
                             src_ip=src_ip,
                             dst_mac=target_mac,
                             dst_ip=target_ip))

    # Packet serializing
    pkt.serialize()
    data = pkt.data
    return data

def broadcast_arp_request(src_mac, src_ip, target_ip):
    pkt = packet.Packet()
    pkt.add_protocol(ethernet.ethernet(ethertype=ETH_TYPE_ARP,
                                       dst=BROADCAST,
                                       src=src_mac))

    pkt.add_protocol(arp.arp(opcode=arp.ARP_REQUEST,
                             src_mac=src_mac,
                             src_ip=src_ip,
                             dst_mac=TARGET_MAC_ADDRESS,
                             dst_ip=target_ip))
    pkt.serialize()
    data = pkt.data
    return data

def new_udp_pkt(eth_dst, eth_src, ip_dst, ip_src, src_port, dst_port, size=0):
    # pcap_pen = pcaplib.Writer(open('pkt.pcap', 'wb'))
    # Creat an empty Packet instance
    pkt = packet.Packet()

    pkt.add_protocol(ethernet.ethernet(ethertype=0x0800, dst=eth_dst,
                                       src=eth_src))

    pkt.add_protocol(ipv4.ipv4(dst=ip_dst, src=ip_src, proto=17))
    pkt.add_protocol(udp.udp(src_port=src_port, dst_port=dst_port))

    # Check how many byte be used under layer 3
    _pkt = copy.deepcopy(pkt)
    _pkt.serialize()
    _d = _pkt.data

    # the max. packet size is 1500 byte
    limited_size = 1500 - len(_d)

    # if size larger than 1500 byte set limit size
    if size >= limited_size:
        size = limited_size

    if size != 0:
        payload = os.urandom(size)
        # Add payload
        pkt.add_protocol(payload)

    # Packet serializing
    pkt.serialize()
    data = pkt.data
    # pcap_pen.write_pkt(data)
    return data

if __name__ == '__main__':
    dut_eth_dst = 'a4:5e:60:c3:1a:2d'
    generator_eth_src = 'a4:5e:60:c3:1a:a0'
    dut_ip_dst = '192.168.8.200'
    generator_ip_src = '192.168.8.100'
    dut_dst_port = 5566
    generator_src_port = 7788
    new_udp_pkt(dut_eth_dst, generator_eth_src, dut_ip_dst, generator_ip_src, dut_dst_port, generator_src_port, 2000)
