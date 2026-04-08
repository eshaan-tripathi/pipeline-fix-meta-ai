TASK_ID = "task_medium"
DIFFICULTY = "medium"
MAX_STEPS = 10
DESCRIPTION = (
    "Repair a 3-step ETL pipeline. There are 3 bugs: "
    "(1) a type casting error converting strings to int instead of float, "
    "(2) NaN values not dropped before aggregation causing silent NaN output, "
    "(3) date column parsed with wrong format string."
)

BROKEN_CODE = '''\
import pandas as pd

def extract(filepath):
    df = pd.read_csv(filepath)
    return df

def transform(df):
    # Bug 1: should be float, not int — will raise ValueError on decimals
    df["price"] = df["price"].astype(int)

    # Bug 2: NaN not dropped — mean() will silently return NaN
    df["avg_price"] = df.groupby("category")["price"].transform("mean")

    # Bug 3: wrong date format — should be %d/%m/%Y not %Y-%m-%d
    df["sale_date"] = pd.to_datetime(df["sale_date"], format="%Y-%m-%d")

    return df

def load(df, output_path):
    df.to_csv(output_path, index=False)

if __name__ == "__main__":
    df = extract("data/transactions.csv")
    df = transform(df)
    load(df, "output.csv")
    print(df.head().to_string())
'''

GOLDEN_CODE = '''\
import pandas as pd

def extract(filepath):
    df = pd.read_csv(filepath)
    return df

def transform(df):
    df["price"] = df["price"].astype(float)
    df = df.dropna(subset=["price"])
    df["avg_price"] = df.groupby("category")["price"].transform("mean")
    df["sale_date"] = pd.to_datetime(df["sale_date"], format="%d/%m/%Y")
    return df

def load(df, output_path):
    df.to_csv(output_path, index=False)

if __name__ == "__main__":
    df = extract("data/transactions.csv")
    df = transform(df)
    load(df, "output.csv")
    print(df.head().to_string())
'''

SAMPLE_DATA_CSV = """\
id,price,category,sale_date
1,10.5,Electronics,15/06/2023
2,25.0,Clothing,20/07/2023
3,,Electronics,01/08/2023
4,8.75,Clothing,10/08/2023
5,150.0,Electronics,22/09/2023
"""

GOLDEN_OUTPUT_CSV = """\
id,price,category,sale_date,avg_price
1,10.5,Electronics,2023-06-15,80.25
2,25.0,Clothing,2023-07-20,16.875
4,8.75,Clothing,2023-08-10,16.875
5,150.0,Electronics,2023-09-22,80.25
"""