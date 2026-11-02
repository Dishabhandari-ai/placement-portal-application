from flask import Flask, session
from flask_login import LoginManager


app = None
from applications.database import db

def create_app():
  app = Flask(__name__)
  app.debug = True
  app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///e-ppa.sqlite3'
  db.init_app(app)
  app.app_context().push()
  return app

app = create_app()
app.secret_key = "your_secret_key_here"
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login" 



from applications.controllers import * 




@login_manager.user_loader
def load_user(user_id):
    role = session.get("role")

    if role == "admin":
        return Admin.query.get(int(user_id))
    elif role == "student":
        return Student.query.get(int(user_id))
    elif role == "company":
        return Company.query.get(int(user_id))

if __name__ == "__main__":
  with app.app_context():
    db.create_all()
    admin = Admin.query.filter_by(id=1).first()
    if admin is None:
      admin = Admin(name='admin1', email='admin@user.com', password='1234')
      db.session.add(admin)
      db.session.commit()
  app.run()