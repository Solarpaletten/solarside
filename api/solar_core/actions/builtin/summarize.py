"""Summarize action."""
import time

from solar_core.actions.base import ActionContext, ActionResult, BaseAction
from solar_core.ai.prompts.builtin import SUMMARIZE_SYSTEM, SUMMARIZE_USER


class SummarizeAction(BaseAction):
    """Produce a tight summary of text in the requested language."""

    name = "summarize"
    description = "Summarize text in 2-4 sentences in the target language."

    async def execute(self, ctx: ActionContext) -> ActionResult:
        start = time.perf_counter()
        prompt = SUMMARIZE_USER.format(
            url=ctx.url or "(no URL)",
            language=ctx.language,
            text=ctx.text,
        )
        completion = await self.ai.complete_text(
            prompt=prompt,
            system=SUMMARIZE_SYSTEM,
            task="summarization",
            max_tokens=512,
            temperature=0.3,
        )
        elapsed = int((time.perf_counter() - start) * 1000)

        return ActionResult(
            success=True,
            data={
                "summary": completion.text.strip(),
                "language": ctx.language,
            },
            provider=completion.provider,
            model=completion.model,
            duration_ms=elapsed,
        )
