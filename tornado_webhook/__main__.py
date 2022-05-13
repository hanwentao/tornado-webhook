#!/usr/bin/env python3

from tornado.escape import json_decode
from tornado.ioloop import IOLoop
from tornado.options import define, options, parse_command_line
from tornado.process import Subprocess
from tornado.web import Application, RequestHandler

define('address', default='localhost', help='address to listen at')
define('port', default=8080, help='port to listen on')
define('debug', default=False, help='debug mode')


class WebhookHandler(RequestHandler):

    async def post(self):
        data = json_decode(self.request.body)
        time = data.get('time', 1)
        proc = Subprocess(['sleep', str(time)])
        code = await proc.wait_for_exit(False)
        self.write({'code': code})


def make_app():
    return Application([
        ('/webhook/', WebhookHandler),
    ], debug=options.debug)


if __name__ == '__main__':
    parse_command_line()
    app = make_app()
    server = app.listen(options.port, options.address, xheaders=True)
    if options.debug:
        print('Debug mode activated')
    print(f'Listening at {options.address}:{options.port}')
    IOLoop.current().start()
