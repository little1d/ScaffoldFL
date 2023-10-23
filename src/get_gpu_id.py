# encoding:gbk
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei']

import torch

if torch.cuda.is_available():
    device = torch.cuda.current_device()
    print(f"GPU ID： {device}")
else:
    print("No GPU available.")
