from flask import Flask, render_template, request,url_for
app = Flask(__name__)

@app.route("/")
def hello():
    return render_template('index.html')

@app.route('/hashtag', methods=['POST'])
def get_tweet_data():
    hashtag = request.POST.get('hashtag')  
    print hashtag
    print url_for('hashtag')
    return;


if __name__ == "__main__":
    app.run(debug=True)
