"""
SmartV2X-CP Ultra — Model Training Pipeline
==============================================
End-to-end training loop for the LSTM+GRU trajectory prediction
model with data loading, loss computation, and checkpointing.
"""

import os
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class ModelTrainer:
    """
    Training pipeline for the trajectory prediction model.

    Handles:
      • Dataset preparation from collected trajectory data
      • Training loop with validation
      • Checkpoint saving
      • Integration with ModelVersionManager
    """

    def __init__(self, config: Dict[str, Any]):
        self.epochs: int = config.get("epochs", 50)
        self.batch_size: int = config.get("batch_size", 32)
        self.learning_rate: float = config.get("learning_rate", 0.001)
        self.checkpoint_dir: str = config.get("checkpoint_dir", "models/checkpoints")
        self.device = "cpu"

        os.makedirs(self.checkpoint_dir, exist_ok=True)

        if TORCH_AVAILABLE and torch.cuda.is_available():
            self.device = "cuda"
        logger.info("Trainer initialised — device=%s, epochs=%d", self.device, self.epochs)

    def train(
        self,
        model,
        train_data: tuple,
        val_data: Optional[tuple] = None,
    ) -> Dict[str, Any]:
        """
        Run the full training loop.

        Parameters
        ----------
        model : nn.Module — the LSTM+GRU predictor
        train_data : (X_train, Y_train) numpy arrays
        val_data : optional (X_val, Y_val)

        Returns
        -------
        Training history dict with losses.
        """
        if not TORCH_AVAILABLE:
            logger.error("PyTorch not available — cannot train")
            return {"error": "PyTorch not installed"}

        model = model.to(self.device)
        optimizer = torch.optim.Adam(model.parameters(), lr=self.learning_rate)
        criterion = nn.MSELoss()

        X_train = torch.tensor(train_data[0], dtype=torch.float32)
        Y_train = torch.tensor(train_data[1], dtype=torch.float32)
        dataset = TensorDataset(X_train, Y_train)
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        history = {"train_loss": [], "val_loss": []}

        for epoch in range(1, self.epochs + 1):
            model.train()
            epoch_loss = 0.0

            for batch_x, batch_y in loader:
                batch_x = batch_x.to(self.device)
                batch_y = batch_y.to(self.device)

                optimizer.zero_grad()
                pred = model(batch_x, pred_len=batch_y.size(1))
                loss = criterion(pred, batch_y)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()

            avg_loss = epoch_loss / len(loader)
            history["train_loss"].append(avg_loss)

            # Validation
            val_loss = None
            if val_data is not None:
                val_loss = self._validate(model, val_data, criterion)
                history["val_loss"].append(val_loss)

            if epoch % 5 == 0 or epoch == 1:
                msg = f"Epoch {epoch}/{self.epochs} — train_loss={avg_loss:.6f}"
                if val_loss is not None:
                    msg += f" val_loss={val_loss:.6f}"
                logger.info(msg)

            # Checkpoint every 10 epochs
            if epoch % 10 == 0:
                path = os.path.join(self.checkpoint_dir, f"model_epoch_{epoch}.pth")
                torch.save(model.state_dict(), path)

        # Save final model
        final_path = os.path.join(self.checkpoint_dir, "model_final.pth")
        torch.save(model.state_dict(), final_path)
        logger.info("Training complete — final model saved to %s", final_path)

        return history

    def _validate(self, model, val_data, criterion) -> float:
        model.eval()
        X_val = torch.tensor(val_data[0], dtype=torch.float32).to(self.device)
        Y_val = torch.tensor(val_data[1], dtype=torch.float32).to(self.device)
        with torch.no_grad():
            pred = model(X_val, pred_len=Y_val.size(1))
            loss = criterion(pred, Y_val)
        return loss.item()
