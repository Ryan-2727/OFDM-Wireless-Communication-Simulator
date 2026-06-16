import numpy as np


def awgn(signal, snr_db, rng):
    signal = np.asarray(signal)
    snr_linear = 10 ** (snr_db / 10.0)
    signal_power = np.mean(np.abs(signal) ** 2)
    noise_power = signal_power / snr_linear
    noise = (
        rng.standard_normal(signal.shape) + 1j * rng.standard_normal(signal.shape)
    ) * np.sqrt(noise_power / 2.0)
    return signal + noise


def rayleigh_channel(num_taps, rng):
    taps = rng.standard_normal(num_taps) + 1j * rng.standard_normal(num_taps)
    taps /= np.sqrt(2.0 * num_taps)
    return taps


def apply_multipath(signal, taps):
    return np.convolve(signal, taps, mode="full")

