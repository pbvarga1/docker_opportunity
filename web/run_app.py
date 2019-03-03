import aiohttp

from web.app import app


async def run():
    async with aiohttp.ClientSession() as session:
        app.session = session
        app.run(host='0.0.0.0', port=81, debug=True)


if __name__ == '__main__':
    run()
