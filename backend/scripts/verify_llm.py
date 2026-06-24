"""验证 LLM 模型接入状态."""
import sys
sys.path.insert(0, "d:/quant_app/quant-trading-app/backend")

from app.core.config import settings

print("=" * 60)
print("LLM 配置检查")
print("=" * 60)
print(f"  LLM_BACKEND:         {settings.LLM_BACKEND}")
print(f"  TRANSFORMERS_MODEL:  {settings.TRANSFORMERS_MODEL_NAME}")
print(f"  LOAD_IN_4BIT:        {settings.TRANSFORMERS_LOAD_IN_4BIT}")
print(f"  EMBEDDING_BACKEND:   {settings.EMBEDDING_BACKEND}")
print(f"  EMBEDDING_MODEL:     {settings.EMBEDDING_MODEL}")
print()

# 检查依赖
print("=" * 60)
print("依赖检查")
print("=" * 60)

try:
    import torch
    print(f"  torch:      {torch.__version__}")
    print(f"  CUDA:       {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"  GPU:        {torch.cuda.get_device_name(0)}")
        print(f"  VRAM:       {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
except ImportError:
    print("  torch:      未安装!")

try:
    import transformers
    print(f"  transformers: {transformers.__version__}")
except ImportError:
    print("  transformers: 未安装!")

try:
    import bitsandbytes
    print(f"  bitsandbytes: {bitsandbytes.__version__}")
except ImportError:
    print("  bitsandbytes: 未安装!")

try:
    import accelerate
    print(f"  accelerate:   {accelerate.__version__}")
except ImportError:
    print("  accelerate:   未安装!")

print()

# 尝试加载 tokenizer（轻量级，不加载模型权重）
print("=" * 60)
print("Tokenizer 加载测试")
print("=" * 60)
try:
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        settings.TRANSFORMERS_MODEL_NAME,
        trust_remote_code=True,
    )
    print(f"  Tokenizer:  加载成功")
    print(f"  Vocab size: {len(tokenizer)}")
    # 测试编码
    test_text = "量化交易"
    tokens = tokenizer.encode(test_text)
    print(f"  测试编码:   '{test_text}' -> {len(tokens)} tokens")
except Exception as e:
    print(f"  Tokenizer:  加载失败: {e}")
    sys.exit(1)

print()

# 尝试完整加载模型（耗时较长）
print("=" * 60)
print("模型加载测试（4-bit 量化）")
print("=" * 60)
print("  开始加载...（约需 1-3 分钟，37GB 模型文件）")
try:
    from transformers import AutoModelForCausalLM, BitsAndBytesConfig
    import torch

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
    )
    model = AutoModelForCausalLM.from_pretrained(
        settings.TRANSFORMERS_MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        dtype=torch.float16,
    )
    print(f"  模型:       加载成功")
    print(f"  设备映射:   {model.hf_device_map if hasattr(model, 'hf_device_map') else 'N/A'}")

    # 简单推理测试
    print()
    print("=" * 60)
    print("推理测试")
    print("=" * 60)
    prompt = "什么是量化交易？"
    messages = [{"role": "user", "content": prompt}]
    if hasattr(tokenizer, "apply_chat_template"):
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    else:
        text = f"User: {prompt}\nAssistant:"

    inputs = tokenizer(text, return_tensors="pt")
    if torch.cuda.is_available():
        inputs = {k: v.cuda() for k, v in inputs.items()}

    print(f"  提示: '{prompt}'")
    print("  生成中...")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=50,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    input_len = inputs["input_ids"].shape[1]
    response = tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True)
    print(f"  响应: {response.strip()}")
    print()
    print("=" * 60)
    print("[OK] LLM 接入验证全部通过")
    print("=" * 60)

except Exception as e:
    print(f"  模型加载失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
