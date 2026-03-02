import torch
from modelscope import snapshot_download
from transformers import AutoModelForCausalLM, AutoTokenizer

class LLMEngine:
    def __init__(self, model_id="Qwen/Qwen3-0.6B"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        if torch.backends.mps.is_available():
            self.device = "mps"
        
        self.model_name = model_id
        print(f"Loading LLM model on {self.device}...")
        try:
            model_dir = snapshot_download(model_id)
            self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_dir,
                torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
                device_map=self.device
            )
            print(f"Successfully loaded {model_id}")
        except Exception as e:
            print(f"Failed to load {model_id}: {e}")
            # Fallback
            fallback = "Qwen/Qwen2.5-0.5B-Instruct"
            self.model_name = fallback
            print(f"Trying fallback: {fallback}")
            try:
                model_dir = snapshot_download(fallback)
                self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_dir,
                    torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
                    device_map=self.device
                )
            except Exception as e2:
                 print(f"Fallback failed: {e2}")
                 self.model_name = "Load Failed"
                 raise e

    def process_text(self, text, context="", custom_prompt="", stream_callback=None):
        # If text is empty but context exists, treat context as the text to be refined
        target_text = text
        instruction = ""
        
        if not text and context:
            target_text = context
            instruction = "Refine the following text."
        elif text and context:
            # User spoke something while selecting text
            # Heuristic: if spoken text is short command, treat as instruction
            if len(text.split()) < 5:
                target_text = context
                instruction = text
            else:
                # Treat as combining both or context is just background
                target_text = f"{text}\nContext: {context}"
        
        if not target_text:
            return ""

        # Default system prompt (Agent Coding Optimization)
        base_system_prompt = (
            "You are an expert AI Coding Agent assistant. Your task is to refine the user's input "
            "into a clear, precise, and actionable prompt suitable for an LLM coding tool.\n"
            "Key Requirements:\n"
            "1. **Terminology**: Fix technical terms (e.g., 'params' -> 'parameters', 'json' -> 'JSON').\n"
            "2. **Structure**: Use Markdown lists for multi-step instructions.\n"
            "3. **Clarity**: Remove conversational filler ('um', 'like', 'maybe') and ambiguity.\n"
            "4. **Intent**: Explicitly state the action (Create, Debug, Refactor, Explain).\n"
            "5. **Thinking**: You MAY output a thinking process before the final result. If you do, enclose it in <think>...</think> tags.\n"
            "6. **Output**: Return the thinking process (optional) followed by the refined prompt text."
        )
        
        # If user provided custom prompt, prepend/replace or mix?
        # Usually custom prompt is "Translate to English" or "Make it formal"
        # If custom prompt is provided, we prioritize it over the base agent coding logic
        if custom_prompt:
             # Use the custom prompt as the primary instruction
             system_prompt = f"You are a helpful expert assistant. Your primary task is: {custom_prompt}\n" \
                             f"Please follow the instructions in the task description strictly.\n" \
                             f"If you need to think before answering, enclose your thoughts in <think>...</think> tags."
        else:
             system_prompt = base_system_prompt
        
        user_content = f"Input text: {target_text}"
        if instruction:
             user_content = f"Instruction: {instruction}\n{user_content}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        text_input = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=True # Qwen3 thinking mode
        )
        
        model_inputs = self.tokenizer([text_input], return_tensors="pt").to(self.device)
        
        # Streamer
        from transformers import TextIteratorStreamer
        streamer = TextIteratorStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True)
        
        generation_kwargs = dict(
            input_ids=model_inputs.input_ids,
            max_new_tokens=1024,
            do_sample=True,
            temperature=0.6,
            top_p=0.95,
            top_k=20,
            min_p=0,
            streamer=streamer
        )

        import threading
        thread = threading.Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()
        
        generated_text = ""
        for new_text in streamer:
            generated_text += new_text
            if stream_callback:
                stream_callback(generated_text)
                
        # Try to clean up thinking tokens if they leaked (TextIteratorStreamer usually handles skip_special_tokens)
        # But Qwen3 thinking format might be custom text like <think>...</think> if tokenizer doesn't mark them special.
        # Assuming Qwen3 tokenizer handles special tokens correctly.
        
        return generated_text
