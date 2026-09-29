"""Shared helpers: speaker embedding model and audio loading."""
import os

import numpy as np
import librosa

MODEL_SOURCE = "speechbrain/spkrec-ecapa-voxceleb"
MODEL_SAMPLE_RATE = 16000


def load_embedding_model(savedir: str = None):
    from speechbrain.inference.speaker import EncoderClassifier
    from speechbrain.utils.fetching import LocalStrategy

    savedir = savedir or os.path.join(os.path.dirname(__file__), ".model_cache")
    # SpeechBrain defaults to symlinking cached model files into savedir, which
    # requires elevated privileges / Developer Mode on Windows. Copy instead.
    return EncoderClassifier.from_hparams(
        source=MODEL_SOURCE, savedir=savedir, local_strategy=LocalStrategy.COPY
    )


def embed_waveform(classifier, waveform: np.ndarray, sample_rate: int) -> np.ndarray:
    """Embed a mono waveform (float32, any sample rate) into a 192-dim speaker vector."""
    import torch

    if waveform.ndim > 1:
        waveform = waveform.mean(axis=-1)
    waveform = waveform.astype(np.float32)

    if sample_rate != MODEL_SAMPLE_RATE:
        waveform = librosa.resample(waveform, orig_sr=sample_rate, target_sr=MODEL_SAMPLE_RATE)

    wav_tensor = torch.from_numpy(waveform).unsqueeze(0)  # (1, num_samples)
    with torch.no_grad():
        embedding = classifier.encode_batch(wav_tensor)
    return embedding.squeeze().cpu().numpy()


def embed_file(classifier, audio_path: str) -> np.ndarray:
    import soundfile as sf

    waveform, sample_rate = sf.read(audio_path, dtype="float32")
    return embed_waveform(classifier, waveform, sample_rate)
