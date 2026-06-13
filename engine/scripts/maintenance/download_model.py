"""
DeepFind — Download Model for Packaging (Step 21)
Downloads the sentence-transformers model locally for bundling.
"""
import os
import sys
from huggingface_hub import snapshot_download

# Path relative to this script
target_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bundled_models", "all-MiniLM-L6-v2"))

print(f"Downloading model to: {target_dir}")
os.makedirs(target_dir, exist_ok=True)

try:
    # We only need the core PyTorch bin, config, tokenizer, and pooling/modules configs
    # We can ignore TensorFlow/Rust/Flax/ONNX models if they exist, but sentence-transformers usually just has pytorch_model.bin
    snapshot_download(
        repo_id="sentence-transformers/all-MiniLM-L6-v2",
        local_dir=target_dir,
        ignore_patterns=["*.msgpack", "*.h5", "*.tflite", "*.ot"],
        local_dir_use_symlinks=False # Ensure actual files are copied for packaging
    )
    print("Download complete.")
except Exception as e:
    print(f"Failed to download model: {e}")
    sys.exit(1)
