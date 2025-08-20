import sqlite3

class LoginModel:
    def __init__(self):
        self.connection = sqlite3.connect('database/database.db')
        self.cursor = self.connection.cursor()