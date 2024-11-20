from flask import Flask
from flask import render_template
import tkinter as tk
from tkinter import filedialog
import sys
app = Flask(__name__)

@app.route('/')
def hello_world():
    return render_template('hello.html')

@app.route('/upload/')
def uploaduj():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename()
    return file_path