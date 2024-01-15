var pc = null;
function createPeerConnection() {
  var config = {
    sdpSemantics: "unified-plan",
  };

  config.iceServers = [
    {
      urls: ["stun:stun1.1.google.com:19302", "stun:stun2.1.google.com:19302"],
    },
  ];

  pc = new RTCPeerConnection(config);
  pc.addEventListener("track", function(evt) {
    console.log("recieved stream");
    document.getElementById("video").srcObject = evt.streams[0];
  });

  return pc;
}

function negotiate() {
  console.log("negotiate");
  return pc
    .createOffer()
    .then(function(offer) {
      return pc.setLocalDescription(offer);
    })
    .then(function() {
      // wait for ICE gathering to complete
      return new Promise(function(resolve) {
        if (pc.iceGatheringState === "complete") {
          resolve();
        } else {
          function checkState() {
            if (pc.iceGatheringState === "complete") {
              pc.removeEventListener("icegatheringstatechange", checkState);
              resolve();
            }
          }
          pc.addEventListener("icegatheringstatechange", checkState);
        }
      });
    })
    .then(function() {
      var offer = pc.localDescription;
      console.log(
        "offer generated: " + JSON.stringify(offer).substring(0, 15) + "..."
      );
      console.log("offer");
      return fetch("/offer", {
        body: JSON.stringify({
          sdp: offer.sdp,
          type: offer.type,
        }),
        headers: {
          "Content-Type": "application/json",
        },
        method: "POST",
      });
    })
    .then(function(response) {
      return response.json();
    })
    .then(function(answer) {
      console.log(
        "answer recieved: " + JSON.stringify(answer).substring(0, 15) + "..."
      );
      return pc.setRemoteDescription(answer);
    })
    .catch(function(e) {
      alert(e);
    });
}
function start() {
  console.log("hello");
  pc = createPeerConnection();
  dc = pc.createDataChannel("chat");
  dc.onclose = function() {};

  dc.onopen = function() {};

  dc.onmessage = function(evt) {
    console.log(evt.data);
  };

  navigator.mediaDevices
    .getUserMedia({
      video: { width: 160, height: 120, frameRate: { max: 3 } },
      audio: false,
    })
    .then(
      function(stream) {
        stream.getTracks().forEach(function(track) {
          pc.addTrack(track, stream);
        });
        return negotiate();
      },
      function(err) {
        alert("Could not acquire media: " + err);
      }
    );
}
