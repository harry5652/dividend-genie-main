from flask import Flask

app = Flask(__name__)

@app.route("/")
def health():
    return "Dividend Genie is running!", 200