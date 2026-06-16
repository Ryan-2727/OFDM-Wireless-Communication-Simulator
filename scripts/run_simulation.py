from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ofdm_sim.simulation import generate_report_assets


def main():
    results = generate_report_assets(ROOT / "results")
    print("Generated simulation outputs.")
    print("SNR(dB):", results["snr_db"].tolist())
    print("QPSK AWGN BER:", [float(v) for v in results["awgn_qpsk"]])
    print("16QAM AWGN BER:", [float(v) for v in results["awgn_16qam"]])
    print("QPSK Rayleigh BER:", [float(v) for v in results["rayleigh_qpsk"]])


if __name__ == "__main__":
    main()

