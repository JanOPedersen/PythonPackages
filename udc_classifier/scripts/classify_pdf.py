from udc_classifier.model import UDCClassifier
from udc_classifier.pdf_extractor import extract_text_from_pdf

MODEL_PATH = "udc_model.pkl"
PDF_PATH = r"C:\Users\janop\OneDrive\Documents\e-Papers\Not classified\FOUNDATIONS FOR BAYESIAN NETWORKS.pdf"


def main():
    clf = UDCClassifier.load(MODEL_PATH)
    prediction = clf.predict_pdf(PDF_PATH, extract_text_from_pdf)
    print("Predicted UDC code:", prediction)


if __name__ == "__main__":
    main()
