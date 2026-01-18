import json
from udc_classifier.hierarchy import walk_hierarchy
from udc_classifier.dataset_builder import build_dataset
from udc_classifier.model import UDCClassifier

HIERARCHY_PATH = r"C:\Users\janop\OneDrive\Documents\Obsidian Vault\.temp\hierarchy_papers.json"
ROOT_DIR = r"C:\Users\janop\OneDrive\Documents\e-Papers\e-library_shortened"


def main():
    with open(HIERARCHY_PATH, "r", encoding="utf-8") as f:
        tree = json.load(f)

    codes_dict = walk_hierarchy(tree, ROOT_DIR)
    texts, labels = build_dataset(codes_dict)

    clf = UDCClassifier()
    clf.train(texts, labels)
    clf.save("udc_model.pkl")

    print("Model saved as udc_model.pkl")


if __name__ == "__main__":
    main()
