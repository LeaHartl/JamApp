from app import app, db
from app.models import User, Entry, Stake
#https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-ii-templates



@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Entry': Entry, 'Stake': Stake}