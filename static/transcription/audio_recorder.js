document.addEventListener("DOMContentLoaded", function () {
    const startButtons = document.querySelectorAll(".start-recording");
    const stopButtons = document.querySelectorAll(".stop-recording");
    const audioPreviews = document.querySelectorAll(".audio-preview");
    const audioDataInputs = document.querySelectorAll(".audio-data");

    function setupRecording(index) {
        let mediaRecorder;
        let audioChunks = [];

        const startButton = startButtons[index];
        const stopButton = stopButtons[index];
        const audioPreview = audioPreviews[index];
        const audioDataInput = audioDataInputs[index];

        startButton.onclick = function () {
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(function (stream) {
                    mediaRecorder = new MediaRecorder(stream);

                    mediaRecorder.ondataavailable = function (event) {
                        audioChunks.push(event.data);
                    };

                    mediaRecorder.onstop = function () {
                        const audioBlob = new Blob(audioChunks, { 'type': 'audio/wav' });
                        const audioURL = URL.createObjectURL(audioBlob);
                        audioPreview.src = audioURL;

                        const reader = new FileReader();
                        reader.readAsDataURL(audioBlob);
                        reader.onloadend = function () {
                            audioDataInput.value = reader.result;
                        };
                    };

                    mediaRecorder.start();
                    audioChunks = [];
                    startButton.disabled = true;
                    stopButton.disabled = false;
                })
                .catch(function (err) {
                    console.error('Error accessing microphone', err);
                    alert('Error accessing microphone. Please ensure you have granted the necessary permissions.');
                });
        };

        stopButton.onclick = function () {
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
                startButton.disabled = false;
                stopButton.disabled = true;
            }
        };
    }

    startButtons.forEach((button, index) => {
        setupRecording(index);
    });
});