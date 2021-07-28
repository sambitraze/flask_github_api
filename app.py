from flask import Flask
from github import Github

app = Flask(__name__)

@app.route('/')
def home():
    # g = Github("sambitraze", "raze123@")
    # for repo in g.get_user().get_repos():
    #     print(repo.name)
    return "hello"

@app.route('/')
def getRepo():
    return "Hello World"

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=4000, debug=True)