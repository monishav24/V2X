"""
SmartV2X-CP Ultra — Hybrid LSTM + GRU Trajectory Prediction Model
==================================================================
PyTorch model definition for predicting vehicle trajectory
over the next 3–5 seconds from a rolling window of state history.

Architecture
------------
Input → LSTM encoder → GRU decoder → FC output layer → trajectory

Input shape  : (batch, seq_len, input_size=4)   [x, y, vx, vy]
Output shape : (batch, pred_horizon, 2)          [x, y] per step
"""

import torch
import torch.nn as nn
from typing import Optional


class LSTMGRUPredictor(nn.Module):
    """Hybrid LSTM encoder → GRU decoder for trajectory prediction."""

    def __init__(
        self,
        input_size: int = 4,
        hidden_size: int = 128,
        num_layers: int = 2,
        pred_horizon: int = 50,      # 5 s at 10 Hz
        output_size: int = 2,        # (x, y)
        dropout: float = 0.2,
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.pred_horizon = pred_horizon

        # ── Encoder: LSTM ─────────────────────────────────
        self.lstm_encoder = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
        )

        # ── Decoder: GRU ─────────────────────────────────
        self.gru_decoder = nn.GRU(
            input_size=hidden_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
        )

        # ── Output projection ────────────────────────────
        self.fc_out = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, output_size),
        )

        # ── Bridge: LSTM hidden → GRU hidden ─────────────
        self.bridge = nn.Linear(hidden_size, hidden_size)

    def forward(
        self,
        x: torch.Tensor,
        pred_len: Optional[int] = None,
    ) -> torch.Tensor:
        """
        Forward pass.

        Parameters
        ----------
        x : (batch, seq_len, input_size)
        pred_len : override default prediction horizon

        Returns
        -------
        trajectory : (batch, pred_len, 2)
        """
        pred_len = pred_len or self.pred_horizon
        batch_size = x.size(0)

        # Encode
        _, (h_n, c_n) = self.lstm_encoder(x)            # h_n: (layers, batch, H)

        # Bridge LSTM hidden → GRU initial hidden
        h_gru = torch.tanh(self.bridge(h_n))            # (layers, batch, H)

        # Decode — auto-regressively feed encoder last output
        decoder_input = h_n[-1].unsqueeze(1)             # (batch, 1, H)
        outputs = []
        h_dec = h_gru
        for _ in range(pred_len):
            out, h_dec = self.gru_decoder(decoder_input, h_dec)
            pred = self.fc_out(out.squeeze(1))            # (batch, 2)
            outputs.append(pred)
            decoder_input = out                           # feed back

        trajectory = torch.stack(outputs, dim=1)          # (batch, pred_len, 2)
        return trajectory
