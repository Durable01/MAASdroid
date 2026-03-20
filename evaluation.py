import copy
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
    for j in range(0, n):
        d_max = max(data2[:, j])
        d_min = min(data2[:, j])
        data3[:, j] = (ymax - ymin) * (d_max - data2[:, j]) / (d_max - d_min) + ymin
    formatted_data3 = np.array2string(data3, formatter={'float_kind': '{:.8f}'.format})
    print(data3)
    print(formatted_data3)

    p = copy.deepcopy(data3)
    for j in range(0, n):
        p[:, j] = data3[:, j] / sum(data3[:, j])
    # p[p == 0] = 1e-8
    print(p)
    E = copy.deepcopy(data3[0, :])
    for j in range(0, n):
        E[j] = -1 / np.log(m) * sum(p[:, j] * np.log(p[:, j]))
    print(E)

    w = (1 - E) / sum(1 - E)
    print(f'w:{w}\n')

    # w = np.array([0.18044275, 0.41092976, 0.19386759, 0.21475991])  # Test set weights

    s = np.dot(data3, w)
    Score = 5 * s / max(s)
    for i in range(0, len(Score)):
        print(f"No.{i+1} score is: {Score[i]}")



