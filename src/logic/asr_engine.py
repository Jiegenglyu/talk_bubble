import os
import torch
import numpy as np
from qwen_asr import Qwen3ASRModel
from modelscope import snapshot_download
import soundfile as sf
import tempfile

class ASREngine:
    def __init__(self, model_id="Qwen/Qwen3-ASR-0.6B"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # Apple Silicon support (MPS)
        if torch.backends.mps.is_available():
            self.device = "mps" 
        
        # qwen-asr might not fully support MPS yet, fallback to CPU if issues arise.
        # However, transformers usually handles it. Let's try CPU first for stability as per qwen-asr notes.
        # If performance is an issue, we can try "mps".
        self.device = "cpu" 

        print(f"Loading ASR model {model_id} on {self.device}...")
        try:
            # Download from ModelScope
            model_dir = snapshot_download(model_id)
            self.model = Qwen3ASRModel.from_pretrained(
                model_dir,
                device_map=self.device
            )
            print(f"Successfully loaded {model_id}")
        except Exception as e:
            print(f"Failed to load {model_id}: {e}")
            raise e

    def transcribe(self, audio_data, sample_rate=16000):
        # Qwen3-ASR expects a file path or potentially raw audio.
        # Let's save to a temp file to be safe and compatible with most APIs.
        
        try:
            # Check if audio_data is valid
            if audio_data is None or len(audio_data) == 0:
                print("ASR Warning: Received empty audio data")
                return ""
                
            # Normalize float32 audio to -1.0 to 1.0 if needed, but sounddevice usually gives float32
            # Qwen3-ASR via transformers pipeline or qwen-asr package often handles file paths best.
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                # Ensure audio_data is compatible with soundfile write
                sf.write(tmp_file.name, audio_data, sample_rate)
                tmp_path = tmp_file.name

            print(f"ASR Debug: Audio saved to {tmp_path}, size: {len(audio_data)} samples")

            # Transcribe
            # language="auto" causes error in qwen-asr 0.0.6 if it expects exact match or None
            # Based on error message: Unsupported language: Auto. Supported: ['Chinese', 'English', ...]
            # It seems it is case sensitive or doesn't support "auto" string.
            # Usually for auto detection, we should pass None or omit the argument if default is auto.
            # But let's try omitting it first, or passing None.
            res = self.model.transcribe(tmp_path) 
            print(f"ASR Debug: Raw result: {res}")
            
            # Cleanup
            os.remove(tmp_path)
            
            # Result parsing logic
            # Debug output showed: [ASRTranscription(language='Chinese', text='...', time_stamps=None)]
            # It seems res is a list of objects, not dicts.
            if isinstance(res, list):
                text_parts = []
                for item in res:
                    if hasattr(item, 'text'):
                        text_parts.append(item.text)
                    elif isinstance(item, dict) and 'text' in item:
                        text_parts.append(item['text'])
                    elif isinstance(item, str):
                        text_parts.append(item)
                
                text = " ".join(text_parts)
                return text
            elif hasattr(res, 'text'):
                 return res.text
            elif isinstance(res, dict):
                 return res.get('text', '')
            
            return str(res)
            
        except Exception as e:
            print(f"Transcription error: {e}")
            import traceback
            traceback.print_exc()
            return ""
