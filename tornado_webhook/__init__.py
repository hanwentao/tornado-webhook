# SPDX-FileCopyrightText: 2022-present Wentao Han <wentao.han@gmail.com>
#
# SPDX-License-Identifier: MIT

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


def match_url(repo, url):
    for key in ['clone_url', 'ssh_url', 'git_url']:
        if repo.get(key) == url:
            return True
    return False

def match_hook(hooks, request):
    url = request.full_url()
    data = json_decode(request.body)
    for hook in hooks:
        if hook.get('hook') != url:
            continue
        if not match_url(data.get('repository'), hook.get('repo')):
            continue
        # TODO: Check signature
        return hook
    return None  # Hook not matched


class WebhookHandler(RequestHandler):

    async def post(self):
        hooks = self.settings['conf']['hooks']
        hook = match_hook(hooks, self.request)
        if hook:
            app_log.info(f'Webhook {hook["hook"]} for repo {hook["repo"]} matched')
            path = hook.get('path', '.')
            action = hook.get('action', 'true')
            app_log.info(f'Executing action "{action}"')
            proc = Subprocess(['/bin/bash', '-c', action], cwd=path)
            def proc_exit_callback(code):
                app_log.info(f'Action "{action}" done with code {code}')
            proc.set_exit_callback(proc_exit_callback)
            self.write({'status': 'executing'})
        else:
            app_log.warning(f'Webhook {self.request.full_url()} not configured')
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

def main():
    parse_command_line()
    app = make_app()
    app.listen(options.port, options.addr, xheaders=True)
    if options.debug:
        print('Debug mode activated')
    print(f'Listening at {options.addr}:{options.port}')
    IOLoop.current().start()
