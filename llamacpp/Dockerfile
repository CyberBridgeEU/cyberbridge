# llama.cpp LLM Server
# Efficient CPU-optimized inference without the Ollama Go wrapper overhead.
# Model: phi-4 Q4_K_M quantization (~9GB) from bartowski/phi-4-GGUF
FROM ghcr.io/ggml-org/llama.cpp:server

# Download the quantized model at build time
RUN mkdir -p /models && \
    apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && \
    curl -L -o /models/phi-4-Q4_K_M.gguf \
        "https://huggingface.co/bartowski/phi-4-GGUF/resolve/main/phi-4-Q4_K_M.gguf" && \
    rm -rf /var/lib/apt/lists/*

# Configurable via environment variables
ENV LLAMA_THREADS=16
ENV LLAMA_PARALLEL=2
ENV LLAMA_CTX_SIZE=8192
ENV LLAMA_BATCH_SIZE=512

EXPOSE 11435

# Override base image entrypoint to allow env var expansion
ENTRYPOINT []
CMD ["/bin/sh", "-c", "/app/llama-server --model /models/phi-4-Q4_K_M.gguf --threads ${LLAMA_THREADS} --ctx-size ${LLAMA_CTX_SIZE} --batch-size ${LLAMA_BATCH_SIZE} --parallel ${LLAMA_PARALLEL} --port 11435 --host 0.0.0.0"]
