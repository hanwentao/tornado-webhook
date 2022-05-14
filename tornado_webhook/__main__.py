#!/usr/bin/env python3

import yaml

from tornado.escape import json_decode
from tornado.ioloop import IOLoop
from tornado.log import app_log
from tornado.options import define, options, parse_command_line
from tornado.process import Subprocess
from tornado.routing import AnyMatches
from tornado.web import Application, RequestHandler

define('addr', default='localhost', help='address to listen at')
define('port', default=8080, help='port to listen on')
define('conf', default='webhooks.yaml', help='path to configuration file')
define('debug', default=False, help='debug mode')


class WebhookHandler(RequestHandler):

    async def post(self):
        hooks = self.settings['conf']['hooks']
        url = self.request.full_url()
        data = json_decode(self.request.body)
        for hook in hooks:
            if hook.get('hook') == url:  # TODO: better matching method
                app_log.info(f'Webhook {url} matched')
                path = hook.get('path', '.')
                action = hook.get('action', 'true')
                app_log.info(f'Executing action "{action}"')
                proc = Subprocess(['/bin/bash', '-c', action], cwd=path)
                def proc_exit_callback(code):
                    app_log.info(f'Action "{action}" done with code {code}')
                proc.set_exit_callback(proc_exit_callback)
                self.write({'status': 'executing'})
                break
        else:
            app_log.warning(f'Webhook {url} not configured')
            self.write({'status': 'failure'})
            self.set_status(400)


def make_app():
    with open(options.conf) as conf_file:
        conf = yaml.safe_load(conf_file)
    return Application(
        [(AnyMatches(), WebhookHandler)],
        conf=conf,
        debug=options.debug,
    )


if __name__ == '__main__':
    parse_command_line()
    app = make_app()
    server = app.listen(options.port, options.addr, xheaders=True)
    if options.debug:
        print('Debug mode activated')
    print(f'Listening at {options.addr}:{options.port}')
    IOLoop.current().start()
