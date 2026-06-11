"""本地 LLM 服务 — Qwen3-14B-MLX-4bit.

部署目标:
    https://huggingface.co/Qwen/Qwen3-14B-MLX-4bit

环境要求:
    - macOS (Apple Silicon)
    - mlx-lm
    - 模型文件下载到本地

使用方式:
    1. 安装: pip install mlx-lm
    2. 下载模型: huggingface-cli download Qwen/Qwen3-14B-MLX-4bit
    3. 设置环境变量: QWEN_MLX_MODEL_PATH=/path/to/model
    4. 启动服务后调用 generate()

降级方案:
    - 模型未下载时自动使用 mock 响应
    - 可通过 OPENAI_API_KEY 切换到 OpenAI API
"""

import os
import json
import asyncio
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

    def __init__(
        self,
        backend: str | None = None,
        model_path: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ):
        """初始化 LLM 服务.

        Args:
            backend: "mlx" | "openai" | "mock"
            model_path: 本地模型路径 (mlx 后端)
            max_tokens: 最大生成 token 数
            temperature: 采样温度
        """
        self.backend = backend or settings.LLM_BACKEND or os.getenv("LLM_BACKEND", "mock")
        self.model_path = model_path or settings.QWEN_MLX_MODEL_PATH or os.getenv("QWEN_MLX_MODEL_PATH", "")
        self.max_tokens = max_tokens
        self.temperature = temperature

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
        elif self.backend == "openai":
            return self._generate_openai(
                prompt, system_prompt, max_tokens, temperature, stream
            )
        else:
            raise ValueError(
                f"[LLM] 未知的backend: {self.backend}. "
                f"支持的backend: mlx, openai. "
                f"生产环境严禁使用mock。"
            )

    async def generate_async(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        """异步生成文本."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.generate(prompt, system_prompt, max_tokens, temperature, False),
        )

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
        elif "可靠性" in prompt or "reliability" in prompt_lower:
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
        elif self.backend == "openai":
            return (settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")) is not None
        return False  # 未知backend不可用

    def get_status(self) -> dict[str, Any]:
        """获取 LLM 状态信息."""
        return {
            "backend": self.backend,
            "model_path": self.model_path,
            "is_loaded": self._is_loaded,
            "is_available": self.is_available(),
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }


@lru_cache()
def get_llm_service() -> LLMService:
    """获取全局 LLM 服务实例（单例）."""
    return LLMService()
