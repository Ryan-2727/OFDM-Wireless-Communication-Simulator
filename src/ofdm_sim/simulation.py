from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .channel import apply_multipath, awgn, rayleigh_channel
from .metrics import bit_error_rate
from .modulation import bits_per_symbol, demodulate, modulate
from .ofdm import (
    add_cyclic_prefix,
    channel_frequency_response,
    data_indices,
    equalize,
    estimate_channel_from_pilots,
    map_to_subcarriers,
    ofdm_fft,
    ofdm_ifft,
    pilot_indices,
    remove_cyclic_prefix,
    serial_to_parallel,
)
from .plots import (
    plot_ber_curves,
    plot_block_diagram,
    plot_constellation,
    plot_time_waveform,
)


@dataclass(frozen=True)
class OFDMConfig:
    n_subcarriers: int = 64
    cp_len: int = 16
    pilot_spacing: int = 4
    pilot_symbol: complex = 1 + 1j
    num_symbols: int = 400
    channel_taps: int = 6
    seed: int = 7

    @property
    def pilot_idx(self):
        return pilot_indices(self.n_subcarriers, self.pilot_spacing)

    @property
    def data_idx(self):
        return data_indices(self.n_subcarriers, self.pilot_idx)


def _build_tx_frame(modulation, config, rng):
    bps = bits_per_symbol(modulation)
    bits = rng.integers(
        0,
        2,
        size=config.num_symbols * config.data_idx.size * bps,
        dtype=np.uint8,
    )
    symbols = modulate(bits, modulation)
    data_matrix = serial_to_parallel(symbols, config.num_symbols)
    freq_frame = map_to_subcarriers(
        data_matrix, config.n_subcarriers, config.pilot_idx, config.pilot_symbol
    )
    time_frame = ofdm_ifft(freq_frame)
    tx_with_cp = add_cyclic_prefix(time_frame, config.cp_len)
    return bits, freq_frame, tx_with_cp


def simulate_awgn(modulation, snr_db, config):
    rng = np.random.default_rng(config.seed + int(snr_db) + bits_per_symbol(modulation))
    tx_bits, freq_frame, tx_with_cp = _build_tx_frame(modulation, config, rng)
    rx_with_cp = awgn(tx_with_cp, snr_db, rng)
    rx_no_cp = remove_cyclic_prefix(rx_with_cp, config.cp_len, config.n_subcarriers)
    rx_freq = ofdm_fft(rx_no_cp)
    rx_data = rx_freq[:, config.data_idx]
    rx_bits = demodulate(rx_data.reshape(-1), modulation)
    ber = bit_error_rate(tx_bits, rx_bits)
    return {
        "ber": ber,
        "tx_time": tx_with_cp.reshape(-1),
        "rx_constellation": rx_data.reshape(-1),
        "channel_estimate": np.ones_like(freq_frame),
    }


def simulate_rayleigh(modulation, snr_db, config, cp_len=None):
    use_cp = config.cp_len if cp_len is None else cp_len
    rng = np.random.default_rng(
        config.seed + 1000 + int(snr_db) + use_cp * 3 + bits_per_symbol(modulation)
    )
    tx_bits, _, tx_with_cp = _build_tx_frame(modulation, config, rng)
    taps = rayleigh_channel(config.channel_taps, rng)
    rx_blocks = []
    for symbol in tx_with_cp:
        faded = apply_multipath(symbol, taps)
        noisy = awgn(faded, snr_db, rng)
        rx_blocks.append(noisy[: use_cp + config.n_subcarriers])
    rx_blocks = np.asarray(rx_blocks)
    rx_no_cp = remove_cyclic_prefix(rx_blocks, use_cp, config.n_subcarriers)
    rx_freq = ofdm_fft(rx_no_cp)
    est = estimate_channel_from_pilots(rx_freq, config.pilot_idx, config.pilot_symbol)
    eq = equalize(rx_freq, est)
    rx_data = eq[:, config.data_idx]
    rx_bits = demodulate(rx_data.reshape(-1), modulation)
    ber = bit_error_rate(tx_bits, rx_bits)
    return {
        "ber": ber,
        "tx_time": tx_with_cp.reshape(-1),
        "rx_constellation": rx_data.reshape(-1),
        "channel_taps": taps,
        "channel_response": channel_frequency_response(taps, config.n_subcarriers),
        "channel_estimate": np.mean(est, axis=0),
    }


def sweep_ber(modulation, snr_values, config, channel_kind, cp_len=None):
    ber = []
    simulator = simulate_awgn if channel_kind == "awgn" else simulate_rayleigh
    for snr_db in snr_values:
        result = simulator(modulation, snr_db, config, cp_len) if simulator is simulate_rayleigh else simulator(modulation, snr_db, config)
        ber.append(result["ber"])
    return np.asarray(ber)


def generate_report_assets(output_dir):
    output_dir = Path(output_dir)
    fig_dir = output_dir / "figures"
    config = OFDMConfig()
    snr_values = np.arange(0, 21, 2)

    awgn_qpsk = sweep_ber("QPSK", snr_values, config, "awgn")
    awgn_16qam = sweep_ber("16QAM", snr_values, config, "awgn")
    rayleigh_qpsk = sweep_ber("QPSK", snr_values, config, "rayleigh")
    cp_short = sweep_ber("QPSK", snr_values, config, "rayleigh", cp_len=8)
    cp_long = sweep_ber("QPSK", snr_values, config, "rayleigh", cp_len=16)

    reference = simulate_rayleigh("16QAM", 18, config)

    plot_block_diagram(fig_dir / "ofdm_block_diagram.png")
    plot_block_diagram(fig_dir / "ofdm_block_diagram.svg")
    plot_time_waveform(reference["tx_time"], fig_dir / "tx_time_waveform.png")
    plot_time_waveform(reference["tx_time"], fig_dir / "tx_time_waveform.svg")
    plot_constellation(
        reference["rx_constellation"][:400],
        fig_dir / "rx_constellation.png",
        "Received Constellation (16QAM, Rayleigh, 18 dB)",
    )
    plot_constellation(
        reference["rx_constellation"][:400],
        fig_dir / "rx_constellation.svg",
        "Received Constellation (16QAM, Rayleigh, 18 dB)",
    )
    plot_ber_curves(
        [
            ("QPSK AWGN", snr_values, awgn_qpsk),
            ("QPSK Rayleigh + EQ", snr_values, rayleigh_qpsk),
        ],
        fig_dir / "ber_snr_curve.png",
        "BER vs SNR",
    )
    plot_ber_curves(
        [
            ("QPSK AWGN", snr_values, awgn_qpsk),
            ("QPSK Rayleigh + EQ", snr_values, rayleigh_qpsk),
        ],
        fig_dir / "ber_snr_curve.svg",
        "BER vs SNR",
    )
    plot_ber_curves(
        [
            ("QPSK AWGN", snr_values, awgn_qpsk),
            ("16QAM AWGN", snr_values, awgn_16qam),
            ("QPSK Rayleigh + EQ", snr_values, rayleigh_qpsk),
        ],
        fig_dir / "modulation_comparison.png",
        "Modulation and Channel Comparison",
    )
    plot_ber_curves(
        [
            ("QPSK AWGN", snr_values, awgn_qpsk),
            ("16QAM AWGN", snr_values, awgn_16qam),
            ("QPSK Rayleigh + EQ", snr_values, rayleigh_qpsk),
        ],
        fig_dir / "modulation_comparison.svg",
        "Modulation and Channel Comparison",
    )
    plot_ber_curves(
        [
            ("CP = 8", snr_values, cp_short),
            ("CP = 16", snr_values, cp_long),
        ],
        fig_dir / "cp_length_impact.png",
        "Impact of Cyclic Prefix Length",
    )
    plot_ber_curves(
        [
            ("CP = 8", snr_values, cp_short),
            ("CP = 16", snr_values, cp_long),
        ],
        fig_dir / "cp_length_impact.svg",
        "Impact of Cyclic Prefix Length",
    )

    return {
        "snr_db": snr_values,
        "awgn_qpsk": awgn_qpsk,
        "awgn_16qam": awgn_16qam,
        "rayleigh_qpsk": rayleigh_qpsk,
        "cp_short": cp_short,
        "cp_long": cp_long,
        "channel_taps": reference["channel_taps"],
        "channel_response": reference["channel_response"],
        "channel_estimate": reference["channel_estimate"],
    }
