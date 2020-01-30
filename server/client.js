var pc = null;
var lastUpdate;
var statusCheckInterval;
var btn;
var media;
var btnClicked =false;

function statusCheck() {
    fetch('/check-state', {
        body: JSON.stringify({}),
        headers: {
            'Content-Type': 'application/json'
        },
        method: 'POST'
    })
        .then(function (response) {
            return response.json();
        })
        .then(function (response) {
            if (!response.last_update)
                return;
            newLastUpdate = new Date(response.last_update * 1000);
            console.log('response.last_update', newLastUpdate)
            if (btnClicked && (!lastUpdate || newLastUpdate > lastUpdate)) {
                console.log('RECONNET!!!!!!!!!!')
                console.log('response.last_update!!!!!!!!!!', newLastUpdate)
                console.log('lastUpdate!!!!!!!!!!', lastUpdate)
                try {
                    stop();
                } catch (error) {
                    console.log('err')
                }
               
                start();
            }
        })
        .catch(function (err) {

        })
}


statusCheckInterval = setInterval(statusCheck, 2000)

document.addEventListener('DOMContentLoaded', function () {
    console.log('DOMContentLoaded')


    btn = document.querySelector(".play-btn");
    media = document.querySelector("#media");
    btn.classList.add("elementToFadeIn");
    btn.addEventListener("click", function () {
        btn.classList.add("elementToFadeOut");
        // Wait until the animation is over and then remove the class, so that
        // the next click can re-add it.
        start()
        setTimeout(function () {
            btn.classList.remove("elementToFadeOut");
            btn.setAttribute("style", "visibility:hidden;");
            media.classList.add("elementToFadeIn");
            btnClicked = true;
        }, 1000);
    });
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
        lastUpdate = new Date();
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
    negotiate()

}

function stop() {

    // close peer connection
    pc.close();
}
