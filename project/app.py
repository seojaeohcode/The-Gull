from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

if __name__ == '__main__':
    # 환경 변수를 통해 설정한 host와 port 사용
    app.run()