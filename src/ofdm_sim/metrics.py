import numpy as np


def bit_error_rate(tx_bits, rx_bits):
    tx_bits = np.asarray(tx_bits, dtype=np.uint8)
    rx_bits = np.asarray(rx_bits, dtype=np.uint8)
    if tx_bits.shape != rx_bits.shape:
        raise ValueError("Bit arrays must share the same shape.")
    return np.mean(tx_bits != rx_bits)

