import sys
import pandas as pd
import matplotlib.pyplot as plt

# Explore BMS data
spreadsheet = "../Triangle_Building_Data_Centre_October/Triangle Boiler Data_Robert.xlsx"

df = pd.read_excel(spreadsheet)
print(df.columns.tolist())
print(df.head(3))

# Headings, picked by position (avoids the Â°C glitch) - AI generated workaround
t_out = df.columns[5]   # Outside Temperature
sup1 = df.columns[1]    # Sec_CT_CKT_1_Flow_Temp
ret1 = df.columns[2]    # Sec_CT_CKT_1_Return_Temp

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
ax[1].set(xlabel="Supply − return (K)")
#plt.tight_layout()
#plt.show()

#fig, ax = plt.subplots(figsize=(12, 4))
df[[sup1, ret1, t_out]].resample("D").mean().plot(ax=ax[2], lw=1)
ax[2].set(ylabel="°C", title="Circuit 1: daily mean temperatures")
plt.tight_layout()
plt.show()