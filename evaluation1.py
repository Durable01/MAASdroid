import copy
import json

import pandas as pd
import numpy as np

excel_path = r'E:\Fastbot_Android-main\eval1.xlsx'
data = pd.read_excel(excel_path, usecols='A:E')
print(data)

label_need = data.keys()[1:]
print(label_need)
data1 = data[label_need].values
print(data1)

data2 = data1
[m, n] = data2.shape
data3 = copy.deepcopy(data2)
ymin = 1e-8
ymax = 1
norm_params = {}
for j in range(0, n):
    d_max = max(data2[:, j])
    d_min = min(data2[:, j])
    data3[:, j] = (ymax - ymin) * (d_max - data2[:, j]) / (d_max - d_min) + ymin
    norm_params[j] = {'d_max': d_max, 'd_min': d_min}

with open('norm_params_t1.json', 'w') as f:
    json.dump(norm_params, f)
formatted_data3 = np.array2string(data3, formatter={'float_kind': '{:.8f}'.format})
print(data3)
print(formatted_data3)

w = np.array([0.18044275, 0.41092976, 0.19386759, 0.21475991])

s = np.dot(data3, w)
score = 5 * s / max(s)

s4 = s[4]
adjusted_score = 4

above_threshold = s > s4
max_above = s[above_threshold].max()
s[above_threshold] = 5 * score[above_threshold] / score[4]

below_threshold = s < s4
min_below = s[below_threshold].min()
s[below_threshold] = 1 + (s[below_threshold] - min_below) * (5 - 1) / (s4 - min_below)

s[4] = adjusted_score

print("Final score is:")
for i in range(0, len(s)):
    print(f"No.{i} score is: {s[i]}")
