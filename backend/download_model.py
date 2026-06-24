"""预下载 Qwen3-8B 模型到本地缓存.

用法:
    conda activate quant
    cd backend
    python download_model.py

环境变量:
    TRANSFORMERS_MODEL_NAME: 模型名称 (默认: Qwen/Qwen3-8B)
    HF_HOME: 缓存目录 (默认: ~/.cache/huggingface)
    HF_ENDPOINT: 镜像源 (可选, 如 https://hf-mirror.com)
"""

import os
import sys


def download_model(model_name: str = "Qwen/Qwen3-8B"):
    """下载模型文件和 tokenizer."""
    cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
    print(f"[*] 开始下载模型: {model_name}")
    print(f"[*] 缓存目录: {cache_dir}")
    print("[*] 模型约 15GB，预计需要 10-30 分钟（取决于网络速度）")
    print("[*] 支持断点续传，中断后重新运行会继续下载\n")

    try:
        from huggingface_hub import snapshot_download

        # 只下载 safetensors + json + tokenizer 相关文件
        cache_path = snapshot_download(
            repo_id=model_name,
            repo_type="model",
            allow_patterns=[
                "*.json",
                "*.safetensors",
                "*.model",
                "*.txt",
                "tokenizer*",
                "vocab*",
                "merges*",
                "config.*",
            ],
            resume_download=True,
        )

        print(f"\n[✓] 模型下载完成!")
        print(f"    模型名称: {model_name}")
        print(f"    缓存路径: {cache_path}")
        print("\n[*] 现在可以启动后端，模型会自动加载到显存。")
        return cache_path

    except KeyboardInterrupt:
        print("\n[!] 下载被用户中断，已缓存的部分下次会继续下载。")
        sys.exit(0)
    except Exception as e:
        print(f"\n[✗] 下载失败: {e}")
        print("\n[*] 常见问题:")
        print("    1. 网络问题: 可尝试设置 HF_ENDPOINT=https://hf-mirror.com")
        print("    2. 磁盘空间: 确保缓存目录所在盘有 20GB+ 空间")
        print("    3. 权限问题: 确保有写入缓存目录的权限")
        sys.exit(1)


if __name__ == "__main__":
    model = os.getenv("TRANSFORMERS_MODEL_NAME", "Qwen/Qwen3-8B")
    download_model(model)
