from flask import Flask, json, jsonify, redirect, \
                 render_template, url_for
from flask import session as login_session
from flask.helpers import make_response
from flask import request
from flask_cors import CORS, cross_origin # My front end is with React and works on a different server

import requests
import random
import string
from credentials import client_id, client_secret # credentials.py has the client_id and client_secret

app = Flask(__name__)
CORS(app) #allows CORS on all routes
app.secret_key = 'super secret key'

authorization_base_url = 'https://github.com/login/oauth/authorize'
token_url = 'https://github.com/login/oauth/access_token'
request_url = 'https://api.github.com'

# 1. Shows login page with a random 'state' parameter to prevent CSRF
@app.route('/')
def showLogin():
  '''
    Shows login page. Sends a random 'state' parameter to the page
    to prevent csrf. If you have your front-end running on a different
    server you can choose to create the 'state' value their or send the
    value from this endpoint.
    The value of 'state' is also stored in session object for future use.
    Returns a random string for 'state' and an optional template.
  '''
  state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
  login_session['state'] = state
  # return jsonify(state=state) # to return state in a json response
  return render_template('login.html', state=state)


# 1. Send initial request to get permissions from the user
@app.route('/handleLogin', methods=["GET"])
def handleLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    if login_session['state'] == state:
        fetch_url = authorization_base_url + \
            '?client_id=' + client_id + \
            '&state=' + login_session['state'] + \
            '&scope=user%20repo%20public_repo' + \
                '&allow_signup=true'
        return redirect(fetch_url)
    else:
        return jsonify(invalid_state_token="invalid_state_token")


#2. Using the /callback route to handle authentication.
@app.route('/callback', methods=['GET', 'POST'])
def handle_callback():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter!'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    if 'code' in requests.args:
        #return jsonify(code=request.args.get('code'))
        payload = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': request.args['code']
        }
        headers = {'Accept': 'application/json'}
        req = requests.post(token_url, params=payload, headers=headers)
        resp = req.json()

        if 'access_token' in resp:
            login_session['access_token'] = resp['access_token']
            return jsonify(access_token=resp['access_token'])
            #return redirect(url_for('index'))
        else:
            return jsonify(error="Error retrieving access_token"), 404
    else:
        return jsonify(error="404_no_code"), 404

# 3. Get user information from Github 
@app.route('/index')
def index():
    # Check for access_token in session
    if 'access_token' not in login_session:
        return 'Never trust strangers', 404
    # Get user information from github api
    access_token_url = 'https://api.github.com/user?access_token={}'
    r = requests.get(access_token_url.format(login_session['access_token']))
    try:
        resp = r.json()
        gh_profile = resp['html_url'] 
        username = resp['login']
        avatar_url = resp['avatar_url']
        bio = resp['bio']
        name = resp['name']
        return jsonify(
          gh_profile=gh_profile,
          gh_username=username,
          avatar_url=avatar_url,
          gh_bio=bio,
          name=name
        )
    except AttributeError:
        app.logger.debug('error getting username from github, whoops')
        return "I don't know who you are; I should, but regretfully I don't", 500
      
# This endpoint fetches list of repositories of a user
@app.route('/user/<string:username>')
def getRepos(username):
    if not 'access_token' in login_session:
        invalid_access_token="Access token has expired or not in session"
        app.logger.error(invalid_access_token)
        return jsonify(invalid_access_token=invalid_access_token)
    if not username:
        return jsonify(username_not_give="Github username needed to fetch \
                                         repos")
    # ?per_page=N : Have N>500. By default Github only returns first 30 objects
    # returned by any query and then the rest are obtained in a different ways.
    # Like using the 'since' parameter to mention the last ID you saw or using 
    # the Link header. Read More about it at: https://developer.github.com/v3/#pagination
    url = request_url + '/users/{username}/repos?per_page=500'.format(username=username)
    headers = {'Accept': 'application/json'}
    try:
        req = requests.get(url, headers=headers, timeout=4)
    except (requests.exceptions.Timeout) as e:
        return jsonify("connection timed out")

    if req.status_code == 200:
        resp = req.json()
        try:
            app.logger.debug("Try to get repository names from response")
            repo_info = []
            for each_repo in resp:
                repo_dict = {}
                repo_dict['repo_name'] = each_repo['full_name']
                repo_dict['repo_link'] = each_repo['html_url']
                repo_dict['description'] = each_repo['description']
                repo_dict['owner_fullname'] = each_repo['owner']['login']
                repo_dict['html_url'] = each_repo['html_url']
                repo_info.append(repo_dict)
            app.logger.debug("Successfully fetched repository info from response")
            return jsonify(  
                repo_count=len(repo_info),
                repo_info=repo_info
            ), 200
        except (TypeError, AttributeError, KeyError) as e:
            app.logger.error(e)
            return jsonify(no_user_found="no user found"), 404
    else:
        res = req.json()['message']
        return jsonify(error=res)

# Get commits on a repository by username
@app.route('/user/<string:username>/<string:repo_name>/commits')
def getCommits(username, repo_name):
    if not 'access_token' in login_session:
        invalid_access_token="Access token has expired or not in session"
        app.logger.error(invalid_access_token)
        return jsonify(invalid_access_token=invalid_access_token)
    if not username and not repo_name:
        return jsonify(username_not_give="Github username or repo_name missing")
    url = request_url + '/repos/{username}/{repo_name}/commits'\
          .format(username=username, repo_name=repo_name)
    headers = {'Accept': 'application/json'}
    res = requests.get(url, headers=headers)
    commits = res.json()
    try:
        app.logger.info("Try to get commits information inside getCommits")
        commit_info = []
        for commit in commits:
            commit_dict = {}
            commit_dict['commit_author'] = commit['commit']['author']['name']
            commit_dict['commit_date'] = commit['commit']['author']['date']
            commit_dict['commit_msg'] = commit['commit']['message']
            commit_info.append(commit_dict)
        app.logger.info("Commit info retrieval successfull")
        return jsonify(commits=commit_info)
    except (TypeError, AttributeError, KeyError)as e:
        app.logger.error(e)
        return jsonify(error=e)
    
if __name__ == '__main__':
    app.run(debug=True, port=4000, host='0.0.0.0',)