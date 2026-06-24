"""本地 LLM 服务 — 支持多后端推理.

部署目标:
    - Apple Silicon: MLX 格式模型 (Qwen3-14B-MLX-4bit)
    - NVIDIA GPU: Transformers + 4-bit 量化 (Qwen3-8B)
    - 云端: OpenAI API

环境要求:
    - mlx 后端: macOS (Apple Silicon) + mlx-lm
    - transformers 后端: Windows/Linux + NVIDIA GPU + transformers + bitsandbytes
    - openai 后端: OPENAI_API_KEY 环境变量

使用方式:
    1. 设置 LLM_BACKEND 环境变量 (mlx | transformers | openai)
    2. 配置对应模型路径或名称
    3. 启动服务后调用 generate()

降级方案:
    - 模型未下载时自动使用 mock 响应
    - 可通过 OPENAI_API_KEY 切换到 OpenAI API
"""

import os
os.environ["HF_HUB_OFFLINE"] = "1"
import json
import asyncio
import concurrent.futures
import time
from typing import Any, AsyncIterator
from dataclasses import dataclass
from functools import lru_cache

from app.core.config import settings


@dataclass
class LLMResponse:
    """LLM 响应."""

    text: str
    model: str
    usage: dict[str, int] | None = None
    finish_reason: str | None = None


class LLMService:
    """LLM 服务统一接口."""

    # 全局锁，防止多协程同时访问 CUDA 模型
    _lock = asyncio.Lock()
    # 单线程 executor：所有 CUDA 推理都在同一个线程执行，避免上下文切换问题
    _executor = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="llm_cuda")

    def __init__(
        self,
        backend: str | None = None,
        model_path: str | None = None,
        model_name: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ):
        """初始化 LLM 服务.

        Args:
            backend: "mlx" | "transformers" | "openai" | "mock"
            model_path: 本地模型路径 (mlx 后端)
            model_name: HuggingFace 模型名称 (transformers 后端)
            max_tokens: 最大生成 token 数
            temperature: 采样温度
        """
        self.backend = backend or settings.LLM_BACKEND or os.getenv("LLM_BACKEND", "mock")
        self.model_path = model_path or settings.QWEN_MLX_MODEL_PATH or os.getenv("QWEN_MLX_MODEL_PATH", "")
        self.model_name = model_name or settings.TRANSFORMERS_MODEL_NAME or os.getenv("TRANSFORMERS_MODEL_NAME", "Qwen/Qwen3-8B")
        # Transformers + 消费级 GPU 生成较慢，限制 token 避免超时/阻塞
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout_seconds: float = float(os.getenv("LLM_GENERATE_TIMEOUT", "180"))

        self._model: Any = None
        self._tokenizer: Any = None
        self._is_loaded = False

    def _load_mlx_model(self) -> bool:
        """加载 MLX 模型.

        Returns:
            是否成功加载
        """
        if self._is_loaded:
            return True

        try:
            from mlx_lm import load, generate

            if not self.model_path or not os.path.exists(self.model_path):
                raise RuntimeError(
                    f"[LLM] 模型路径不存在: {self.model_path}. "
                    f"请设置 QWEN_MLX_MODEL_PATH 环境变量或下载模型"
                )

            print(f"[LLM] 正在加载 MLX 模型: {self.model_path}")
            self._model, self._tokenizer = load(self.model_path)
            self._is_loaded = True
            print("[LLM] MLX 模型加载完成")
            return True

        except ImportError:
            raise RuntimeError(
                "[LLM] mlx-lm 未安装. 请运行: pip install mlx-lm"
            )
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"[LLM] MLX 模型加载失败: {e}")

    def _load_transformers_model(self) -> bool:
        """加载 Transformers 模型 (支持 4-bit 量化, 适用于 NVIDIA GPU).

        Returns:
            是否成功加载
        """
        if self._is_loaded:
            return True

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

            print(f"[LLM] 正在加载 Transformers 模型: {self.model_name}", flush=True)
            print(
                f"[LLM] CUDA 可用: {torch.cuda.is_available()}, "
                f"设备: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}",
                flush=True,
            )

            # Windows WDDM 下清理显存并限制分配块大小，减少 TDR 风险
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "max_split_size_mb:512")

            # 4-bit 量化配置 (大幅降低显存占用, 8GB 显存可跑 8B 模型)
            if settings.TRANSFORMERS_LOAD_IN_4BIT:
                print("[LLM] 启用 4-bit 量化加载", flush=True)
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                )
                self._model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    quantization_config=bnb_config,
                    device_map="cuda:0",
                    trust_remote_code=True,
                    dtype=torch.float16,
                    local_files_only=True,
                    low_cpu_mem_usage=True,
                )
            else:
                self._model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    device_map="cuda:0",
                    trust_remote_code=True,
                    dtype=torch.float16,
                    local_files_only=True,
                    low_cpu_mem_usage=True,
                )

            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                local_files_only=True,
            )

            # 设置 pad_token
            if self._tokenizer.pad_token is None:
                self._tokenizer.pad_token = self._tokenizer.eos_token

            self._is_loaded = True
            print("[LLM] Transformers 模型加载完成", flush=True)

            # 预热 CUDA（避免 Windows WDDM 下的首次推理错误）
            if torch.cuda.is_available():
                try:
                    torch.cuda.synchronize()
                    dummy = torch.zeros(1, device="cuda")
                    _ = dummy + 1
                    torch.cuda.synchronize()
                    print("[LLM] CUDA 预热完成", flush=True)
                except Exception as warmup_err:
                    print(f"[LLM] CUDA 预热警告: {warmup_err}", flush=True)

            return True

        except ImportError as e:
            raise RuntimeError(
                f"[LLM] transformers 或 bitsandbytes 未安装. 请运行: pip install transformers bitsandbytes torch. 错误: {e}"
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"[LLM] Transformers 模型加载失败: {e}")

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        stream: bool = False,
    ) -> LLMResponse | AsyncIterator[str]:
        """生成文本.

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            max_tokens: 覆盖默认最大 token
            temperature: 覆盖默认温度
            stream: 是否流式输出

        Returns:
            LLMResponse 或 AsyncIterator[str] (stream=True 时)
        """
        if self.backend == "mlx":
            return self._generate_mlx(
                prompt, system_prompt, max_tokens, temperature, stream
            )
        elif self.backend == "transformers":
            return self._generate_transformers(
                prompt, system_prompt, max_tokens, temperature, stream
            )
        elif self.backend == "openai":
            return self._generate_openai(
                prompt, system_prompt, max_tokens, temperature, stream
            )
        elif self.backend == "mock":
            return self._generate_mock(prompt, system_prompt)
        else:
            raise ValueError(
                f"[LLM] 未知的backend: {self.backend}. "
                f"支持的backend: mlx, transformers, openai, mock(仅测试). "
            )

    async def generate_async(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        """异步生成文本.

        注意: transformers + CUDA 不支持并发访问，必须使用锁串行化。
        为了不阻塞 FastAPI 事件循环，推理放到单线程 executor 中执行。
        """
        print(f"[LLM] generate_async 开始, backend={self.backend}", flush=True)
        async with self._lock:
            print("[LLM] 已获取锁, 准备在线程池中执行生成", flush=True)
            loop = asyncio.get_running_loop()
            future = loop.run_in_executor(
                self._executor,
                self.generate,
                prompt,
                system_prompt,
                max_tokens,
                temperature,
                False,
            )
            try:
                result = await asyncio.wait_for(future, timeout=self.timeout_seconds)
            except asyncio.TimeoutError:
                print(f"[LLM] 生成超时 ({self.timeout_seconds}s)，取消任务", flush=True)
                future.cancel()
                raise RuntimeError(
                    f"[LLM] 模型生成超时（超过 {self.timeout_seconds} 秒）。"
                    "可能原因：提示词过长、GPU 显存不足或模型首次推理较慢。"
                    "请尝试减小 max_tokens、缩短提示词或检查 GPU 状态。"
                )
            print("[LLM] run_in_executor 返回", flush=True)
            return result

    def _generate_mlx(
        self,
        prompt: str,
        system_prompt: str | None,
        max_tokens: int | None,
        temperature: float | None,
        stream: bool,
    ) -> LLMResponse | AsyncIterator[str]:
        """MLX 模型生成."""
        if not self._load_mlx_model():
            raise RuntimeError("[LLM] MLX 模型加载失败，无法生成文本。生产环境严禁使用mock。")

        from mlx_lm import generate

        # 构建消息格式
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # 使用 tokenizer 应用聊天模板
        if self._tokenizer and hasattr(self._tokenizer, "apply_chat_template"):
            try:
                formatted_prompt = self._tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
                )
            except TypeError:
                formatted_prompt = self._tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
        else:
            # 回退到简单格式
            formatted_prompt = f"{system_prompt or ''}\n\nUser: {prompt}\n\nAssistant:"

        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature

        if stream:
            # 流式生成
            return self._stream_mlx(formatted_prompt, max_tokens, temperature)

        # 非流式生成
        response_text = generate(
            self._model,
            self._tokenizer,
            prompt=formatted_prompt,
            max_tokens=max_tokens,
            verbose=False,
        )

        return LLMResponse(
            text=response_text,
            model="Qwen3-14B-MLX-4bit",
            usage={"prompt_tokens": len(formatted_prompt), "completion_tokens": len(response_text)},
            finish_reason="stop",
        )

    async def _stream_mlx(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> AsyncIterator[str]:
        """MLX 流式生成."""
        # mlx-lm 目前不直接支持流式, 这里模拟
        response = self._generate_mlx(prompt, None, max_tokens, temperature, False)
        if isinstance(response, LLMResponse):
            # 模拟流式: 按字符 yield
            for char in response.text:
                yield char
                await asyncio.sleep(0.01)

    def _generate_transformers(
        self,
        prompt: str,
        system_prompt: str | None,
        max_tokens: int | None,
        temperature: float | None,
        stream: bool,
    ) -> LLMResponse | AsyncIterator[str]:
        """Transformers 模型生成 (NVIDIA GPU)."""
        if not self._load_transformers_model():
            raise RuntimeError("[LLM] Transformers 模型加载失败，无法生成文本。")

        import torch

        # 构建消息格式
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # 使用 tokenizer 应用聊天模板
        if hasattr(self._tokenizer, "apply_chat_template"):
            # Qwen3 支持 enable_thinking 参数，禁用思考过程可加速并减少token占用
            try:
                formatted_prompt = self._tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
                )
            except TypeError:
                # 旧版 tokenizer 不支持 enable_thinking
                formatted_prompt = self._tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
        else:
            formatted_prompt = f"{system_prompt or ''}\n\nUser: {prompt}\n\nAssistant:"

        # Tokenize
        inputs = self._tokenizer(formatted_prompt, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
            # 清理显存，降低 OOM/阻塞风险
            torch.cuda.empty_cache()

        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature
        # 消费级 GPU 默认限制生成长度，避免单条请求阻塞过久
        if self.backend == "transformers" and max_tokens > 256:
            max_tokens = 256
            print(f"[LLM] transformers 后端限制 max_new_tokens={max_tokens}", flush=True)

        if stream:
            return self._stream_transformers(inputs, max_tokens, temperature)

        # 非流式生成
        print("[LLM] 开始 model.generate()", flush=True)
        start_time = time.time()
        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                pad_token_id=self._tokenizer.pad_token_id,
                eos_token_id=self._tokenizer.eos_token_id,
            )
        elapsed = time.time() - start_time
        print(f"[LLM] model.generate() 完成, 耗时 {elapsed:.1f}s", flush=True)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # 解码 (只取新生成的部分)
        input_length = inputs["input_ids"].shape[1]
        generated_ids = outputs[0][input_length:]
        response_text = self._tokenizer.decode(generated_ids, skip_special_tokens=True)
        print(f"[LLM] 解码完成, 生成长度 {len(generated_ids)} tokens", flush=True)

        return LLMResponse(
            text=response_text,
            model=self.model_name,
            usage={
                "prompt_tokens": input_length,
                "completion_tokens": len(generated_ids),
            },
            finish_reason="stop",
        )

    async def _stream_transformers(
        self, inputs: dict, max_tokens: int, temperature: float
    ) -> AsyncIterator[str]:
        """Transformers 流式生成 (模拟)."""
        import torch

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                pad_token_id=self._tokenizer.pad_token_id,
                eos_token_id=self._tokenizer.eos_token_id,
            )

        input_length = inputs["input_ids"].shape[1]
        generated_ids = outputs[0][input_length:]
        response_text = self._tokenizer.decode(generated_ids, skip_special_tokens=True)

        # 模拟流式: 按字符 yield
        for char in response_text:
            yield char
            await asyncio.sleep(0.01)

    def _generate_openai(
        self,
        prompt: str,
        system_prompt: str | None,
        max_tokens: int | None,
        temperature: float | None,
        stream: bool,
    ) -> LLMResponse | AsyncIterator[str]:
        """OpenAI API 生成."""
        import openai

        api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 未设置")

        client = openai.OpenAI(api_key=api_key)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            max_tokens=max_tokens or self.max_tokens,
            temperature=temperature or self.temperature,
            stream=stream,
        )

        if stream:
            return self._stream_openai(response)

        return LLMResponse(
            text=response.choices[0].message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            },
            finish_reason=response.choices[0].finish_reason,
        )

    async def _stream_openai(self, response) -> AsyncIterator[str]:
        """OpenAI 流式生成."""
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _generate_mock(
        self, prompt: str, system_prompt: str | None
    ) -> LLMResponse:
        """Mock 生成 — 用于开发和测试.

        返回符合 RAG 审核预期的 JSON 格式文本，确保 _parse_review 能正确解析。
        """
        prompt_lower = prompt.lower()

        # 判断审核类型，返回对应的 JSON 格式响应
        if "资产配置" in prompt or "saa" in prompt_lower or "配置" in prompt:
            text = '{"passed": true, "issues": [], "adjustments": [], "theory_cited": ["theory_markowitz"], "cases_cited": ["alloc_moderate_recession"]}'
        elif "战术" in prompt or "taa" in prompt_lower or "行业" in prompt:
            text = '{"passed": true, "issues": [], "adjustments": [], "theory_cited": ["theory_black_litterman"]}'
        elif "绑定" in prompt or "binding" in prompt_lower or "回测" in prompt:
            text = '{"passed": true, "issues": [], "adjustments": [], "cases_cited": ["sb_momentum_trend"]}'
        elif "风控" in prompt or "risk" in prompt_lower or "止损" in prompt:
            text = '{"passed": true, "issues": [], "adjustments": [], "cases_cited": ["rc_moderate_balanced"]}'
        elif "可靠性" in prompt or "reliability" in prompt:
            text = '{"passed": true, "issues": [], "adjustments": []}'
        elif "最终" in prompt or "final" in prompt_lower or "综合" in prompt:
            text = '{"passed": true, "issues": [], "adjustments": []}'
        elif "论文" in prompt or "paper" in prompt_lower:
            text = "相关研究表明, 因子动量策略在A股市场具有显著超额收益 (Ma et al., 2024)。"
        else:
            # 默认返回通过
            text = '{"passed": true, "issues": [], "adjustments": []}'

        return LLMResponse(
            text=text,
            model="mock",
            usage={"prompt_tokens": len(prompt), "completion_tokens": len(text)},
            finish_reason="stop",
        )

    def is_available(self) -> bool:
        """检查 LLM 是否可用."""
        if self.backend == "mlx":
            return self._load_mlx_model()
        elif self.backend == "transformers":
            return self._load_transformers_model()
        elif self.backend == "openai":
            return (settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")) is not None
        return False  # 未知backend不可用

    def get_status(self) -> dict[str, Any]:
        """获取 LLM 状态信息."""
        return {
            "backend": self.backend,
            "model_path": self.model_path,
            "model_name": self.model_name,
            "is_loaded": self._is_loaded,
            "is_available": self.is_available(),
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }


@lru_cache()
def get_llm_service() -> LLMService:
    """获取全局 LLM 服务实例（单例）."""
    return LLMService()
