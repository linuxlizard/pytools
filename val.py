#/usr/bin/env python3

# Valentine.
# davep 14-Nov-2016
#
# math via https://twitter.com/walkingrandomly/status/698156033403920384

import numpy as np
import matplotlib.pyplot as plt

x = np.arange(-2, 2, 0.001, dtype="complex")
y = (np.sqrt(np.cos(x))*np.cos(200*x) + np.sqrt(np.abs(x))-0.7) * (4-x*x)**0.01
plt.plot(x, np.real(y), ".")
plt.show()

