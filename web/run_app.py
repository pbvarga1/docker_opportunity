from web.app import app


def run():
    app.run(host='0.0.0.0', port=81, debug=True)


if __name__ == '__main__':
    run()
