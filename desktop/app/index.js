var controller = require('./controller.js');

controller.isSwitchReady(function(status){
  if(!status){
    console.log('OpenFlow switch or Controller is not ready!');
    // alert('OpenFlow switch or Controller is not ready!');
  }
});

$(document).ready(function(){
  $('.menu .item').tab();
  $('.ui.checkbox').checkbox();
  $('.ui.toggle.button').state({
    text: {
      inactive : 'Send',
      active   : 'Sending'
    }
  });

  $('#send-btn').click(function(){
    $self = $(this);

    var outputPortNum = $("#outputPort").val();
    var pktSize = $("#pktSize").val();

    if($self.hasClass('active')) {
      if (!outputPortNum) {
        $("#dutInPortField").removeClass('inline field').addClass('inline field error');
        return
      }

      if (!pktSize) {
        $("#pktSizeField").removeClass('inline field').addClass('inline field error');
        return
      }

      controller.setOutputPort(outputPortNum);
      // console.log('outputPortNum' + outputPortNum);
      controller.setPayloadSize(pktSize);
      controller.startPkt();

      var currentPkt = 0;
      var lastPkt = 0;
      var currentByte = 0;
      var lastByte = 0;

      function updateStatis() {
        controller.getStatis(function(err, result){

          // var pktCount = Math.round(new Date().getTime() / 1000);
          // var byteCount = Math.round(new Date().getTime() / 1000 * 8);
          var pktCount = result['packet_count'];
          var byteCount = result['byte_count'];

          currentPkt = pktCount;
          currentByte = byteCount;

          // var pktDiff = (currentPkt - lastPkt) / 5;
          var mbps = Math.round((currentByte - lastByte) * 8 / 1024 / 1024 / 5 * 10) / 10;

          // $('.pps').text(pktDiff);
          // $('.packet-count').text(currentPkt);
          $('.mbps').text(mbps);

          // lastPkt = result['packet_count'];
          lastPkt = pktCount;
          lastByte = byteCount;

        });
      }

      nIntervId = setInterval(updateStatis, 5000);

    } else {
        clearInterval(nIntervId);
        controller.stopPkt();

        // $('.pps').text('0');
        // $('.packet-count').text('0');
        $('.mbps').text('0');

        var currentPkt = 0;
        var lastPkt = 0;
        var currentBit = 0;
        var lastBit = 0;

    }

  });

});
