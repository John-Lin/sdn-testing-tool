def set_meter_entry(datapath, bandwidth, id, mod):
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        command = None
        if mod == 'ADD':
            command = ofproto.OFPMC_ADD
        elif mod == 'MODIFY':
            command = ofproto.OFPMC_MODIFY
        elif mod == 'DELETE':
            command = ofproto.OFPMC_DELETE

        print command, type(command)
        # Policing for Scavenger class
        band = parser.OFPMeterBandDrop(rate=bandwidth,
                                       burst_size=5)
        req = parser.OFPMeterMod(datapath, command,
                                 ofproto.OFPMF_KBPS, id, [band])
        datapath.send_msg(req)

def add_flow_for_ratelimite(datapath, priority, match, actions, meter, buffer_id=None):
    ofproto = datapath.ofproto
    parser = datapath.ofproto_parser
    # print "aaaaa",datapath, priority, match, actions, meter, type(meter)
    inst = [parser.OFPInstructionMeter(int(meter)), parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

    if buffer_id:
        mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                priority=priority, match=match,
                                instructions=inst)
    else:
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
    datapath.send_msg(mod)
