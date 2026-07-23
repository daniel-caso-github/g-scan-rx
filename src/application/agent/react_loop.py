import base64
import logging
from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from src.domain.entities.verified_record import VerifiedRecord

logger = logging.getLogger(__name__)

AsyncTool = Callable[..., Awaitable[Any]]


class AgentAbstainError(Exception):
    """Agent abstains because the image was identified as out-of-distribution."""


class _Action(StrEnum):
    DETECT = "detect_anomaly"
    EXTRACT = "vision_extract"
    VERIFY = "verify_prescription"
    FINISH = "finish"
    ABSTAIN = "abstain"


class AgentStep(BaseModel):
    action: str
    observation: dict


class _State(BaseModel):
    image_b64: str
    image_hash: str
    steps: list[AgentStep] = Field(default_factory=list)
    prescription_data: dict | None = None
    record_data: dict | None = None
    anomaly_checked: bool = False
    is_anomaly: bool = False


class ReActLoop:
    """Pure Python Reason-Act-Observe loop for processing a prescription.

    Tools injected as async callables; no infrastructure imports.
    The LangGraph version (Step 4) reuses these same tools via graph.py.
    """

    def __init__(
        self,
        vision_extract: AsyncTool,
        retrieve_drug: AsyncTool,
        verify_prescription: AsyncTool,
        detect_anomaly: AsyncTool | None = None,
        max_steps: int = 10,
    ) -> None:
        self._vision_extract = vision_extract
        self._retrieve_drug = retrieve_drug
        self._verify_prescription = verify_prescription
        self._detect_anomaly = detect_anomaly
        self._max_steps = max_steps

    async def execute(self, image_bytes: bytes, image_hash: str) -> VerifiedRecord:
        state = _State(
            image_b64=base64.b64encode(image_bytes).decode(),
            image_hash=image_hash,
        )

        for step_num in range(self._max_steps):
            action = self._reason(state)
            logger.debug("image_hash=%s paso=%d acción=%s", image_hash, step_num, action)

            if action == _Action.FINISH:
                break
            if action == _Action.ABSTAIN:
                raise AgentAbstainError(
                    f"Imagen {image_hash!r} rechazada: fuera de distribución"
                )

            observation = await self._act(action, state)
            self._observe(state, action, observation)
        else:
            logger.warning(
                "image_hash=%s: agente alcanzó max_steps=%d sin finalizar",
                image_hash,
                self._max_steps,
            )

        if state.record_data is None:
            raise RuntimeError(
                f"ReActLoop terminó sin VerifiedRecord para image_hash={image_hash!r}"
            )

        return VerifiedRecord.model_validate(state.record_data)

    @property
    def history(self) -> list[AgentStep]:
        return []

    def _reason(self, state: _State) -> _Action:
        if self._detect_anomaly is not None and not state.anomaly_checked:
            return _Action.DETECT
        if state.is_anomaly:
            return _Action.ABSTAIN
        if state.prescription_data is None:
            return _Action.EXTRACT
        if state.record_data is None:
            return _Action.VERIFY
        return _Action.FINISH

    async def _act(self, action: _Action, state: _State) -> dict:
        if action == _Action.DETECT:
            return await self._detect_anomaly(image_b64=state.image_b64)
        if action == _Action.EXTRACT:
            return await self._vision_extract(
                image_b64=state.image_b64,
                image_hash=state.image_hash,
            )
        if action == _Action.VERIFY:
            return await self._verify_prescription(prescription_data=state.prescription_data)
        raise ValueError(f"Acción no manejada en _act: {action}")

    def _observe(self, state: _State, action: _Action, observation: dict) -> None:
        state.steps.append(AgentStep(action=action, observation=observation))

        if action == _Action.DETECT:
            state.anomaly_checked = True
            state.is_anomaly = observation.get("is_anomaly", False)
        elif action == _Action.EXTRACT:
            state.prescription_data = observation
        elif action == _Action.VERIFY:
            state.record_data = observation
