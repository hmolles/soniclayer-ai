"""Audio utilities for waveform extraction and processing."""
import numpy as np
from pathlib import Path

try:
    import soundfile as sf
    USE_SOUNDFILE = True
except ImportError:
    USE_SOUNDFILE = False

try:
    from scipy.io import wavfile
    USE_SCIPY = True
except ImportError:
    import wave
    USE_SCIPY = False


def extract_waveform(audio_path):
    """
    Extract time and amplitude data from audio file.
    Supports both standard WAV and FLAC-compressed WAV formats.
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Tuple of (time_array, amplitude_array)
    """
    try:
        if not Path(audio_path).exists():
            print(f"Warning: Audio file not found: {audio_path}")
            return np.array([0, 1]), np.array([0, 0])  # Return minimal valid data
        
        # Try soundfile first - handles FLAC, WAV, and other formats
        if USE_SOUNDFILE:
            try:
                audio_data, sample_rate = sf.read(audio_path)
                
                # Handle stereo by taking first channel
                if len(audio_data.shape) > 1:
                    audio_data = audio_data[:, 0]
                
                # Normalize amplitude (soundfile returns float64 in [-1, 1] range)
                amplitude = audio_data.astype(float)
                
                # Create time array
                n_frames = len(amplitude)
                duration = n_frames / sample_rate
                time = np.linspace(0, duration, n_frames)
                
                # Downsample for faster rendering (max 10000 points)
                if n_frames > 10000:
                    step = n_frames // 10000
                    time = time[::step]
                    amplitude = amplitude[::step]
                
                return time, amplitude
            except Exception as e:
                print(f"Warning: soundfile failed for {audio_path}: {e}")
                # Fall through to scipy/wave
        
        if USE_SCIPY:
            # Use scipy which handles standard WAV formats
            sample_rate, audio_data = wavfile.read(audio_path)
            
            # Handle stereo by taking first channel
            if len(audio_data.shape) > 1:
                audio_data = audio_data[:, 0]
            
            # Normalize amplitude
            if audio_data.dtype == np.int16:
                amplitude = audio_data.astype(float) / 32768.0
            elif audio_data.dtype == np.int32:
                amplitude = audio_data.astype(float) / 2147483648.0
            elif audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
                amplitude = audio_data.astype(float)
            else:
                amplitude = audio_data.astype(float) / np.max(np.abs(audio_data))
            
            # Create time array
            n_frames = len(amplitude)
            duration = n_frames / sample_rate
            time = np.linspace(0, duration, n_frames)
            
            # Downsample for faster rendering (max 10000 points)
            if n_frames > 10000:
                step = n_frames // 10000
                time = time[::step]
                amplitude = amplitude[::step]
            
            return time, amplitude
        else:
            # Fallback to wave module (doesn't support float WAV)
            with wave.open(audio_path, 'rb') as wav_file:
                # Read parameters
                sample_rate = wav_file.getframerate()
                n_frames = wav_file.getnframes()
                
                if n_frames == 0:
                    print(f"Warning: Audio file has no frames: {audio_path}")
                    return np.array([0, 1]), np.array([0, 0])
                
                audio_data = wav_file.readframes(n_frames)
                
                # Convert to numpy array
                if wav_file.getsampwidth() == 2:
                    amplitude = np.frombuffer(audio_data, dtype=np.int16)
                else:
                    amplitude = np.frombuffer(audio_data, dtype=np.uint8)
                
                # Normalize amplitude
                max_amp = np.max(np.abs(amplitude))
                if max_amp > 0:
                    amplitude = amplitude.astype(float) / max_amp
                else:
                    amplitude = amplitude.astype(float)
                
                # Create time array
                duration = n_frames / sample_rate
                time = np.linspace(0, duration, n_frames)
                
                # Downsample for faster rendering (max 10000 points)
                if n_frames > 10000:
                    step = n_frames // 10000
                    time = time[::step]
                    amplitude = amplitude[::step]
                
                return time, amplitude
    except Exception as e:
        # Return minimal valid arrays on error
        print(f"Error extracting waveform from {audio_path}: {e}")
        import traceback
        traceback.print_exc()
        return np.array([0, 1]), np.array([0, 0])
