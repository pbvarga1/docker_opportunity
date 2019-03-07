from app.app import app
# from app.app import db
# from app.models import ProductType, Image, Camera


def run():
    app.run(host='0.0.0.0', port=80, debug=True)


if __name__ == '__main__':
    # db.drop_all()
    # db.create_all()
    run()
