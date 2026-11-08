import sys
import pandas as pd
import matplotlib.pyplot as plt

# Explore BMS data
spreadsheet = "../Triangle_Building_Data_Centre_October/Triangle Boiler Data_Robert.xlsx"

df = pd.read_excel(spreadsheet)
print(df.columns.tolist()); print(df.head(3))

# Template to plot results instead - for Outdoor temperature not Boiler
"""
t_out, sup1, ret1 = "<outdoor col>", "<circuit 1 supply>", "<circuit 1 return>"
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
ax[0].scatter(df[t_out], df[sup1], s=2); ax[0].set(xlabel="Outdoor °C", ylabel="Supply °C")
ax[1].hist(df[sup1] - df[ret1], bins=50); ax[1].set(xlabel="Supply − return (K)")
plt.tight_layout(); plt.savefig("outputs/bms_circuit1.png", dpi=150)
"""