#!/usr/bin/env python3

import yaml

from tornado.escape import json_decode
from tornado.ioloop import IOLoop
from tornado.log import app_log
from tornado.options import define, options, parse_command_line
from tornado.process import Subprocess
from tornado.routing import AnyMatches
from tornado.web import Application, RequestHandler

define('address', default='localhost', help='address to listen at')
define('port', default=8080, help='port to listen on')
define('debug', default=False, help='debug mode')
define('config', default='webhooks.yaml', help='webhook configuration file')


class WebhookHandler(RequestHandler):

    async def post(self):
        hooks = self.settings['config']['hooks']
        url = self.request.full_url()
        # data = json_decode(self.request.body)
        for hook in hooks:
            if hook.get('hook') == url:  # TODO: better matching method
                app_log.info(f'URL {url} matched')
                args = [hook.get('cmd', '/bin/bash')] + hook.get('args', [])
                app_log.info(f'Executing task {args}')
                proc = Subprocess(args)
                def proc_exit_callback(code):
                    app_log.info(f'Task {args} done with code {code}')
                proc.set_exit_callback(proc_exit_callback)
                self.write({'status': 'executing'})
                break
        else:
            app_log.warning(f'URL {url} not configured')
            self.write({'status': 'failure'})
            self.set_status(400)


def make_app():
    with open(options.config) as config_file:
        config = yaml.safe_load(config_file)
    return Application(
        [(AnyMatches(), WebhookHandler)],
        config=config,
        debug=options.debug,
    )


if __name__ == '__main__':
    parse_command_line()
    app = make_app()
    server = app.listen(options.port, options.address, xheaders=True)
    if options.debug:
        print('Debug mode activated')
    print(f'Listening at {options.address}:{options.port}')
    IOLoop.current().start()
