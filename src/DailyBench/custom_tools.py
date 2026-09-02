"""Custom mobilerun tools exposing ground-truth device date/time and approximate location"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict

from openai import AsyncOpenAI

from .pricing import ModelPricing, get_default_pricing

if TYPE_CHECKING:
    from mobilerun.agent.action_context import ActionContext

_LOCATION_RE = re.compile(r"last location=Location\[(\w+) ([\-\d.*]+),([\-\d.*]+)")

# Fixed for the whole harness - not exposed as a CLI flag, since every run uses the same
# simulated-user model. Override via the function's own `model=` kwarg in tests.
DEFAULT_ASK_USER_MODEL = "gpt-5.4-mini"

# Adapted from the AndroidWorld/MobileAgent-family "ask-user" simulated-user prompt. The
# original hardcoded "Today is 2025-10-16, Thursday" as a fixed snapshot; this asks for the
# device's own real `adb shell date` output instead, so the simulated user is never stale.
ASK_USER_SYSTEM_PROMPT_TEMPLATE = """You are acting as a mobile phone user. A mobile GUI agent is executing a task on your phone. The task goal is: {goal}

The relevant information for the task is: {relevant_information}

You need to answer questions from the mobile GUI agent about the task above. You can ONLY answer using the relevant information given and the task goal - do not make up any information under any circumstances. If the question is not related to the task, or no relevant information is available to answer it, refuse to answer in a polite manner and say so plainly.

The current real date and time is: {current_datetime}. If the question is about the date or time, answer using this real value rather than any date you might otherwise assume."""


# Multi-turn / KB persona prompt. Used when the task supplies a knowledge-base
# profile (--ask-user-kb) instead of a single hidden fact. The simulated user is
# an honest oracle over the profile: it answers whatever the agent asks, using
# only the profile + the task goal, and it REMEMBERS the whole conversation so
# follow-ups are consistent across turns ("I already told you - the Swiggy one").
ASK_USER_KB_SYSTEM_PROMPT_TEMPLATE = """You are acting as a mobile phone user. A mobile GUI agent is executing a task on your phone. The task goal is: {goal}

Here is everything about you that is relevant: {knowledge_base}

You must answer the mobile GUI agent's questions about the task. Rules:
- Answer ONLY from the knowledge base above and the task goal - never invent facts.
- Answer whatever is asked, honestly and directly. You are busy, so keep answers short (one sentence or a few words).
- If the question is about something not in your knowledge base, say plainly that you don't have that information.
- Remember everything already said in this conversation (the history below) and stay consistent with it. If the agent asks again about something you already answered, remind it of the earlier answer instead of repeating yourself at length.
- If the agent asks a question that is ambiguous, answer the most reasonable interpretation and note which one you assumed.

The current real date and time is: {current_datetime}.

Conversation so far (JSON, oldest first — "user" = the agent's question, "assistant" = your earlier answer):
{history}
The mobile GUI agent's latest question is below."""


_ask_user_phoenix_tracer: Any = None


def _get_ask_user_phoenix_tracer() -> Any | None:
    """Return a lazily-built OTel tracer that exports ask_user LLM spans to Phoenix.

    mobilerun's Phoenix integration only instruments LlamaIndex (the main agent's LLM).
    The ask_user tool calls the OpenAI SDK directly (AsyncOpenAI), so without this its
    tokens never reach Phoenix. We emit a single OpenInference LLM span per ask_user call
    ourselves, scoped to just that call — deliberately NOT instrumenting the openai package
    globally, which would double-count the main agent (llama_index's OpenAILike also uses
    the openai SDK and is already captured by the LlamaIndex instrumentor). Returns None
    when Phoenix tracing is off or the OTel/OpenInference extras aren't installed.
    """
    global _ask_user_phoenix_tracer
    if _ask_user_phoenix_tracer is not None:
        return _ask_user_phoenix_tracer
    endpoint = os.environ.get("phoenix_url")
    if not endpoint:
        _ask_user_phoenix_tracer = False
        return None
    try:
        from opentelemetry import trace as otel_trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk import trace as trace_sdk
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor
        from openinference.semconv.resource import ResourceAttributes
    except ImportError:
        _ask_user_phoenix_tracer = False
        return None
    resource_attributes: dict[str, object] = {}
    project = os.environ.get("phoenix_project_name", "")
    if project.strip():
        resource_attributes[ResourceAttributes.PROJECT_NAME] = project
    provider = trace_sdk.TracerProvider(resource=Resource(attributes=resource_attributes))
    provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint + "/v1/traces")))
    _ask_user_phoenix_tracer = otel_trace.get_tracer("dailybench.ask_user", tracer_provider=provider)
    return _ask_user_phoenix_tracer


def _annotate_ask_user_span(
    span: Any,
    model: str,
    system_prompt: str,
    question: str,
    answer: str | None,
    response: Any,
) -> None:
    """Set OpenInference LLM span attributes so Phoenix counts the simulated user's tokens."""
    from openinference.semconv.trace import SpanAttributes

    span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "LLM")
    span.set_attribute(SpanAttributes.LLM_PROVIDER, "openai")
    span.set_attribute(SpanAttributes.LLM_MODEL_NAME, model)
    span.set_attribute(SpanAttributes.LLM_INVOCATION_PARAMETERS, json.dumps({"model": model}, sort_keys=True))
    span.set_attribute(
        SpanAttributes.LLM_INPUT_MESSAGES,
        json.dumps(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ]
        ),
    )
    span.set_attribute(SpanAttributes.LLM_OUTPUT_MESSAGES, json.dumps([{"role": "assistant", "content": answer or ""}]))
    usage = response.usage
    if usage is not None:
        if usage.prompt_tokens is not None:
            span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_PROMPT, usage.prompt_tokens)
        if usage.completion_tokens is not None:
            span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_COMPLETION, usage.completion_tokens)
        if usage.total_tokens is not None:
            span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_TOTAL, usage.total_tokens)


def _emit_ask_user_span(
    tracer: Any,
    model: str,
    system_prompt: str,
    question: str,
    answer: str | None,
    response: Any,
) -> None:
    """Best-effort: emit one OpenInference LLM span for an ask_user call. Never raises — a
    tracing hiccup (e.g. Phoenix briefly unreachable) must not break the simulated user's answer.
    """
    try:
        with tracer.start_as_current_span("ask_user.llm") as span:
            _annotate_ask_user_span(span, model, system_prompt, question, answer, response)
    except Exception:
        pass


async def get_current_datetime(*, ctx: "ActionContext") -> str:
    """Return the device's real current date and time."""
    return await ctx.driver.get_date()


async def get_current_location(*, ctx: "ActionContext") -> str:
    """Return the device's last known approximate location as latitude/longitude."""
    dump = await ctx.driver.device.shell("dumpsys location")
    match = _LOCATION_RE.search(dump)
    if not match:
        return "Failed: no location fix available on this device (location services may be off)."
    provider, lat, lon = match.groups()
    return f"Approximate location ({provider} provider): latitude {lat}, longitude {lon}"


def build_ask_user_tool(
    relevant_information: str = "",
    *,
    kb: dict | None = None,
    model: str = DEFAULT_ASK_USER_MODEL,
    api_key: str | None = None,
    base_url: str | None = None,
    log_path: Path | None = None,
    pricing: ModelPricing | None = None,
    temperature: float = 0.0,
    top_p: float = 0.95,
    seed: int = 42,
) -> Dict[str, Dict[str, Any]]:
    """Build a per-run `ask_user` custom tool.

    Two modes (backward compatible):

    1. Single-fact (legacy): ``relevant_information`` is the task's hidden
       ground-truth fact (Hard/ASK-USER tasks). The simulated user holds ONLY
       that fact and answers just what's asked. This is the pre-v2 behaviour.

    2. Knowledge-base / multi-turn: ``kb`` is a JSON profile (dict) of the
       user's data (orders, contacts, wishlists, preferences...). The simulated
       user is an honest oracle over the profile: it answers whatever the agent
       asks, from the profile only, and it keeps a ROLLING MEMORY of the whole
       conversation so follow-up questions are answered consistently across
       turns. This is the multi-turn mode: the agent's job is to ask the right
       clarifying questions to disambiguate a vague task and converge.

    Each call appends a JSONL entry (timing, tokens, cost, turn number) to
    ``log_path`` when set, so per-turn costs and turn counts are tracked. The
    client is built lazily on first call so non-ask-user tasks never require
    OPENAI_API_KEY.
    """
    client: AsyncOpenAI | None = None
    # Rolling conversation history for multi-turn (KB) mode. Each entry is
    # {"role": "user"|"assistant", "content": ...}. Persisted across calls so
    # the simulated user remembers earlier answers.
    history: list[dict[str, str]] = []
    turn_count: int = 0

    async def ask_user(question: str, *, ctx: "ActionContext") -> str:
        nonlocal client, history, turn_count
        if client is None:
            client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        current_datetime = await ctx.driver.get_date()
        turn_count += 1
        if kb is not None:
            history_str = json.dumps(history, ensure_ascii=False)
            system_prompt = ASK_USER_KB_SYSTEM_PROMPT_TEMPLATE.format(
                goal=ctx.shared_state.instruction,
                knowledge_base=json.dumps(kb, ensure_ascii=False, indent=2),
                current_datetime=current_datetime,
                history=history_str,
            )
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ]
        else:
            system_prompt = ASK_USER_SYSTEM_PROMPT_TEMPLATE.format(
                goal=ctx.shared_state.instruction,
                relevant_information=relevant_information or "(none provided for this task)",
                current_datetime=current_datetime,
            )
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ]
        start = time.monotonic()
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            seed=seed,
        )
        elapsed_ms = (time.monotonic() - start) * 1000.0
        content = response.choices[0].message.content
        # Rolling memory: only persist in KB/multi-turn mode so legacy
        # single-fact runs behave exactly as before.
        if kb is not None:
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": content or ""})
        tracer = _get_ask_user_phoenix_tracer()
        if tracer is not None:
            _emit_ask_user_span(tracer, model, system_prompt, question, content, response)
        if log_path is not None:
            _log_ask_user_call(
                log_path,
                model,
                question,
                content,
                response,
                elapsed_ms,
                pricing=pricing if pricing is not None else get_default_pricing(),
                turn_number=turn_count,
            )
        return content.strip() if content else "Failed: empty response from the simulated user."

    return {
        "ask_user": {
            "function": ask_user,
            "parameters": {
                "question": {
                    "type": "string",
                    "required": True,
                    "description": "The clarifying question to ask the user, in plain language.",
                },
            },
            "description": (
                "Ask the human user a clarifying question when the task needs a specific fact that is "
                "NOT available anywhere on the device (for example a particular contact's name, a date or "
                "time, a file, or an amount etc.). First search the device thoroughly for it — only if you genuinely "
                "cannot find or infer it should you ask. Use this INSTEAD of guessing or inventing the specific fact "
                "you think is missing to complete the task. Never ask about things you can look up yourself. "
                "You may ask multiple questions over multiple turns to "
                "disambiguate a vague request."
            ),
        }
    }


def _log_ask_user_call(
    log_path: Path,
    model: str,
    question: str,
    answer: str | None,
    response: Any,
    elapsed_ms: float,
    *,
    pricing: ModelPricing | None = None,
    turn_number: int | None = None,
) -> None:
    """Append one ask_user completion record to a JSONL log, matching the main proxy's format.

    Cost is recorded in USD. The dollar figure is never hardcoded: if the provider already
    returned ``usage.cost`` (some gateways do) that value wins; otherwise the per-1M-token rate
    is looked up at runtime from the provider's pricing catalog keyed by ``model`` (see
    ``DailyBench.pricing``). If the model has no published rate, ``cost`` is logged as ``None``
    with an explanatory ``cost_details`` rather than a fabricated number.
    """
    usage = response.usage
    prompt_tokens = usage.prompt_tokens if usage else None
    completion_tokens = usage.completion_tokens if usage else None
    total_tokens = usage.total_tokens if usage else None

    # Prefer a provider-returned dollar figure (e.g. OpenRouter gateways), else estimate.
    cost = float(usage.cost) if usage is not None and getattr(usage, "cost", None) is not None else None
    cost_details: dict[str, Any] | None = None
    if cost is None and prompt_tokens is not None and completion_tokens is not None:
        resolver = pricing if pricing is not None else get_default_pricing()
        price = resolver.lookup(model)
        if price is not None:
            cost = resolver.estimate_cost(model, prompt_tokens, completion_tokens)
            cost_details = {
                "source": "runtime_pricing_catalog",
                "prompt_per_1m": price.prompt_per_1m,
                "completion_per_1m": price.completion_per_1m,
            }
        else:
            cost_details = {"source": "runtime_pricing_catalog", "error": f"no published rate for model {model!r}"}

    entry = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "kind": "chat.completion",
        "source": "ask_user",
        "elapsed_ms": elapsed_ms,
        "request": {"model": model, "message_count": 2, "framework_prompt": question},
        "turn_number": turn_number,
        "response": answer or "",
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        },
        "cost": cost,
        "cost_details": cost_details,
        "id": response.id,
        "model": response.model,
        "finish_reason": response.choices[0].finish_reason if response.choices else None,
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


CUSTOM_TOOLS: Dict[str, Dict[str, Any]] = {
    "get_current_datetime": {
        "function": get_current_datetime,
        "parameters": {},
        "description": (
            "Get the device's real current date and time. Call this whenever a task references "
            "'today', 'this week', 'right now', or any other relative date/time - do not guess or "
            "infer the date from on-screen content alone."
        ),
    },
    "get_current_location": {
        "function": get_current_location,
        "parameters": {},
        "description": (
            "Get the device's last known approximate location as latitude/longitude. Call this for "
            "tasks that reference 'my current place' or 'nearby'."
        ),
    },
}
