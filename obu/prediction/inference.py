"""
SmartV2X-CP Ultra — Edge-Optimised Trajectory Inference
========================================================
Loads a pretrained LSTM+GRU model and runs inference in real-time.
Supports both standard PyTorch and ONNX Runtime backends.
"""

import os
import time
import logging
import numpy as np
from typing import Dict, Any, List, Optional
from collections import deque

logger = logging.getLogger(__name__)

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

from .model import LSTMGRUPredictor


class TrajectoryPredictor:
    """
    High-level wrapper for trajectory prediction.

    Maintains a rolling buffer of recent states and produces
    predicted waypoints for the next N seconds.
    """

    def __init__(self, config: Dict[str, Any]):
        self.model_path: str = config.get("model_path", "")
        self.seq_len: int = config.get("sequence_length", 20)
        self.pred_horizon: int = config.get("prediction_horizon_sec", 5) * 10  # 10 Hz
        self.hidden_size: int = config.get("hidden_size", 128)
        self.num_layers: int = config.get("num_layers", 2)
        self.use_onnx: bool = config.get("use_onnx", False)

        # Rolling state buffer: each entry is [x, y, vx, vy]
        self._buffer: deque = deque(maxlen=self.seq_len)

        self._model = None
        self._onnx_session = None
        self._device = "cpu"

        self._load_model()

    # ── Model loading ─────────────────────────────────────
    def _load_model(self):
        """Load the pretrained model (PyTorch or ONNX)."""
        if self.use_onnx and ONNX_AVAILABLE:
            onnx_path = self.model_path.replace(".pth", ".onnx")
            if os.path.exists(onnx_path):
                self._onnx_session = ort.InferenceSession(onnx_path)
                logger.info("ONNX model loaded: %s", onnx_path)
                return

        if TORCH_AVAILABLE:
            self._model = LSTMGRUPredictor(
                input_size=4,
                hidden_size=self.hidden_size,
                num_layers=self.num_layers,
                pred_horizon=self.pred_horizon,
            )
            if os.path.exists(self.model_path):
                state = torch.load(self.model_path, map_location="cpu")
                self._model.load_state_dict(state)
                logger.info("PyTorch model loaded: %s", self.model_path)
            else:
                logger.warning(
                    "Model file not found (%s) — using random weights (demo mode)",
                    self.model_path,
                )
            self._model.eval()
        else:
            logger.error("Neither PyTorch nor ONNX runtime available!")

    # ── Public API ────────────────────────────────────────
    def push_state(self, state: Dict[str, float]):
        """Add a new fused state to the rolling buffer."""
        self._buffer.append([
            state.get("x", 0.0),
            state.get("y", 0.0),
            state.get("vx", 0.0),
            state.get("vy", 0.0),
        ])

    def predict(self) -> Optional[List[Dict[str, float]]]:
        """
        Run trajectory prediction.

        Returns a list of predicted waypoints [{x, y}, …]
        or None if the buffer is not full yet.
        """
        if len(self._buffer) < self.seq_len:
            logger.debug(
                "Buffer not full (%d/%d) — skipping prediction",
                len(self._buffer), self.seq_len,
            )
            return None

        seq = np.array(list(self._buffer), dtype=np.float32)  # (seq, 4)
        start = time.time()

        if self._onnx_session is not None:
            trajectory = self._infer_onnx(seq)
        elif self._model is not None:
            trajectory = self._infer_torch(seq)
        else:
            return None

        elapsed_ms = (time.time() - start) * 1000
        logger.debug("Prediction latency: %.1f ms", elapsed_ms)
        return trajectory

    # ── Inference backends ────────────────────────────────
    def _infer_torch(self, seq: np.ndarray) -> List[Dict[str, float]]:
        inp = torch.tensor(seq).unsqueeze(0)  # (1, seq, 4)
        with torch.no_grad():
            out = self._model(inp)             # (1, pred_horizon, 2)
        points = out.squeeze(0).numpy()
        return [{"x": float(p[0]), "y": float(p[1])} for p in points]

    def _infer_onnx(self, seq: np.ndarray) -> List[Dict[str, float]]:
        inp = seq[np.newaxis, ...]              # (1, seq, 4)
        input_name = self._onnx_session.get_inputs()[0].name
        result = self._onnx_session.run(None, {input_name: inp})
        points = result[0].squeeze(0)
        return [{"x": float(p[0]), "y": float(p[1])} for p in points]

    # ── ONNX export utility ───────────────────────────────
    def export_onnx(self, output_path: str = "model.onnx"):
        """Export the loaded PyTorch model to ONNX format."""
        if not TORCH_AVAILABLE or self._model is None:
            logger.error("Cannot export — no PyTorch model loaded")
            return
        dummy = torch.randn(1, self.seq_len, 4)
        torch.onnx.export(
            self._model, dummy, output_path,
            input_names=["state_sequence"],
            output_names=["trajectory"],
            dynamic_axes={
                "state_sequence": {0: "batch"},
                "trajectory": {0: "batch"},
            },
        )
        logger.info("ONNX model exported to %s", output_path)
