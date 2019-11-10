var pc = null;


document.addEventListener('DOMContentLoaded', function () {
    console.log('DOMContentLoaded')
    start()
});

function negotiate() {
    pc.addTransceiver('video', { direction: 'recvonly' });
    pc.addTransceiver('audio', { direction: 'recvonly' });
    return pc.createOffer().then(function (offer) {
        return pc.setLocalDescription(offer);
    }).then(function () {
        // wait for ICE gathering to complete
        return new Promise(function (resolve) {
            if (pc.iceGatheringState === 'complete') {
                resolve();
            } else {
                function checkState() {
                    if (pc.iceGatheringState === 'complete') {
                        pc.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                }
                pc.addEventListener('icegatheringstatechange', checkState);
            }
        });
    }).then(function () {
        var offer = pc.localDescription;
        return fetch('/stream', {
            body: JSON.stringify({
                sdp: offer.sdp,
                type: offer.type,
                track_id: 0
            }),
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'POST'
        });
    }).then(function (response) {
        return response.json();
    }).then(function (answer) {
        return pc.setRemoteDescription(answer);
    }).catch(function (e) {
       console.log('e: ',e)
    });
}

function start() {
    console.log('Start ')
    var config = {
        sdpSemantics: 'unified-plan'
    };

    config.iceServers = [
        {
            'url': 'stun:stun.l.google.com:19302'
        }
    ];

    pc = new RTCPeerConnection(config);

    // connect audio / video
    pc.addEventListener('track', function (evt) {
        if (evt.track.kind == 'video') {
            document.getElementById('video').srcObject = evt.streams[0];
        } else {
            document.getElementById('audio').srcObject = evt.streams[0];
        }
    });
    negotiate()

}

function stop() {

    // close peer connection
    setTimeout(function () {
        pc.close();
    }, 500);
}
