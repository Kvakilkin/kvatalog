from flask import Flask, render_template
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('Ozon.html')

@app.route('/static_page')
def static_page():
    return app.send_static_file

@app.route('/run-script')
def run_script():
    try:
        # Запускаем скрипт ozon_parcer.py
        result = subprocess.run(['python', 'ozon_parcer.py'], capture_output=True, text=True)
        return f"Скрипт завершил выполнение с кодом "
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    app.run(port=5500, debug=True)