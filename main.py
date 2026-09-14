import torch
import time
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)

MODEL_NAME = "Qwen/Qwen3-4B"
print("Loading Rune Stone...")

# 4-bit quantization configuration
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=quantization_config,
    device_map="auto",
)


print("Model loaded!")
print("Model device:", model.device)
print(
    "GPU memory allocated:",
    round(torch.cuda.memory_allocated() / 1024**3, 2),
    "GB"
)

while True:
    prompt = input("\nYou: ")

    if prompt.lower() in ["exit", "quit"]:
        break

    messages = [
        {"role": "user", "content": prompt}
    ]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )

    inputs = tokenizer(
        [text],
        return_tensors="pt"
    ).to(model.device)
    # Synchronize GPU before timing 
    torch.cuda.synchronize() 
    start = time.perf_counter()
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=100,
            temperature=0.7,
            top_p=0.8,
        )
        # Wait for GPU work to finish 
        torch.cuda.synchronize() 
        elapsed = time.perf_counter() - start 
        new_tokens = outputs.shape[1] - inputs.input_ids.shape[1] 
        tokens_per_second = new_tokens / elapsed

    response = outputs[0][inputs.input_ids.shape[1]:]

    print("\nRune Stone:")
    print(
        tokenizer.decode(
            response,
            skip_special_tokens=True
        )
    )
    print("\n--- Benchmark ---") 
    print(f"Generated tokens : {new_tokens}") 
    print(f"Generation time : {elapsed:.2f} sec") 
    print(f"Speed : {tokens_per_second:.2f} tokens/sec")