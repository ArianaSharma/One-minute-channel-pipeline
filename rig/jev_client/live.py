"""Live client: the official TypeSafe Python SDK (`typesafe-sdk`), used as documented.

  TypeSafeClient(api_key=..., model=..., timeout=...)   # docs: sdk/python/api/clients/sync
  client.system_one(state=..., questions=..., model=...) -> SystemOneResponse
  response.model, response.usage.input_tokens, response.request_id, response.answers
Errors are TypeSafeError subclasses. Only the class name and HTTP status are logged,
never the key (the SDK's own `endpoint` attribute also excludes credentials).
"""
from __future__ import annotations

import time

from rig.config import env
from rig.jev_client.base import JevResult, parse, token_cost


class LiveJevClient:
    mode = "live"

    def __init__(self, cfg: dict, transport=None):
        from typesafe_sdk import TypeSafeClient

        api_key = env("TYPESAFE_API_KEY")
        if not api_key:
            raise RuntimeError("JEV_MODE=live needs TYPESAFE_API_KEY in the environment (.env)")
        jev = cfg["jev"]
        self.model = jev["model"]
        self.price = jev["price_per_mtok_input_usd"]
        self._client = TypeSafeClient(
            api_key=api_key, model=self.model, timeout=jev.get("timeout_s", 10.0),
            transport=transport,
        )

    def ask(self, state: dict, questions: dict) -> JevResult:
        from typesafe_sdk import TypeSafeError

        start = time.perf_counter()
        try:
            resp = self._client.system_one(state=state, questions=questions, model=self.model)
        except TypeSafeError as exc:
            status = getattr(exc, "status", None)
            return JevResult(self.mode, self.model, None, (time.perf_counter() - start) * 1000,
                             error=f"{type(exc).__name__}" + (f" (HTTP {status})" if status else ""))
        latency = (time.perf_counter() - start) * 1000
        body = resp.model_dump(mode="json")
        usage = body.get("usage") or {}
        try:
            request_id = resp.request_id
        except Exception:  # header missing
            request_id = None
        result = JevResult(
            self.mode, body.get("model"), body.get("answers"), latency,
            input_tokens=usage.get("input_tokens"), output_tokens=usage.get("output_tokens"),
            cost_usd=token_cost(usage.get("input_tokens"), self.price), request_id=request_id,
        )
        try:
            result.parsed = parse(result.answers)
        except (KeyError, TypeError) as exc:
            result.error = f"unexpected answer shape: missing {exc}"
        return result

    def close(self) -> None:
        self._client.close()
