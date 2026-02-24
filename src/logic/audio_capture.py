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
                # Normalize a bit? 
                # Typical speech might be low, boost it visually
                level = min(rms * 20, 1.0) # Increased gain for better visibility
                self.level_callback(level)

    def start_recording(self):
        self.recording = True
        self.buffer = []
        # Clear queue
        with self.audio_queue.mutex:
            self.audio_queue.queue.clear()
            
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=self.callback
        )
        self.stream.start()

    def stop_recording(self):
        self.recording = False
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        
        # Collect all data from queue
        while not self.audio_queue.empty():
            self.buffer.append(self.audio_queue.get())
            
        if not self.buffer:
            return None
            
        return np.concatenate(self.buffer, axis=0)
