TASK_ID = "task_hard"
DIFFICULTY = "hard"
MAX_STEPS = 15
DESCRIPTION = (
    "Fix a multi-file pipeline that merges monthly sales CSVs. "
    "Bugs: (1) schema drift — column renamed across files, "
    "(2) duplicate rows not removed before merge, "
    "(3) merge key is non-unique causing row explosion, "
    "(4) revenue computed before currency normalisation (mix of USD/GBP), "
    "(5) output sorted incorrectly (ascending instead of descending by revenue)."
)

BROKEN_CODE = '''\
import pandas as pd
import glob

def load_all_months(pattern):
    files = glob.glob(pattern)
    frames = []
    for f in files:
        df = pd.read_csv(f)
        frames.append(df)
    # Bug 1: no column harmonisation — jan uses "sales_amount", feb uses "amount"
    combined = pd.concat(frames, ignore_index=True)
    return combined

def enrich(df, fx_rates):
    # Bug 2: duplicate rows not removed
    # Bug 3: merging on "product_id" which is non-unique in fx_rates → row explosion
    df = df.merge(fx_rates, on="product_id", how="left")
    # Bug 4: revenue computed before currency conversion
    df["revenue_usd"] = df["sales_amount"] * df["quantity"]
    return df

def finalise(df):
    # Bug 5: should be ascending=False
    df = df.sort_values("revenue_usd", ascending=True)
    return df[["product_id", "product_name", "revenue_usd", "month"]]

if __name__ == "__main__":
    df = load_all_months("data/monthly_*.csv")
    fx = pd.read_csv("data/fx_rates.csv")
    df = enrich(df, fx)
    df = finalise(df)
    df.to_csv("output.csv", index=False)
    print(df.head().to_string())
'''

GOLDEN_CODE = '''\
import pandas as pd
import glob

COLUMN_MAP = {
    "sales_amount": "amount",
    "sale_amount": "amount",
}

def load_all_months(pattern):
    files = sorted(glob.glob(pattern))
    frames = []
    for f in files:
        df = pd.read_csv(f)
        df = df.rename(columns=COLUMN_MAP)
        frames.append(df)
    combined = pd.concat(frames, ignore_index=True)
    combined = combined.drop_duplicates()
    return combined

def enrich(df, fx_rates):
    fx_rates = fx_rates.drop_duplicates(subset=["product_id"])
    df = df.merge(fx_rates, on="product_id", how="left")
    df["revenue_usd"] = df["amount"] * df["quantity"] * df["usd_rate"]
    return df

def finalise(df):
    df = df.sort_values("revenue_usd", ascending=False)
    return df[["product_id", "product_name", "revenue_usd", "month"]]

if __name__ == "__main__":
    df = load_all_months("data/monthly_*.csv")
    fx = pd.read_csv("data/fx_rates.csv")
    df = enrich(df, fx)
    df = finalise(df)
    df.to_csv("output.csv", index=False)
    print(df.head().to_string())
'''

MONTHLY_JAN_CSV = """\
product_id,product_name,sales_amount,quantity,month,currency
P001,Gadget X,29.99,100,Jan,USD
P002,Gadget Y,49.99,50,Jan,GBP
P001,Gadget X,29.99,100,Jan,USD
"""

MONTHLY_FEB_CSV = """\
product_id,product_name,amount,quantity,month,currency
P001,Gadget X,29.99,120,Feb,USD
P003,Gadget Z,19.99,200,Feb,USD
"""

FX_RATES_CSV = """\
product_id,product_name,usd_rate
P001,Gadget X,1.0
P001,Gadget X,1.0
P002,Gadget Y,1.27
P003,Gadget Z,1.0
"""

GOLDEN_OUTPUT_CSV = """\
product_id,product_name,revenue_usd,month
P003,Gadget Z,3998.0,Feb
P001,Gadget X,3598.8,Feb
P002,Gadget Y,3174.365,Jan
P001,Gadget X,2999.0,Jan
"""