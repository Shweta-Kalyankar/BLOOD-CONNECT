from flask import Flask
from config import Config
from models import db 
from routes import init_routes
from models import BloodInventory
 


app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)


         
with app.app_context():
    db.create_all()

    init_routes(app)

if __name__ == "__main__":
    app.run(debug=True)
    




