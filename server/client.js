var pc = null;


document.addEventListener('DOMContentLoaded', function () {
    console.log('DOMContentLoaded')


    var btn = document.querySelector(".play-btn");
    var media = document.querySelector("#media");
    btn.classList.add("elementToFadeIn");

    btn.addEventListener("click", function () {
        btn.classList.add("elementToFadeOut");
        // Wait until the animation is over and then remove the class, so that
        // the next click can re-add it.
        setTimeout(function () {
            btn.classList.remove("elementToFadeOut");
            btn.setAttribute("style", "visibility:hidden;");
            media.classList.add("elementToFadeIn");
            start()

        }, 1000);
    });
});

function negotiate() {
    alert('negotiate')

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
        console.log('e: ', e)
    });
}

function start() {
    var config = {
        sdpSemantics: 'unified-plan'
    };

    config.iceServers = [
        {
            'urls': 'stun:stun.l.google.com:19302'
        }
    ];

    pc = new RTCPeerConnection(config);

    // connect audio / video
    pc.addEventListener('track', function (evt) {
        document.getElementById('video').srcObject = evt.streams[0];
    });
    alert('start')
    negotiate()

}

function stop() {

    // close peer connection
    setTimeout(function () {
        pc.close();
    }, 500);
}
