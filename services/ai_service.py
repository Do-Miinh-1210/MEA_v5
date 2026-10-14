"""
services/ai_service.py — Abstraction layer cho AI providers.
Đồng bộ V1 + V2: hỗ trợ key rotation thông minh, temperature/max_tokens theo model.
"""

from __future__ import annotations
import abc
import re as _re
import time as _time
from typing import Optional

from services.logger import get_logger as _get_log

from config import (
    MODEL_TEMPERATURE, DEFAULT_TEMPERATURE,
    MODEL_MAX_TOKENS, DEFAULT_MAX_TOKENS,
)


class AIService(abc.ABC):
    @abc.abstractmethod
    def generate(self, prompt: str) -> str: ...

    def generate_with_image(self, prompt: str, image_path: str) -> str:
        """Generate response from prompt + image (vision). Default: fallback to text-only."""
        return self.generate(prompt)

    @property
    @abc.abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abc.abstractmethod
    def model_name(self) -> str: ...


class GeminiService(AIService):
    def __init__(self, api_keys: list[str], model: str):
        if not api_keys or not api_keys[0]:
            raise ValueError("Cần ít nhất 1 Gemini API Key.")
        self._keys  = api_keys
        self._model = model
        self._client_cache: dict[str, object] = {}

    @property
    def provider_name(self) -> str: return "Google Gemini"

    @property
    def model_name(self) -> str: return self._model

    def generate(self, prompt: str) -> str:
        try:
            from google import genai as _genai
            from google.genai import types as _types
        except ImportError as exc:
            raise ImportError("Chưa cài google-genai\nChạy: pip install google-genai") from exc

        temperature = MODEL_TEMPERATURE.get(self._model, DEFAULT_TEMPERATURE)
        max_tokens  = MODEL_MAX_TOKENS.get(self._model, DEFAULT_MAX_TOKENS)
        last_err: Optional[Exception] = None

        for key in self._keys:
            try:
                if key not in self._client_cache:
                    self._client_cache[key] = _genai.Client(api_key=key)
                client   = self._client_cache[key]
                _t0 = _time.time()
                # Enable Google Search grounding for better accuracy
                tools = []
                try:
                    tools = [_types.Tool(google_search=_types.GoogleSearch())]
                except Exception:
                    pass  # Fallback: no grounding if not supported

                response = client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config=_types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                        tools=tools if tools else None,
                    ),
                )
                _get_log().response(model=self._model, ok=True,
                    latency_ms=int((_time.time()-_t0)*1000))
                return response.text
            except ImportError:
                raise
            except Exception as e:
                last_err = e
                _get_log().error(model=self._model, error=str(e)[:80])
                msg = str(e).lower()
                # Rotate key khi lỗi do key / quota — import constants từ
                # config để support chỉnh nhanh khi model mới dùng message khác.
                from config import (
                    AI_ERROR_KEYWORDS_INVALID_KEY,
                    AI_ERROR_KEYWORDS_SERVER,
                    AI_SERVER_ERROR_RETRY_DELAY,
                    AI_SERVER_SUGGESTED_RETRY_CAP,
                )
                if any(kw in msg for kw in AI_ERROR_KEYWORDS_INVALID_KEY):
                    continue
                # Retry on server errors (503/500) with configured delay
                if any(kw in msg for kw in AI_ERROR_KEYWORDS_SERVER):
                    _get_log().info(
                        f"Server error, retrying in {AI_SERVER_ERROR_RETRY_DELAY}s...")
                    _time.sleep(AI_SERVER_ERROR_RETRY_DELAY)
                    continue
                delay = _extract_retry_delay(e)
                if delay:
                    _get_log().info(
                        f"Server recommends retry in {delay:.0f}s")
                    _time.sleep(min(delay, AI_SERVER_SUGGESTED_RETRY_CAP))
                raise

        raise RuntimeError(
            f"Tất cả {len(self._keys)} key đều hết quota.\nLỗi cuối: {last_err}\n"
            f"💡 Thêm key mới trong tab Cài đặt → nhấn ➕ Thêm."
        )

    def generate_with_image(self, prompt: str, image_path: str | bytes) -> str:
        try:
            from google import genai as _genai
            from google.genai import types as _types
            from PIL import Image as _PILImage
            import io as _io
        except ImportError:
            return self.generate(prompt)

        temperature = MODEL_TEMPERATURE.get(self._model, DEFAULT_TEMPERATURE)
        max_tokens  = MODEL_MAX_TOKENS.get(self._model, DEFAULT_MAX_TOKENS)
        last_err: Optional[Exception] = None

        if isinstance(image_path, (bytes, bytearray)):
            img = _PILImage.open(_io.BytesIO(image_path))
        elif hasattr(image_path, "read"):
            img = _PILImage.open(image_path)
        else:
            img = _PILImage.open(image_path)

        for key in self._keys:
            try:
                if key not in self._client_cache:
                    self._client_cache[key] = _genai.Client(api_key=key)
                client = self._client_cache[key]
                _t0 = _time.time()
                response = client.models.generate_content(
                    model=self._model,
                    contents=[prompt, img],
                    config=_types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                    ),
                )
                _get_log().response(model=self._model, ok=True,
                    latency_ms=int((_time.time()-_t0)*1000))
                return response.text
            except ImportError:
                raise
            except Exception as e:
                last_err = e
                _get_log().error(model=self._model, error=str(e)[:80])
                msg = str(e).lower()
                if any(kw in msg for kw in ("quota", "429", "403", "invalid", "key", "rate")):
                    continue
                raise

        raise RuntimeError(f"Vision call failed: {last_err}")


class AnthropicService(AIService):
    def __init__(self, api_keys: list[str], model: str):
        if not api_keys or not api_keys[0]:
            raise ValueError("Cần ít nhất 1 Anthropic API Key.")
        self._keys  = api_keys
        self._model = model

    @property
    def provider_name(self) -> str: return "Anthropic Claude"

    @property
    def model_name(self) -> str: return self._model

    def generate(self, prompt: str) -> str:
        try:
            import anthropic as _anthropic
        except ImportError as exc:
            raise ImportError("Chưa cài anthropic\nChạy: pip install anthropic") from exc

        last_err: Optional[Exception] = None
        max_tokens = MODEL_MAX_TOKENS.get(self._model, DEFAULT_MAX_TOKENS)

        for key in self._keys:
            try:
                client = _anthropic.Anthropic(api_key=key)
                _t0 = _time.time()
                resp = client.messages.create(
                    model=self._model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                )
                _get_log().response(model=self._model, ok=True,
                    latency_ms=int((_time.time()-_t0)*1000))
                return resp.content[0].text
            except ImportError:
                raise
            except Exception as e:
                last_err = e
                _get_log().error(model=self._model, error=str(e)[:80])
                msg_str = str(e).lower()
                if any(kw in msg_str for kw in ("quota", "429", "403", "invalid", "key", "rate")):
                    continue
                delay = _extract_retry_delay(e)
                if delay:
                    _get_log().info(f"Server recommends retry in {delay:.0f}s")
                    _time.sleep(min(delay, 60))
                raise

        raise RuntimeError(
            f"Tất cả {len(self._keys)} key đều hết quota.\nLỗi cuối: {last_err}\n"
            f"💡 Thêm key mới trong tab Cài đặt → nhấn ➕ Thêm."
        )

    def generate_with_image(self, prompt: str, image_path: str | bytes) -> str:
        try:
            import anthropic as _anthropic
            import base64 as _b64
            from pathlib import Path as _P
        except ImportError:
            return self.generate(prompt)

        last_err: Optional[Exception] = None
        max_tokens = MODEL_MAX_TOKENS.get(self._model, DEFAULT_MAX_TOKENS)

        if isinstance(image_path, (bytes, bytearray)):
            img_data = _b64.standard_b64encode(image_path).decode()
            media_type = "image/png"
        else:
            img_data = _b64.standard_b64encode(_P(image_path).read_bytes()).decode()
            ext = _P(image_path).suffix.lower().lstrip(".")
            media_map = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "webp": "webp"}
            media_type = f"image/{media_map.get(ext, 'jpeg')}"

        for key in self._keys:
            try:
                client = _anthropic.Anthropic(api_key=key)
                _t0 = _time.time()
                resp = client.messages.create(
                    model=self._model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": img_data}},
                        {"type": "text", "text": prompt},
                    ]}],
                )
                _get_log().response(model=self._model, ok=True,
                    latency_ms=int((_time.time()-_t0)*1000))
                return resp.content[0].text
            except ImportError:
                raise
            except Exception as e:
                last_err = e
                _get_log().error(model=self._model, error=str(e)[:80])
                msg_str = str(e).lower()
                if any(kw in msg_str for kw in ("quota", "429", "403", "invalid", "key", "rate")):
                    continue
                raise

        raise RuntimeError(f"Vision call failed: {last_err}")


class OpenAICompatibleService(AIService):
    def __init__(self, provider_name: str, base_url: str, api_keys: list[str], model: str):
        if not api_keys or not api_keys[0]:
            if provider_name != "9Router":
                raise ValueError(f"Cần ít nhất 1 {provider_name} API Key.")
            api_keys = ["dummy_key_for_local"]
        self._provider_name = provider_name
        self._base_url = base_url
        self._keys  = api_keys
        self._model = model

    @property
    def provider_name(self) -> str: return self._provider_name

    @property
    def model_name(self) -> str: return self._model

    def generate(self, prompt: str) -> str:
        try:
            from openai import OpenAI as _OpenAI
        except ImportError as exc:
            raise ImportError("Chưa cài openai\nChạy: pip install openai") from exc

        temperature = MODEL_TEMPERATURE.get(self._model, DEFAULT_TEMPERATURE)
        max_tokens  = MODEL_MAX_TOKENS.get(self._model, DEFAULT_MAX_TOKENS)
        last_err: Optional[Exception] = None

        candidate_models = [self._model]
        if self._provider_name == "9Router":
            if not self._model.startswith("ag/"):
                candidate_models.append(f"ag/{self._model}")
            else:
                candidate_models.append(self._model.replace("ag/", "", 1))

        for key in self._keys:
            if not key:
                key = "dummy_key_for_local"
            for model_attempt in candidate_models:
                try:
                    _t0 = _time.time()
                    client = _OpenAI(api_key=key, base_url=self._base_url)
                    resp = client.chat.completions.create(
                        model=model_attempt,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    _get_log().response(model=model_attempt, ok=True,
                        latency_ms=int((_time.time()-_t0)*1000))
                    # Update current model if fallback worked
                    if model_attempt != self._model:
                        self._model = model_attempt
                    return resp.choices[0].message.content
                except ImportError:
                    raise
                except Exception as e:
                    last_err = e
                    _get_log().error(model=model_attempt, error=str(e)[:80])
                    msg = str(e).lower()
                    if "404" in msg and model_attempt != candidate_models[-1]:
                        # Thử tiếp candidate model (vd: thử ag/ prefix)
                        continue
                    if any(kw in msg for kw in ("quota", "429", "403", "invalid", "key", "rate")):
                        break  # Đổi sang key kế tiếp
                    delay = _extract_retry_delay(e)
                    if delay:
                        _get_log().info(f"Server recommends retry in {delay:.0f}s")
                        _time.sleep(min(delay, 60))
                        continue
                    raise

        raise RuntimeError(
            f"Tất cả {len(self._keys)} key đều lỗi hoặc hết quota.\nLỗi cuối: {last_err}\n"
            f"💡 Thêm key mới trong tab Cài đặt."
        )

    def generate_with_image(self, prompt: str, image_path: str | bytes) -> str:
        try:
            from openai import OpenAI as _OpenAI
            import base64 as _b64
            from pathlib import Path as _P
        except ImportError:
            return self.generate(prompt)

        last_err: Optional[Exception] = None
        temperature = MODEL_TEMPERATURE.get(self._model, DEFAULT_TEMPERATURE)
        max_tokens  = MODEL_MAX_TOKENS.get(self._model, DEFAULT_MAX_TOKENS)

        if isinstance(image_path, (bytes, bytearray)):
            img_data = _b64.standard_b64encode(image_path).decode()
            media_type = "image/png"
        else:
            img_data = _b64.standard_b64encode(_P(image_path).read_bytes()).decode()
            ext = _P(image_path).suffix.lower().lstrip(".")
            media_map = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "webp": "webp"}
            media_type = f"image/{media_map.get(ext, 'jpeg')}"

        candidate_models = [self._model]
        if self._provider_name == "9Router":
            if not self._model.startswith("ag/"):
                candidate_models.append(f"ag/{self._model}")
            else:
                candidate_models.append(self._model.replace("ag/", "", 1))

        for key in self._keys:
            if not key:
                key = "dummy_key_for_local"
            for model_attempt in candidate_models:
                try:
                    client = _OpenAI(api_key=key, base_url=self._base_url)
                    _t0 = _time.time()
                    resp = client.chat.completions.create(
                        model=model_attempt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:{media_type};base64,{img_data}"
                                        },
                                    },
                                ],
                            }
                        ],
                    )
                    _get_log().response(model=model_attempt, ok=True,
                        latency_ms=int((_time.time()-_t0)*1000))
                    if model_attempt != self._model:
                        self._model = model_attempt
                    return resp.choices[0].message.content
                except ImportError:
                    raise
                except Exception as e:
                    last_err = e
                    _get_log().error(model=model_attempt, error=str(e)[:80])
                    msg = str(e).lower()
                    if "404" in msg and model_attempt != candidate_models[-1]:
                        continue
                    if any(kw in msg for kw in ("quota", "429", "403", "invalid", "key", "rate")):
                        break
                    raise

        raise RuntimeError(f"Vision call failed: {last_err}")


def _extract_retry_delay(exc: Exception) -> float:
    """Read the server-recommended retry delay from a 429 error response."""
    msg = str(exc)
    m = _re.search(r'retry[^0-9]*(\d+(?:\.\d+)?)\s*s', msg, _re.IGNORECASE)
    if m:
        return float(m.group(1))
    return 0.0


def create_ai_service(provider: str, api_keys: list[str], model: str) -> AIService:
    if provider == "Google Gemini":
        svc = GeminiService(api_keys, model)
    elif provider == "Anthropic Claude":
        svc = AnthropicService(api_keys, model)
    elif provider == "DeepSeek":
        svc = OpenAICompatibleService("DeepSeek", "https://api.deepseek.com/v1", api_keys, model)
    elif provider == "OpenAI GPT":
        svc = OpenAICompatibleService("OpenAI GPT", "https://api.openai.com/v1", api_keys, model)
    elif provider == "9Router":
        from config import AI_PROVIDERS
        base_url = AI_PROVIDERS.get("9Router", {}).get("base_url", "http://localhost:20128/v1")
        svc = OpenAICompatibleService("9Router", base_url, api_keys, model)
    else:
        raise ValueError(f"Provider không hỗ trợ: {provider}")
    # Bọc instance vào logger — mỗi call generate/generate_with_image sẽ
    # tự động ghi 1 dòng vào ~/.exam_generator/ai_usage.jsonl.
    return _wrap_with_usage_log(svc)


def _wrap_with_usage_log(svc: AIService) -> AIService:
    """Monkey-patch instance methods to record AI usage. Best-effort —
    nếu logger lỗi thì vẫn trả về kết quả AI bình thường."""
    try:
        from services import ai_usage_log
    except Exception:
        return svc

    original_generate = svc.generate
    original_generate_with_image = svc.generate_with_image

    def _wrapped_generate(prompt: str) -> str:
        t0 = _time.monotonic()
        try:
            result = original_generate(prompt)
            ai_usage_log.record(
                provider=svc.provider_name, model=svc.model_name,
                kind="generate",
                prompt_chars=len(prompt or ""),
                response_chars=len(result or ""),
                duration_ms=int((_time.monotonic() - t0) * 1000),
                ok=True,
            )
            return result
        except Exception as e:
            ai_usage_log.record(
                provider=svc.provider_name, model=svc.model_name,
                kind="generate",
                prompt_chars=len(prompt or ""),
                response_chars=0,
                duration_ms=int((_time.monotonic() - t0) * 1000),
                ok=False, error=str(e),
            )
            raise

    def _wrapped_generate_with_image(prompt: str, image_path: str) -> str:
        t0 = _time.monotonic()
        try:
            result = original_generate_with_image(prompt, image_path)
            ai_usage_log.record(
                provider=svc.provider_name, model=svc.model_name,
                kind="generate_with_image",
                prompt_chars=len(prompt or ""),
                response_chars=len(result or ""),
                duration_ms=int((_time.monotonic() - t0) * 1000),
                ok=True,
            )
            return result
        except Exception as e:
            ai_usage_log.record(
                provider=svc.provider_name, model=svc.model_name,
                kind="generate_with_image",
                prompt_chars=len(prompt or ""),
                response_chars=0,
                duration_ms=int((_time.monotonic() - t0) * 1000),
                ok=False, error=str(e),
            )
            raise

    # Gắn __self__ để code phía UI (vd: ai_call.__self__ để lấy service object
    # cho vision call) vẫn hoạt động đúng như bound method gốc.
    _wrapped_generate.__self__ = svc                    # type: ignore[attr-defined]
    _wrapped_generate_with_image.__self__ = svc         # type: ignore[attr-defined]

    svc.generate = _wrapped_generate                       # type: ignore[method-assign]
    svc.generate_with_image = _wrapped_generate_with_image  # type: ignore[method-assign]
    return svc


def execute_vision_call(
    prompt: str,
    image_data: bytes | str,
    mime_type: str = "image/png",
    active_service: Optional[AIService] = None,
) -> tuple[str, str]:
    """Gọi AI Vision để phân tích hình ảnh và trả về kết quả kèm tên Provider/Model đã sử dụng.

    Hỗ trợ mọi Provider: Google Gemini, Anthropic Claude, OpenAI GPT, 9Router.
    Nếu provider hiện tại không hỗ trợ ảnh (ví dụ DeepSeek) hoặc gặp sự cố kết nối,
    hệ thống tự động tìm kiếm các khóa API có hỗ trợ Vision trong KeyManager để thay thế liền mạch.
    """
    from services.key_manager import get_key_manager
    km = get_key_manager()
    last_err: Optional[Exception] = None

    # 1. Thử active_service nếu có và không phải DeepSeek
    if active_service is not None and getattr(active_service, "provider_name", "") != "DeepSeek":
        try:
            res = active_service.generate_with_image(prompt, image_data)
            if res and res.strip():
                return res.strip(), f"{active_service.provider_name} ({active_service.model_name})"
        except Exception as e:
            last_err = e
            _get_log().warning("Active service %s vision failed: %s, attempting fallback...",
                               getattr(active_service, "provider_name", "unknown"), e)

    # 2. Thử các provider có Vision từ KeyManager
    # 2a. Google Gemini
    gemini_keys_raw = km.load("Google Gemini")
    if gemini_keys_raw:
        gemini_keys = [k.strip() for k in gemini_keys_raw.splitlines() if k.strip()]
        valid_gemini = [k for k in gemini_keys if k.startswith("AIza")]
        if valid_gemini:
            try:
                g_svc = create_ai_service("Google Gemini", valid_gemini, "gemini-2.5-flash")
                res = g_svc.generate_with_image(prompt, image_data)
                if res and res.strip():
                    return res.strip(), "Google Gemini (gemini-2.5-flash)"
            except Exception as e:
                last_err = e

    # 2b. OpenAI GPT
    openai_keys_raw = km.load("OpenAI GPT")
    if openai_keys_raw:
        openai_keys = [k.strip() for k in openai_keys_raw.splitlines() if k.strip()]
        if openai_keys:
            try:
                o_svc = create_ai_service("OpenAI GPT", openai_keys, "gpt-4o")
                res = o_svc.generate_with_image(prompt, image_data)
                if res and res.strip():
                    return res.strip(), "OpenAI GPT (gpt-4o)"
            except Exception as e:
                last_err = e

    # 2c. Anthropic Claude
    claude_keys_raw = km.load("Anthropic Claude")
    if claude_keys_raw:
        claude_keys = [k.strip() for k in claude_keys_raw.splitlines() if k.strip()]
        if claude_keys:
            try:
                c_svc = create_ai_service("Anthropic Claude", claude_keys, "claude-3-5-sonnet-20241022")
                res = c_svc.generate_with_image(prompt, image_data)
                if res and res.strip():
                    return res.strip(), "Anthropic Claude (claude-3-5-sonnet)"
            except Exception as e:
                last_err = e

    # 2d. 9Router
    router_keys_raw = km.load("9Router")
    if router_keys_raw:
        router_keys = [k.strip() for k in router_keys_raw.splitlines() if k.strip()]
        if router_keys:
            candidate_r_models = ["ag/gemini-3.8-flash", "ag/gemini-2.5-flash"]
            if active_service is not None and getattr(active_service, "model_name", ""):
                act_m = active_service.model_name
                if not act_m.startswith("ag/"):
                    act_m = f"ag/{act_m}"
                if act_m not in candidate_r_models:
                    candidate_r_models.insert(0, act_m)
            for r_model in candidate_r_models:
                try:
                    r_svc = create_ai_service("9Router", router_keys, r_model)
                    res = r_svc.generate_with_image(prompt, image_data)
                    if res and res.strip():
                        return res.strip(), f"9Router ({r_model})"
                except Exception as e:
                    last_err = e

    # 2e. Trường hợp đặc biệt: key lưu trong Gemini nhưng lại có dạng sk-... (9Router hoặc OpenAI key)
    if gemini_keys_raw and not valid_gemini:
        sk_keys = [k.strip() for k in gemini_keys_raw.splitlines() if k.strip().startswith("sk-")]
        if sk_keys:
            try:
                r_svc = create_ai_service("9Router", sk_keys, "ag/gemini-3.8-flash")
                res = r_svc.generate_with_image(prompt, image_data)
                if res and res.strip():
                    return res.strip(), "9Router (từ key sk-)"
            except Exception as e:
                last_err = e

            try:
                o_svc = create_ai_service("OpenAI GPT", sk_keys, "gpt-4o-mini")
                res = o_svc.generate_with_image(prompt, image_data)
                if res and res.strip():
                    return res.strip(), "OpenAI GPT (từ key sk-)"
            except Exception as e:
                last_err = e

    err_detail = f"\nChi tiết lỗi: {last_err}" if last_err else ""
    raise RuntimeError(
        "Không thể kết nối dịch vụ AI Vision để phân tích hình ảnh.\n\n"
        "💡 GIẢI PHÁP:\n"
        "  • Vào tab Cài đặt ⚙️ → Chọn 'Google Gemini' (miễn phí) và nhập API Key (bắt đầu bằng AIza...)\n"
        "  • Hoặc dùng OpenAI GPT (gpt-4o) / Anthropic Claude có hỗ trợ ảnh.\n"
        "  • Bạn cũng có thể dán trực tiếp Google Gemini API Key vào ô nhập nhanh của hộp thoại." + err_detail
    )

