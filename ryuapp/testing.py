from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto import ether
from ryu.ofproto import inet
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import tcp
from ryu.lib.packet import udp
from ryu.lib.packet import arp
from ryu.lib.packet import ether_types
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.lib import dpid as dpid_lib
from ryu.lib import hub

from webob import Response
import json
from operator import attrgetter

from pkt_utils import pktgen

pkt_gen_instance = 'pkt_gen_api_app'

# url = '/packetgen/{dpid}'

url_sw_ready = '/packetgen/swready'
url_start = '/packetgen/start'
url_stop = '/packetgen/stop'
url_set_output_port = '/packetgen/setoutput'
url_set_payload_size = '/packetgen/setpktsize'
url_monitor = '/packetgen/monitor'

class PacketGenerator(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = { 'wsgi': WSGIApplication }

    def __init__(self, *args, **kwargs):
        super(PacketGenerator, self).__init__(*args, **kwargs)
        wsgi = kwargs['wsgi']
        wsgi.register(PacketGeneratorController, {pkt_gen_instance : self})
        self.switches = {}
        self.datapaths = {}
        self.port_one = 1
        self.port_two = 2
        self.pkt_size = 0

        self.port_thirteen = 13
        self.out_port = 0

        self.monitor_packet_count = 0
        self.monitor_byte_count = 0

        self.dut_eth_dst = 'a4:5e:60:c3:1a:2d'
        self.generator_eth_src = 'a4:5e:60:c3:1a:a0'
        self.dut_ip_dst = '192.168.8.200'
        self.generator_ip_src = '192.168.8.100'
        self.dut_dst_port = 5566
        self.generator_src_port = 7788

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        self.switches[datapath.id] = datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Table miss entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def _arp_request_handler(self, pkt_arp):
        data = None

        if pkt_arp.dst_ip == self.generator_ip_src:
            # Who has 192.168.8.100 ?
            # Tell 192.168.8.xxx (DUT),
            # 192.168.8.1's fake MAC address (eth1)
            data = pktgen.arp_reply(src_mac=self.generator_eth_src,
                                    src_ip=self.generator_ip_src,
                                    target_mac=pkt_arp.src_mac,
                                    target_ip=pkt_arp.src_ip)
        return data


    def install_flow_entry(self, dpid, out_port):
        print '[*] Install flow entry'
        datapath = self.switches.get(dpid)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # match_port_two = parser.OFPMatch(in_port=self.port_two,
        #                                  eth_type=ether.ETH_TYPE_IP,
        #                                  ip_proto=inet.IPPROTO_UDP)
        #
        # actions_port_one = [parser.OFPActionOutput(self.port_one)]
        #
        # self.add_flow(datapath, 100, match_port_two, actions_port_one)


        match_port_one = parser.OFPMatch(in_port=self.port_one,
                                         eth_type=ether.ETH_TYPE_IP,
                                         ip_proto=inet.IPPROTO_UDP)

        actions_port_two_outport = [parser.OFPActionOutput(self.port_two),
                                     parser.OFPActionOutput(out_port)]
        self.add_flow(datapath, 100, match_port_one, actions_port_two_outport)

    def create_send_packet(self, dpid, pkt_size, five_tuple=None):
        print '[*] Create and send packet to port 2'
        datapath = self.switches.get(dpid)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        if five_tuple is None:
            eth_dst = self.dut_eth_dst
            eth_src = self.generator_eth_src
            ip_dst = self.dut_ip_dst
            ip_src = self.generator_ip_src
            dst_port = self.dut_dst_port
            src_port = self.generator_src_port
        else:
            eth_dst = five_tuple[0]
            eth_src = five_tuple[1]
            ip_dst = five_tuple[2]
            ip_src = five_tuple[3]
            dst_port = int(five_tuple[4])
            src_port = int(five_tuple[5])

        data = pktgen.new_udp_pkt(eth_dst, eth_src,
                                  ip_dst, ip_src,
                                  src_port, dst_port, pkt_size)
        # Sending packet to port 2
        self._send_packet_to_port(datapath, self.port_two, data)

    def delete_flow_entry(self, dpid):
        print '[*] Delete flow entry'
        datapath = self.switches.get(dpid)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match_port_one = parser.OFPMatch(in_port=self.port_one)

        self.del_flow(datapath, match_port_one)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    def del_flow(self, datapath, match, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = []

        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    table_id=0, command=ofproto.OFPFC_DELETE,
                                    out_port=ofproto.OFPP_ANY,
                                    out_group=ofproto.OFPP_ANY,
                                    match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath,
                                    table_id=0, command=ofproto.OFPFC_DELETE,
                                    out_port=ofproto.OFPP_ANY,
                                    out_group=ofproto.OFPP_ANY,
                                    match=match,
                                    instructions=inst)
        datapath.send_msg(mod)

    def _send_packet_to_port(self, datapath, port, data):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        actions = [parser.OFPActionOutput(port=port)]
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ofproto.OFPP_CONTROLLER,
                                  actions=actions,
                                  data=data)
        datapath.send_msg(out)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)

        pkt_ethernet = pkt.get_protocol(ethernet.ethernet)
        pkt_arp = pkt.get_protocol(arp.arp)
        if pkt_arp:
            if pkt_arp.opcode == arp.ARP_REQUEST:
                print "[*] Detect DUT send ARP requet"
                arp_reply_pkt = self._arp_request_handler(pkt_arp)
                self._send_packet_to_port(datapath, in_port, arp_reply_pkt)
                print "[*] Reply DUT ARP reply"
            elif pkt_arp.opcode == arp.ARP_REPLY:
                pass

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath

        # If switch connect to controller
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath

        # If switch disconnect to controller
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]


    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

        # req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        # datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body
        for stat in body:
            if stat.priority == 100:
                self.monitor_packet_count = stat.packet_count
                self.monitor_byte_count = stat.byte_count
                return


class PacketGeneratorController(ControllerBase):

    def __init__(self, req, link, data, **config):
        super(PacketGeneratorController, self).__init__(req, link, data, **config)
        self.pkt_gen_app = data[pkt_gen_instance]

    @route('ready', url_sw_ready, methods=['GET'])
    def is_ready(self, req, **kwargs):
        pkt_gen = self.pkt_gen_app
        dpid = None

        for d in pkt_gen.datapaths.keys():
            dpid = d
            print 'DPID: %s' % dpid
            return Response(status=200)

        if dpid is None:
            print '[*] DPID Not in dict'
            return Response(status=404)


    @route('start', url_start, methods=['GET', 'PUT'])#, requirements={'dpid': dpid_lib.DPID_PATTERN})
    def start(self, req, **kwargs):
        pkt_gen = self.pkt_gen_app
        # dpid = dpid_lib.str_to_dpid(kwargs['dpid'])
        five_tuple = None
        dpid = None

        if req.body:
            d = json.loads(req.body)
            src = d.get('src')
            dst = d.get('dst')
            src_ip = d.get('src_ip')
            dst_ip = d.get('dst_ip')
            src_port = d.get('src_port')
            dst_port = d.get('dst_port')
            five_tuple = (src, dst, src_ip, dst_ip, src_port, dst_port)

        for d in pkt_gen.datapaths.keys():
            dpid = d
            print 'DPID: %s' % dpid

        if dpid is None:
            print '[*] DPID Not in dict'
            return Response(status=404)

        # if dpid not in pkt_gen.switches.keys():
        #     print '[*] Not in dict'
        #     return Response(status=404)

        # five_tuple = ('a4:5e:60:c3:1a:2d', 'a4:5e:60:c3:1a:a0',
        #               '192.168.55.66', '192.168.77.88', 5566, 7788)

        if pkt_gen.out_port == 0:
            out_port = 13
        else:
            out_port = pkt_gen.out_port


        pkt_gen.install_flow_entry(dpid, out_port)
        pkt_gen.create_send_packet(dpid, pkt_gen.pkt_size)
        return Response(status=200)

    @route('stop', url_stop, methods=['GET'])#, requirements={'dpid': dpid_lib.DPID_PATTERN})
    def stop(self, req, **kwargs):
        pkt_gen = self.pkt_gen_app
        dpid = None
        # dpid = dpid_lib.str_to_dpid(kwargs['dpid'])

        # if dpid not in pkt_gen.switches.keys():
        #     print '[*] Not in dict'
        #     return Response(status=404)

        for d in pkt_gen.datapaths.keys():
            dpid = d
            print 'DPID: %s' % dpid

        if dpid is None:
            print '[*] DPID Not in dict'
            return Response(status=404)

        pkt_gen.delete_flow_entry(dpid)
        return Response(status=200)

    @route('setoutput', url_set_output_port, methods=['PUT'])
    def set_output_port(self, req, **kwargs):
        pkt_gen = self.pkt_gen_app
        d = json.loads(req.body)
        out_port = d.get('output')
        pkt_gen.out_port = int(out_port)
        return Response(status=200)

    @route('setpktsize', url_set_payload_size, methods=['PUT'])
    def set_payload_size(self, req, **kwargs):
        pkt_gen = self.pkt_gen_app
        d = json.loads(req.body)
        size = d.get('payloadSize')
        pkt_gen.pkt_size = int(size)
        return Response(status=200)

    @route('monitor', url_monitor, methods=['GET'])
    def monitor(self, req, **kwargs):
        counters = {}
        pkt_gen = self.pkt_gen_app

        for dp in pkt_gen.datapaths.values():
            pkt_gen._request_stats(dp)

            # if (pkt_gen.monitor_packet_count > 0
            #     and pkt_gen.monitor_packet_count > 0):
        counters['packet_count'] = pkt_gen.monitor_packet_count
        counters['byte_count'] = pkt_gen.monitor_byte_count
        body = json.dumps(counters)
        return Response(content_type='application/json', body=body)
