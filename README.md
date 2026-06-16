# OFDM-Wireless-Communication-Simulator

[English README](README_EN.md)

基于 Python 的 OFDM 无线通信仿真项目，覆盖从基带比特生成到接收端均衡与误码率分析的完整链路，支持 QPSK、16QAM、AWGN、多径瑞利信道、导频辅助信道估计、频域均衡、星座图和 BER 曲线绘制。

## 项目功能

- 随机二进制比特生成
- QPSK / 16QAM 调制与解调
- 串并转换与 OFDM 子载波映射
- IFFT 生成 OFDM 时域符号
- 循环前缀 CP 添加与去除
- AWGN 信道
- 多径瑞利衰落信道
- 导频插入
- 基于导频的 LS 信道估计
- 频域一拍均衡
- BER 与 SNR 曲线绘制
- 不同调制方式性能对比
- 不同 CP 长度对 BER 的影响分析
- 发射时域波形与接收星座图绘制

## 项目结构

```text
OFDM-Wireless-Communication-Simulator/
|-- src/ofdm_sim/
|   |-- __init__.py
|   |-- channel.py
|   |-- metrics.py
|   |-- modulation.py
|   |-- ofdm.py
|   `-- simulation.py
|-- scripts/run_simulation.py
|-- results/figures/
|-- requirements.txt
|-- README.md
`-- README_EN.md
```

## OFDM 原理简介

### 1. 随机比特源

发送端首先生成二进制比特序列：

```math
b_k \in \{0,1\}, \quad k = 0,1,\dots,N_b-1
```

### 2. 数字调制

QPSK 中，每 2 比特映射为 1 个复数符号：

```math
s = \frac{1}{\sqrt{2}} \left( \pm 1 + j(\pm 1) \right)
```

16QAM 中，每 4 比特映射为 1 个复数符号：

```math
s = \frac{1}{\sqrt{10}} (a + jb), \quad a,b \in \{\pm 1,\pm 3\}
```

归一化因子用于保证平均符号能量为 1。

### 3. 串并转换与导频插入

调制后的数据符号被映射到 OFDM 子载波上，部分子载波用于插入导频：

```math
X[k] =
\begin{cases}
X_d[k], & k \in \mathcal{D} \\
X_p[k], & k \in \mathcal{P}
\end{cases}
```

其中 `D` 为数据信道子载波集合，`P` 为导频子载波集合。

### 4. OFDM 调制

通过 IFFT 将频域子载波信号变换到时域：

```math
x[n] = \frac{1}{N}\sum_{k=0}^{N-1} X[k] e^{j2\pi kn/N}, \quad n=0,\dots,N-1
```

### 5. 循环前缀

将 OFDM 符号尾部的 `N_cp` 个采样复制到前面：

```math
x_{cp}[n] = x[(n - N_{cp}) \bmod N], \quad n=0,\dots,N+N_{cp}-1
```

当 CP 长度大于信道最大时延扩展时，线性卷积可近似转化为循环卷积，从而简化频域均衡。

### 6. 信道模型

#### AWGN 信道

```math
y[n] = x[n] + w[n]
```

其中 `w[n]` 为复高斯白噪声。

#### 多径瑞利信道

```math
h[\ell] \sim \mathcal{CN}(0,\sigma_\ell^2), \quad
y[n] = \sum_{\ell=0}^{L-1} h[\ell]x[n-\ell] + w[n]
```

### 7. 接收端处理

去除 CP 后，通过 FFT 恢复频域子载波：

```math
Y[k] = \sum_{n=0}^{N-1} y[n] e^{-j2\pi kn/N}
```

利用导频进行最小二乘信道估计：

```math
\hat{H}[k_p] = \frac{Y[k_p]}{X_p[k_p]}
```

再对全频带进行插值，并执行频域一拍均衡：

```math
\hat{X}[k] = \frac{Y[k]}{\hat{H}[k]}
```

### 8. BER 计算

误码率定义为：

```math
\mathrm{BER} = \frac{N_\mathrm{error}}{N_\mathrm{total}}
```

## 默认仿真参数

- 子载波数：64
- 循环前缀长度：16
- 导频间隔：4
- 每个 SNR 点的 OFDM 符号数：400
- 瑞利信道抽头数：6
- SNR 扫描范围：0 dB 到 20 dB

## 使用方法

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行仿真

```bash
python scripts/run_simulation.py
```

运行后会在 `results/figures/` 目录下生成图像结果。

## 仿真结果图

### 1. OFDM 系统框图

![OFDM 系统框图](results/figures/ofdm_block_diagram.svg)

### 2. 发送端时域波形

![发送端时域波形](results/figures/tx_time_waveform.svg)

### 3. 接收星座图

![接收星座图](results/figures/rx_constellation.svg)

### 4. BER-SNR 曲线

![BER-SNR 曲线](results/figures/ber_snr_curve.svg)

### 5. 不同调制方式性能对比

![不同调制方式性能对比](results/figures/modulation_comparison.svg)

### 6. 不同 CP 长度对 BER 的影响

![不同 CP 长度对 BER 的影响](results/figures/cp_length_impact.svg)

## 结果说明

- 在相同 SNR 下，QPSK 的抗噪性能优于 16QAM，因为其星座点间距更大。
- 在多径信道下，加入导频、信道估计和频域均衡后，系统可以明显恢复误码性能。
- 较长的循环前缀通常更有利于抑制码间干扰，但会牺牲一定频谱效率。
- 当前实现采用的是轻量级导频估计与线性插值方法，便于理解和复现实验流程。
