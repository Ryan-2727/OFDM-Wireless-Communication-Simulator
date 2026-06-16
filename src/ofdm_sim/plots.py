from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["svg.fonttype"] = "none"


def _finalize(fig, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_block_diagram(path):
    fig, ax = plt.subplots(figsize=(14, 2.8))
    ax.axis("off")
    labels = [
        "Bits",
        "QPSK/16QAM",
        "S/P",
        "Pilot Insert",
        "IFFT",
        "Add CP",
        "Channel",
        "Remove CP",
        "FFT",
        "Channel Est.",
        "Equalizer",
        "BER",
    ]
    xs = np.linspace(0.04, 0.96, len(labels))
    for x, label in zip(xs, labels):
        rect = plt.Rectangle((x - 0.035, 0.37), 0.07, 0.24, fill=False, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x, 0.49, label, ha="center", va="center", fontsize=9)
    for x0, x1 in zip(xs[:-1], xs[1:]):
        ax.annotate("", xy=(x1 - 0.04, 0.49), xytext=(x0 + 0.04, 0.49),
                    arrowprops=dict(arrowstyle="->", lw=1.2))
    _finalize(fig, path)


def plot_time_waveform(samples, path, count=200):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(np.real(samples[:count]), label="Real")
    ax.plot(np.imag(samples[:count]), label="Imag", alpha=0.8)
    ax.set_title("Transmit OFDM Time-Domain Waveform")
    ax.set_xlabel("Sample Index")
    ax.set_ylabel("Amplitude")
    ax.legend()
    _finalize(fig, path)


def plot_constellation(symbols, path, title):
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(np.real(symbols), np.imag(symbols), s=12, alpha=0.6)
    ax.set_title(title)
    ax.set_xlabel("In-Phase")
    ax.set_ylabel("Quadrature")
    ax.set_aspect("equal", adjustable="box")
    _finalize(fig, path)


def plot_ber_curves(curves, path, title):
    fig, ax = plt.subplots(figsize=(8, 5))
    for label, snr_db, ber in curves:
        ax.semilogy(snr_db, ber, marker="o", linewidth=1.8, label=label)
    ax.set_title(title)
    ax.set_xlabel("SNR (dB)")
    ax.set_ylabel("BER")
    ax.set_ylim(1e-4, 1.0)
    ax.legend()
    _finalize(fig, path)
