import math

import torch
import torchaudio
from transformers.models.dac import DacModel


class DACAutoencoder:
    def __init__(self, dac_model_folder: str | None = None):
        super().__init__()
        self.dac = DacModel.from_pretrained(dac_model_folder) if dac_model_folder else DacModel.from_pretrained("descript/dac_44khz")
        self.dac.eval().requires_grad_(False)
        self.codebook_size = self.dac.config.codebook_size
        self.num_codebooks = self.dac.quantizer.n_codebooks
        self.sampling_rate = self.dac.config.sampling_rate

    def preprocess(self, wav: torch.Tensor, sr: int) -> torch.Tensor:
        wav = torchaudio.functional.resample(wav, sr, 44_100)
        right_pad = math.ceil(wav.shape[-1] / 512) * 512 - wav.shape[-1]
        return torch.nn.functional.pad(wav, (0, right_pad))

    def encode(self, wav: torch.Tensor) -> torch.Tensor:
        return self.dac.encode(wav).audio_codes

    def decode(self, codes: torch.Tensor) -> torch.Tensor:
        with torch.autocast(self.dac.device.type, torch.float16, enabled=self.dac.device.type != "cpu"):
            return self.dac.decode(audio_codes=codes).audio_values.unsqueeze(1).float()
