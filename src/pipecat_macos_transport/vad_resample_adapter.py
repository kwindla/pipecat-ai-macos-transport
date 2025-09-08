from __future__ import annotations

"""
Resampling VAD adapter for Mac transport.

This adapter wraps a VADAnalyzer and ensures that, if the analyzer does not
support the transport's input sample rate (e.g., 48000 Hz), audio is
resampled to a supported rate (e.g., 16000 Hz) for VAD analysis only.

Pass-through audio remains at the transport rate elsewhere in the pipeline.
"""

import asyncio
from typing import Optional

from loguru import logger

from pipecat.audio.utils import create_stream_resampler
from pipecat.audio.vad.vad_analyzer import VADAnalyzer, VADParams, VADState


class ResamplingVADAdapter(VADAnalyzer):
    """Adapter that resamples audio for the underlying VAD if needed.

    - Attempts to configure the underlying VAD with the transport's sample rate.
    - If that fails (e.g., Silero requires 8/16 kHz), it configures the VAD at
      a target rate (default 16 kHz) and resamples incoming audio buffers only
      for VAD analysis.
    - Downstream audio frames are unchanged; only VAD input is resampled.
    """

    def __init__(self, underlying: VADAnalyzer, *, target_rate: int = 16000):
        # Initialize parent with underlying params for consistency; we do not
        # use the base class state machine here, delegating to the underlying
        # analyzer instead.
        super().__init__(sample_rate=None, params=underlying.params)
        self._underlying = underlying
        self._target_rate = target_rate
        self._transport_sr: int = 0
        self._resample_needed: bool = False
        self._resampler = create_stream_resampler()

    # Properties delegate to underlying so control frames report real values
    @property
    def params(self) -> VADParams:  # type: ignore[override]
        return self._underlying.params

    @property
    def sample_rate(self) -> int:  # type: ignore[override]
        # Report the underlying analyzer's configured sample rate.
        return self._underlying.sample_rate

    def set_sample_rate(self, sample_rate: int):  # type: ignore[override]
        """Try to set underlying VAD to transport SR, else fall back to target SR."""
        self._transport_sr = sample_rate
        try:
            # If the underlying analyzer supports this SR, use it directly.
            self._underlying.set_sample_rate(sample_rate)
            self._resample_needed = False
            logger.debug(
                f"VAD adapter using native SR {sample_rate} Hz (no resampling)."
            )
        except Exception as e:
            # Fallback to target rate (e.g., 16kHz for Silero)
            logger.debug(
                f"Underlying VAD rejected SR {sample_rate} Hz ({e}); using {self._target_rate} Hz with resampling."
            )
            self._underlying.set_sample_rate(self._target_rate)
            self._resample_needed = True

    def set_params(self, params: VADParams):  # type: ignore[override]
        # Forward updated params to the underlying analyzer
        self._underlying.set_params(params)

    def num_frames_required(self) -> int:  # type: ignore[override]
        # Delegate to underlying analyzer
        return self._underlying.num_frames_required()

    def voice_confidence(self, buffer) -> float:  # type: ignore[override]
        # Not used when we delegate analyze_audio; still delegate for completeness
        return self._underlying.voice_confidence(buffer)

    def _resample_sync(self, audio: bytes, in_rate: int, out_rate: int) -> bytes:
        """Synchronously resample audio using the stream resampler.

        This runs the async resampler in a private event loop within the
        executor thread used by BaseInputTransport.
        """
        try:
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(
                    self._resampler.resample(audio, in_rate, out_rate)
                )
            finally:
                try:
                    loop.close()
                except Exception:
                    pass
        except Exception as e:
            logger.exception(f"VAD adapter resample failed: {e}")
            # On failure, return original audio to avoid crashing
            return audio

    def analyze_audio(self, buffer) -> VADState:  # type: ignore[override]
        # Optionally resample to the underlying analyzer's configured rate
        if self._resample_needed and self._transport_sr and self._target_rate:
            buffer = self._resample_sync(buffer, self._transport_sr, self._target_rate)
        # Delegate state machine and confidence calculation to the underlying analyzer
        return self._underlying.analyze_audio(buffer)

