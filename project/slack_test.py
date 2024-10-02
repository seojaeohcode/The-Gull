import json
from flask import Flask, request, make_response

app = Flask(__name__)

@app.route('/', methods=['POST'])
def hello_there():
    slack_event = json.loads(request.data)
    
    # Slack에서 온 'challenge' 요청을 처리하고 응답
    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"Content-Type": "application/json"})
    
    return make_response("There are no slack request events", 404, {"X-Slack-No-Retry": 1})

# '/인사' Slash Command 처리 라우트
@app.route('/slash-hello', methods=['POST'])
def slash_hello():
    slack_event = request.form  # Slash command는 form data로 전달됨
    
    # Slash Command '/인사' 처리
    if slack_event.get('command') == '/인사':
        return make_response("Hello", 200)
    
    return make_response("Command not recognized", 404)

if __name__ == '__main__':
    app.run()