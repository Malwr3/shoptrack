import os
from flask import Flask

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'shoptrack.db'),
    )

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import models
    
    with app.app_context():
        models.init_db()

    app.teardown_appcontext(models.close_db)

    from . import routes
    app.register_blueprint(routes.bp)

    return app
