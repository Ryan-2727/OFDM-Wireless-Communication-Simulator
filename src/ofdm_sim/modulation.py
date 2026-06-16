import numpy as np


QPSK_SCALE = np.sqrt(2.0)
QAM16_SCALE = np.sqrt(10.0)


def bits_per_symbol(modulation):
    if modulation == "QPSK":
        return 2
    if modulation == "16QAM":
        return 4
    raise ValueError(f"Unsupported modulation: {modulation}")


def modulate(bits, modulation):
    bits = np.asarray(bits, dtype=np.uint8)
    bps = bits_per_symbol(modulation)
    if bits.size % bps != 0:
        raise ValueError("Bit stream length must be divisible by bits per symbol.")
    groups = bits.reshape(-1, bps).astype(np.int16, copy=False)
    if modulation == "QPSK":
        i = 1 - 2 * groups[:, 0]
        q = 1 - 2 * groups[:, 1]
        return (i + 1j * q) / QPSK_SCALE
    if modulation == "16QAM":
        i_levels = 3 - 2 * (2 * groups[:, 0] + groups[:, 1])
        q_levels = 3 - 2 * (2 * groups[:, 2] + groups[:, 3])
        return (i_levels + 1j * q_levels) / QAM16_SCALE
    raise ValueError(f"Unsupported modulation: {modulation}")


def demodulate(symbols, modulation):
    symbols = np.asarray(symbols)
    if modulation == "QPSK":
        scaled = symbols * QPSK_SCALE
        bits_i = (np.real(scaled) < 0).astype(np.uint8)
        bits_q = (np.imag(scaled) < 0).astype(np.uint8)
        return np.column_stack((bits_i, bits_q)).reshape(-1)
    if modulation == "16QAM":
        scaled = symbols * QAM16_SCALE
        i = np.real(scaled)
        q = np.imag(scaled)
        bits_i_msb, bits_i_lsb = _demodulate_16qam_axis(i)
        bits_q_msb, bits_q_lsb = _demodulate_16qam_axis(q)
        return np.column_stack(
            (bits_i_msb, bits_i_lsb, bits_q_msb, bits_q_lsb)
        ).reshape(-1)
    raise ValueError(f"Unsupported modulation: {modulation}")


def _demodulate_16qam_axis(values):
    msb = np.zeros(values.shape, dtype=np.uint8)
    lsb = np.zeros(values.shape, dtype=np.uint8)

    inner_pos = (values >= 0) & (values < 2)
    inner_neg = (values < 0) & (values >= -2)
    outer_neg = values < -2

    lsb[inner_pos] = 1
    msb[inner_neg] = 1
    lsb[inner_neg] = 0
    msb[outer_neg] = 1
    lsb[outer_neg] = 1
    return msb, lsb
