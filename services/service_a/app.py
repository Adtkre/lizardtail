from flask import Flask, jsonify
from flask_cors import CORS, cross_origin
import random
import time

app = Flask(__name__)
CORS(app)  