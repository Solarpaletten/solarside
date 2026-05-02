"""Translate action."""
import time

from solar_core.actions.base import ActionContext, ActionResult, BaseAction
from solar_core.ai.prompts.builtin import TRANSLATE_SYSTEM, TRANSLATE_USER


class TranslateAction(BaseAction):
    """High-fidelity translation to target language."""

    name = "translate"
    description = "Translate text to the target language preserving structure and entities."

    async def execute(self, ctx: ActionContext) -> ActionResult:
        start = time.perf_counter()
        prompt = TRANSLATE_USER.format(
            language=ctx.language,
            text=ctx.text,
        )
        completion = await self.ai.complete_text(
            prompt=prompt,
            system=TRANSLATE_SYSTEM,
            task="translation",
            max_tokens=2048,
            temperature=0.2,
        )
        elapsed = int((time.perf_counter() - start) * 1000)

        return ActionResult(
            success=True,
            data={
                "translation": completion.text.strip(),
                "target_language": ctx.language,
            },
            provider=completion.provider,
            model=completion.model,
            duration_ms=elapsed,
        )
