// Function to initialize the player
function initializePlayer() {
    // Retrieve playback state from local storage
    const playbackState = JSON.parse(localStorage.getItem('playbackState'));
    
    // If playback state exists, update player with stored state
    if (playbackState) {
        const audioPlayer = document.getElementById('audioPlayer');
        audioPlayer.src = playbackState.currentSong;
        audioPlayer.currentTime = playbackState.currentTime;
        // You can also update UI elements like song title, artist, etc.
    }
    }

    // Function to handle page transitions
    function handlePageTransition() {
    // Save playback state to local storage when navigating away from the page
    window.addEventListener('beforeunload', function() {
        const audioPlayer = document.getElementById('audioPlayer');
        const playbackState = {
        currentSong: audioPlayer.src,
        currentTime: audioPlayer.currentTime
        };
        localStorage.setItem('playbackState', JSON.stringify(playbackState));
    });
    }

    // Function to start playback
    function startPlayback(songURL) {
    const audioPlayer = document.getElementById('audioPlayer');
    audioPlayer.src = songURL;
    audioPlayer.play();
    }

    // Call initialization function when the page loads
    window.addEventListener('load', function() {
    initializePlayer();
    handlePageTransition();
    });

    // Example usage:
    // Call startPlayback() with the URL of the song you want to play
    startPlayback('Srivalli(PaglaSongs).mp3');


    document.getElementById("playsong").addEventListener("click", function() {
        var audio = document.getElementById("myAudio");
        audio.play();
      });
      