import numpy as np


def pilot_indices(n_subcarriers, pilot_spacing):
    return np.arange(0, n_subcarriers, pilot_spacing, dtype=int)


def data_indices(n_subcarriers, pilot_idx):
    mask = np.ones(n_subcarriers, dtype=bool)
    mask[pilot_idx] = False
    return np.nonzero(mask)[0]


def serial_to_parallel(symbols, n_rows):
    return np.asarray(symbols).reshape(n_rows, -1)


def parallel_to_serial(matrix):
    return np.asarray(matrix).reshape(-1)


def map_to_subcarriers(data_matrix, n_subcarriers, pilot_idx, pilot_symbol):
    frame = np.zeros((data_matrix.shape[0], n_subcarriers), dtype=complex)
    data_idx = data_indices(n_subcarriers, pilot_idx)
    frame[:, data_idx] = data_matrix
    frame[:, pilot_idx] = pilot_symbol
    return frame


def ofdm_ifft(freq_symbols):
    return np.fft.ifft(freq_symbols, axis=1)


def add_cyclic_prefix(time_symbols, cp_len):
    return np.concatenate((time_symbols[:, -cp_len:], time_symbols), axis=1)


def remove_cyclic_prefix(rx_with_cp, cp_len, n_subcarriers):
    return rx_with_cp[:, cp_len : cp_len + n_subcarriers]


def ofdm_fft(time_symbols):
    return np.fft.fft(time_symbols, axis=1)


def channel_frequency_response(taps, n_subcarriers):
    return np.fft.fft(taps, n_subcarriers)


def estimate_channel_from_pilots(rx_freq, pilot_idx, pilot_symbol):
    pilot_est = rx_freq[:, pilot_idx] / pilot_symbol
    n_subcarriers = rx_freq.shape[1]
    grid = np.arange(n_subcarriers)
    estimates = np.empty_like(rx_freq)
    for row in range(rx_freq.shape[0]):
        real = np.interp(grid, pilot_idx, np.real(pilot_est[row]))
        imag = np.interp(grid, pilot_idx, np.imag(pilot_est[row]))
        estimates[row] = real + 1j * imag
    return estimates


def equalize(rx_freq, channel_estimate):
    eps = 1e-12
    return rx_freq / np.where(np.abs(channel_estimate) < eps, eps, channel_estimate)

