var request = require('request');

module.exports = {

  isSwitchReady: function(callback) {
    urlApi = 'http://127.0.0.1:8080/packetgen/swready';
    request(urlApi, function(error, response, body) {
      if (!error && response.statusCode == 200) {
        callback(true);
      } else {
        callback(false);
      }
    });
  },

  startPkt: function() {
    urlApi = 'http://127.0.0.1:8080/packetgen/start';
    request(urlApi, function(error, response, body) {
      if (!error && response.statusCode == 200) {
        console.log('[200] Start looping');
      }
    });
  },

  stopPkt: function() {
    urlApi = 'http://127.0.0.1:8080/packetgen/stop';
    request(urlApi, function(error, response, body) {
      if (!error && response.statusCode == 200) {
        console.log('[200] Stop looping');
      }
    });
  },

  setOutputPort: function(outputPort) {
    request.put(
      {
        url: 'http://127.0.0.1:8080/packetgen/setoutput',
        json: {output: outputPort}
      },
      function(error, response, body) {
        if (!error && response.statusCode == 200) {
          console.log('[*] Set output port ' + outputPort);
        }
      });
  },

  setPayloadSize: function(size) {
    request.put(
      {
        url: 'http://127.0.0.1:8080/packetgen/setpktsize',
        json: {payloadSize: size}
      },
      function(error, response, body) {
        if (!error && response.statusCode == 200) {
          console.log('[*] Set packet size ' + size);
        }
      });
  },

  // startPktWithTuple: function(src, dst, src_ip, dst_ip, src_port, dst_port) {
  //   urlApi = 'http://127.0.0.1:8080/packetgen/start';
  //   request({
  //     url: urlApi,
  //     method: 'PUT',
  //     json:{src:src, dst:dst, src_ip:src_ip, dst_ip:dst_ip, src_port:src_ip, dst_port:dst_port},
  //     function(error, response, body) {
  //       if (!error && response.statusCode == 200) {
  //         console.log('Set 5 tuple' + json);
  //       }
  //     }
  //   });
  // },

  getStatis: function(callback) {
    urlApi = 'http://127.0.0.1:8080/packetgen/monitor';
    request(urlApi, function(error, response, body) {
      if (!error && response.statusCode == 200) {
        var statisJson = JSON.parse(body);
        callback(null, statisJson);
      }
    });
  },

};
