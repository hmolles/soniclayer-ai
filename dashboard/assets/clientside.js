window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        update_current_time: function(n_intervals) {
            const audioElement = document.getElementById('audio-player');
            
            if (audioElement && audioElement.currentTime !== undefined && !isNaN(audioElement.currentTime)) {
                console.log('[CLIENTSIDE] Audio time:', audioElement.currentTime);
                return audioElement.currentTime;
            }
            
            console.log('[CLIENTSIDE] No audio element or invalid time');
            return window.dash_clientside.no_update;
        },
        
        seek_audio: function(click_data) {
            if (!click_data) {
                return window.dash_clientside.no_update;
            }
            
            // Get clicked time from waveform
            const clicked_time = click_data.points[0].x;
            
            // Find and seek the audio element
            const audioElement = document.getElementById('audio-player');
            if (audioElement) {
                console.log('[CLIENTSIDE] Seeking to:', clicked_time);
                audioElement.currentTime = clicked_time;
            }
            
            return true;  // Set user-clicked flag
        }
    }
});
