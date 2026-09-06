import pandas as pd
from pathlib import Path

file = Path("dataset_download/data/validation-00000-of-00004.parquet")

df = pd.read_parquet(file)

print("LABEL COUNTS")
print(df["label"].value_counts().sort_index())

print("\nGENERATOR COUNTS")
print(df["generator"].value_counts().sort_index())

print("\nLABEL + GENERATOR")
print(
    df.groupby(["label", "generator"])
      .size()
      .reset_index(name="count")
)