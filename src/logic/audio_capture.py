import sounddevice as sd
import numpy as np
import threading
import queue

class AudioCapture:
    def __init__(self, sample_rate=16000, level_callback=None):
        self.sample_rate = sample_rate
        self.channels = 1
        self.recording = False
        self.audio_queue = queue.Queue()
        self.buffer = []
        self.level_callback = level_callback

    def callback(self, indata, frames, time, status):
        if status:
            print(status)
        if self.recording:
            self.audio_queue.put(indata.copy())
            
            # Calculate audio level for visualization
            if self.level_callback:
                # RMS amplitude
                rms = np.sqrt(np.mean(indata**2))
                
                # Amplified RMS for visibility
                # Use a high gain so even soft speech is visible
                amplified = rms * 40
                
                # Clamp to 0.0 - 1.0
                level = min(amplified, 1.0)
                
                self.level_callback(level)

    def start_recording(self):
        self.recording = True
        self.buffer = []
        # Clear queue
        with self.audio_queue.mutex:
            self.audio_queue.queue.clear()
            
        # Use a fixed blocksize for consistent UI update rate
        # 16000Hz / 1024 samples ~= 15 updates per second
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            blocksize=1024, 
            channels=self.channels,
            callback=self.callback
        )
        self.stream.start()

    def read_available_audio(self):
        """Read all available audio chunks from the queue without stopping."""
        new_data = []
        while not self.audio_queue.empty():
            try:
                chunk = self.audio_queue.get_nowait()
                new_data.append(chunk)
                self.buffer.append(chunk)  # Keep a copy for stop_recording
            except queue.Empty:
                break
        
        if not new_data:
            return None
            
        return np.concatenate(new_data, axis=0)

    def stop_recording(self):
        self.recording = False
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        
        # Collect all remaining data from queue
        while not self.audio_queue.empty():
            self.buffer.append(self.audio_queue.get())
            
        if not self.buffer:
            return None
            
        return np.concatenate(self.buffer, axis=0)
