import joblib
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from sklearn.feature_extraction.text import TfidfVectorizer


class UDCClassifier:
    def __init__(self, model=None):
        self.model = model or Pipeline([
            ("tfidf", TfidfVectorizer(
                stop_words="english",
                max_df=0.9,
                min_df=2,
                ngram_range=(1, 2)
            )),
            ("clf", LinearSVC(random_state=42))
        ])

    def train(self, texts, labels):
        self.model.fit(texts, labels)

    def predict_pdf(self, pdf_path, extractor):
        text = extractor(pdf_path)
        return self.model.predict([text])[0]

    def save(self, path):
        joblib.dump(self.model, path)

    @staticmethod
    def load(path):
        model = joblib.load(path)
        return UDCClassifier(model)
