from flask import Flask, request, g, session, redirect, url_for
from flask import render_template_string, jsonify
from flask_github import GitHub

DEBUG = True

GITHUB_CLIENT_ID = 'Iv1.387ade82abe70fd3'
GITHUB_CLIENT_SECRET= '4311124136b8370cd6aee062a00580ac9a093300'

app = Flask(__name__)
app.config.from_object(__name__)

# setup github-flask
github = GitHub(app)


# @app.before_request
# def before_request():
#     g.user = None
#     if 'user_id' in session:
#         g.user = User.query.get(session['user_id'])


# @app.after_request
# def after_request(response):
#     db_session.remove()
#     return response


@app.route('/')
def index():
    # if g.user:
    #     t = 'Hello! %s <a href="{{ url_for("user") }}">Get user</a> ' \
    #         '<a href="{{ url_for("repo") }}">Get repo</a> ' \
    #         '<a href="{{ url_for("logout") }}">Logout</a>'
    #     t %= g.user.github_login
    # else:
    t = 'Hello! <a href="{{ url_for("login") }}">Login</a>'

    return render_template_string(t)


@github.access_token_getter
def token_getter():
    return g.user.github_access_token


@app.route('/github-callback')
@github.authorized_handler
def authorized(access_token):
    next_url = request.args.get('next') or url_for('index')
    if access_token is None:
        return redirect(next_url)

    # user = User.query.filter_by(github_access_token=access_token).first()
    # if user is None:
    #     user = User(access_token)
    #     db_session.add(user)

    # user.github_access_token = access_token

    # # Not necessary to get these details here
    # # but it helps humans to identify users easily.
    # g.user = user
    # github_user = github.get('/user')
    # user.github_id = github_user['id']
    # user.github_login = github_user['login']

    # db_session.commit()

    # session['user_id'] = user.id
    return redirect(next_url)


@app.route('/login')
def login():
    if session.get('user_id', None) is None:
        return github.authorize()
    else:
        return 'Already logged in'


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/user')
def user():
    return jsonify(github.get('/user'))


@app.route('/repo')
def repo():
    return jsonify(github.get('/repos/cenkalti/github-flask'))

if __name__ == '__main__':
    app.run(debug=True, port=4000, host='0.0.0.0',)