from flask import Blueprint, request, jsonify, render_template, current_app
from datetime import datetime, timezone

main = Blueprint('main', __name__)

def format_timestamp(ts_string):
    dt = datetime.fromisoformat(ts_string.replace("Z", "+00:00"))
    dt = dt.astimezone(timezone.utc)
    
    day = dt.day
    if 11 <= day <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    
    return dt.strftime(f"{day}{suffix} %B %Y - %I:%M %p UTC")

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/webhook', methods=['POST'])
def webhook():
    event_type = request.headers.get('X-GitHub-Event')
    payload = request.json

    if event_type == 'ping':
        return jsonify({"msg": "pong"}), 200

    db = current_app.db
    doc = None

    if event_type == 'push':
        author = payload['pusher']['name']
        to_branch = payload['ref'].replace('refs/heads/', '')
        timestamp = payload['head_commit']['timestamp']
        request_id = payload['head_commit']['id']

        doc = {
            "request_id": request_id,
            "author": author,
            "action": "PUSH",
            "from_branch": None,
            "to_branch": to_branch,
            "timestamp": format_timestamp(timestamp)
        }

    elif event_type == 'pull_request':
        pr = payload['pull_request']
        action = payload['action']

        if action == 'opened':
            doc = {
                "request_id": str(pr['number']),
                "author": pr['user']['login'],
                "action": "PULL_REQUEST",
                "from_branch": pr['head']['ref'],
                "to_branch": pr['base']['ref'],
                "timestamp": format_timestamp(pr['created_at'])
            }
        elif action == 'closed' and pr.get('merged'):
            doc = {
                "request_id": str(pr['number']),
                "author": pr['merged_by']['login'],
                "action": "MERGE",
                "from_branch": pr['head']['ref'],
                "to_branch": pr['base']['ref'],
                "timestamp": format_timestamp(pr['merged_at'])
            }

    if doc:
        db.events.insert_one(doc)

    return jsonify({"msg": "received"}), 200

@main.route('/events', methods=['GET'])
def get_events():
    db = current_app.db
    events = list(db.events.find().sort("_id", -1).limit(20))
    for e in events:
        e['_id'] = str(e['_id'])
    return jsonify(events), 200