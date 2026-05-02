"""Extract structured entities from text."""
import time

from solar_core.actions.base import ActionContext, ActionResult, BaseAction
from solar_core.ai.prompts.builtin import EXTRACT_SYSTEM, EXTRACT_USER


class ExtractAction(BaseAction):
    """Extract structured entities (people, orgs, dates, amounts, ...) into JSON."""

    name = "extract"
    description = "Extract structured entities from text into JSON."

    async def execute(self, ctx: ActionContext) -> ActionResult:
        start = time.perf_counter()
        prompt = EXTRACT_USER.format(
            url=ctx.url or "(no URL)",
            text=ctx.text,
        )
        completion = await self.ai.complete_text(
            prompt=prompt,
            system=EXTRACT_SYSTEM,
            task="extraction",
            max_tokens=1024,
            temperature=0.0,
        )
        elapsed = int((time.perf_counter() - start) * 1000)
        parsed = self._parse_json_response(completion.text)

        return ActionResult(
            success="parse_error" not in parsed,
            data=parsed,
            provider=completion.provider,
            model=completion.model,
            duration_ms=elapsed,
        )
