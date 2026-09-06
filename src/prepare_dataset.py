import pandas as pd
from PIL import Image
from io import BytesIO
from pathlib import Path


DATA_DIR = Path("dataset_download/data")
OUTPUT_DIR = Path("datasets/image")


def process_parquet(parquet_file, split):
    print(f"\nProcessing: {parquet_file}")

    df = pd.read_parquet(parquet_file)

    for index, row in df.iterrows():

        image_data = row["image"]
        label = int(row["label"])

        # 0 = Real
        # 1 = Fake
        if label == 0:
            output_dir = OUTPUT_DIR / split / "real"
        else:
            output_dir = OUTPUT_DIR / split / "fake"

        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Image stored as dictionary containing raw bytes
            image_bytes = image_data["bytes"]

            image = Image.open(BytesIO(image_bytes))
            image = image.convert("RGB")

            output_file = output_dir / f"{split}_{index:06d}.jpg"
            image.save(output_file, "JPEG")

        except Exception as e:
            print(f"Error at index {index}: {e}")

        if (index + 1) % 500 == 0:
            print(f"Processed {index + 1} images")


# -----------------------------
# TRAIN DATA
# -----------------------------

train_files = sorted(DATA_DIR.glob("train-*.parquet"))

for file in train_files:
    process_parquet(file, "train")


# -----------------------------
# VALIDATION DATA
# -----------------------------

validation_files = sorted(DATA_DIR.glob("validation-*.parquet"))

for file in validation_files:
    process_parquet(file, "validation")


print("\n===================================")
print("DATASET EXTRACTION COMPLETED")
print("===================================")