"""
DATA SOURCE DETAILS (not included: sponsor-confidential)
------------------------------------------------
Data Structure of Excel Spreadsheet:
Sheet:   first sheet (default), header on row 1, one row per timestamp
Period:  <first timestamp> to <last timestamp> (calendar year 2025)
Step:    <e.g. hourly>; <n> rows; <any gaps or missing values>

(Zero-indexed)
Columns (read by position; the header encoding is unreliable):
  0  Timestamp                       text, "DD-Mon-YY H:MM:SS AM/PM TZ",
                                     TZ = BST or GMT (UK local time with
                                     clock changes) -> converted to UTC here
  1  Sec_CT_CKT_1_Flow_Temp(°C)      circuit 1 supply water temp, °C
  2  Sec_CT_CKT_1_Return_Temp(°C)    circuit 1 return water temp, °C
  3  Sec_CT_CKT_2_Flow_Temp(°C)      circuit 2 supply water temp, °C
  4  Sec_CT_CKT_2_Return_Temp(°C)    circuit 2 return water temp, °C
  5  Outside Temperature - (°C)      outdoor air temp, °C
  6  Sec_CT_CKT_1_Vol_Flow (L/s)
  7  Sec_CT_CKT_2_Vol_Flow (L/s)

Notes:
  - "Sec" = secondary circuits after the common header; "CT" assumed to mean
    constant temperature (to confirm with sponsor).
  - Flow rates are not logged in this file (spot readings ~8-11 l/s).
  - To reproduce without the data, build a table with this exact layout
    (e.g. synthetic values) and run the script on it.
"""

import sys
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
from waste_heat_model.physics.thermo import water_heat_flow_kw

# Explore BMS data
#old_spreadsheet = "../Triangle_Building_Data_Centre_October/Triangle Boiler Data_Robert.xlsx"
spreadsheet = "../Triangle_Building_Data_Centre_November/Triangle Boiler Data_Robert.xlsx"

df = pd.read_excel(spreadsheet)
print(df.columns.tolist())
print(df.head(3))

# Headings, picked by position (avoids the Â°C glitch) - AI generated workaround
t_out = df.columns[5]   # Outside Temperature
sup1 = df.columns[1]    # Sec_CT_CKT_1_Flow_Temp
ret1 = df.columns[2]    # Sec_CT_CKT_1_Return_Temp
sup2, ret2 = df.columns[3], df.columns[4]
flow1, flow2 = df.columns[6], df.columns[7]

ts = df.columns[0]
s = df[ts].astype(str)
offset = s.str[-3:].map({"BST": "+0100", "GMT": "+0000"})
df[ts] = pd.to_datetime(s.str[:-4] + " " + offset,
                        format="%d-%b-%y %I:%M:%S %p %z", utc=True)
df = df.set_index(ts).sort_index()
# End of AI generated code

# sys.path("outputs").mkdir(exist_ok=True)   # if outputs/ isn't in git, so create it
fig, ax = plt.subplots(3, 1, figsize=(8, 10))
ax[0].scatter(df[t_out], df[sup1], s=2)
ax[0].set(xlabel="Outdoor °C", ylabel="Supply °C")
ax[1].hist(df[sup1] - df[ret1], bins=50)
ax[1].set(xlabel="Supply − return (K)", ylabel="Hours")
plt.tight_layout()
#plt.show()

#fig, ax = plt.subplots(figsize=(12, 4))
df[[sup1, ret1, t_out]].resample("D").mean().plot(ax=ax[2], lw=1)
ax[2].set(ylabel="°C", title="Circuit 1: daily mean temperatures")
plt.tight_layout()

RHO_KG_PER_L = 0.98   # water at ~60-70 °C; placeholder -> add to base.yaml properties after scripting
TO_KG_S = RHO_KG_PER_L          # if the unit is l/s; if m3/h use RHO_KG_PER_L * 1000 / 3600

df["q1_kw"] = water_heat_flow_kw(df[flow1] * TO_KG_S, df[sup1], df[ret1])
df["q2_kw"] = water_heat_flow_kw(df[flow2] * TO_KG_S, df[sup2], df[ret2])
df["q_kw"] = df["q1_kw"] + df["q2_kw"]

# New data (as of november)
daily = df.resample("D").mean(numeric_only=True)
fig2, ax2 = plt.subplots(3, 1, figsize=(9, 11))
daily[[flow1, flow2]].plot(ax=ax2[0], lw=1, title="Flow rate per circuit (daily mean)")
daily[["q1_kw", "q2_kw", "q_kw"]].plot(ax=ax2[1], lw=1, title="Measured heat, kW (daily mean)")
ax2[2].scatter(daily[t_out], daily["q_kw"], s=6)
ax2[2].set(xlabel="Outdoor °C (daily mean)", ylabel="Heat, kW", title="Energy signature")
fig2.tight_layout()
#Path("outputs").mkdir(exist_ok=True)
#fig2.savefig("outputs/bms_heat_first_look.png", dpi=150)

plt.show()