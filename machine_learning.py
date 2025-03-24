# machine_learning.py

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

def train_model(X_train, y_train):
    model = LinearRegression()
    model.fit(X_train, y_train)
    return model

def evaluate_model(model, X_test, y_test):
    return model.score(X_test, y_test)
