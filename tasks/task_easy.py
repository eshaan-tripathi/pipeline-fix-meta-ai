TASK_ID = "task_easy"
DIFFICULTY = "easy"
MAX_STEPS = 5
DESCRIPTION = "Fix a broken CSV loader. The script crashes on a renamed column. Find and fix the KeyError."

BROKEN_CODE = '''\
import pandas as pd

def load_sales(filepath):
    df = pd.read_csv(filepath)
    # Someone renamed the column from "sale_amount" to "amount" but forgot to update the code
    df["revenue"] = df["sale_amount"] * 1.1
    df = df[df["sale_amount"] > 0]
    return df

if __name__ == "__main__":
    df = load_sales("data/sales.csv")
    df.to_csv("output.csv", index=False)
    print(df.head().to_string())
'''

GOLDEN_CODE = '''\
import pandas as pd

def load_sales(filepath):
    df = pd.read_csv(filepath)
    df["revenue"] = df["amount"] * 1.1
    df = df[df["amount"] > 0]
    return df

if __name__ == "__main__":
    df = load_sales("data/sales.csv")
    df.to_csv("output.csv", index=False)
    print(df.head().to_string())
'''

SAMPLE_DATA_CSV = """\
id,amount,product,region
1,120.0,Widget A,North
2,85.5,Widget B,South
3,-5.0,Widget C,East
4,200.0,Widget A,West
5,0.0,Widget B,North
"""

GOLDEN_OUTPUT_CSV = """\
id,amount,product,region,revenue
1,120.0,Widget A,North,132.0
2,85.5,Widget B,South,94.05
4,200.0,Widget A,West,220.00000000000003
"""
