import copy
import json

import pandas as pd
import numpy as np


def eva(data):
    print(data)
    label_need = data.keys()[1:]
    print(label_need)
    data1 = data[label_need].values
    print(data1)
    data2 = data1
    print(data2)

    [m, n] = data2.shape
    data3 = copy.deepcopy(data2)
    ymin = 1e-8
    ymax = 1
    with open('norm_params_t1.json', 'r') as f:
        norm_params = json.load(f)
    for j in range(0, n):
        d_max = norm_params[str(j)]['d_max']
        d_min = norm_params[str(j)]['d_min']
        data3[:, j] = (ymax - ymin) * (d_max - data2[:, j]) / (d_max - d_min) + ymin
    formatted_data3 = np.array2string(data3, formatter={'float_kind': '{:.8f}'.format})
    print(data3)
    print(formatted_data3)

    w = np.array([0.22979309, 0.52331734, 0.24688957])

    s = np.dot(data3, w)
    score = 4 * s / max(s)
    for i in range(0, len(score)):
        print(f"No.{i} score is:：{score[i]}")
