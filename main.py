# ______________import_____________
from flask import Flask, render_template

from data import db


#_______________init_______________

app = Flask(__name__)

# ______________routes____________

@app.route('/')
def index():
    return render_template('index.html', title='Main page')



# ______________start_____________
def main():
    db.global_init("db/database.db")
    app.run()

if __name__ == '__main__':
    main()