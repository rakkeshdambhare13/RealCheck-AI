from pathlib import Path
from PIL import Image
import time

from predict_image import predict_image


# ==========================================
# REALCHECK AI - IMAGE ROBUSTNESS TEST
# ==========================================

TEST_DIR = Path("test_images")


def test_image(image_path):

    print("\n================================")
    print("TESTING:", image_path.name)
    print("================================")

    try:

        image = Image.open(image_path)

        print("Image format :", image.format)
        print("Image size   :", image.size)

        start_time = time.time()

        label, confidence, prediction = predict_image(image)

        analysis_time = time.time() - start_time

        print("Result       :", label)
        print(
            f"Confidence   : {confidence:.2f}%"
        )
        print(
            f"Analysis time: {analysis_time:.2f} seconds"
        )

        print("STATUS       : PASS")

        return True

    except Exception as e:

        print("STATUS       : FAIL")
        print("Error        :", e)

        return False


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    print("================================")
    print("REALCHECK AI ROBUSTNESS TEST")
    print("================================")

    if not TEST_DIR.exists():

        TEST_DIR.mkdir()

        print(
            "\nCreated test_images folder."
        )

        print(
            "Put your test images inside:"
        )

        print(
            "C:\\RD_Project\\test_images"
        )

        exit()

    images = list(
        TEST_DIR.glob("*.jpg")
    )

    images += list(
        TEST_DIR.glob("*.jpeg")
    )

    images += list(
        TEST_DIR.glob("*.png")
    )

    if not images:

        print(
            "\nNo test images found."
        )

        print(
            "Put JPG/PNG images inside "
            "test_images folder."
        )

        exit()

    passed = 0
    failed = 0

    for image_path in images:

        result = test_image(
            image_path
        )

        if result:
            passed += 1
        else:
            failed += 1

    print("\n================================")
    print("TEST SUMMARY")
    print("================================")

    print(
        "Total tests :", len(images)
    )

    print(
        "Passed      :", passed
    )

    print(
        "Failed      :", failed
    )

    print(
        "================================"
    )