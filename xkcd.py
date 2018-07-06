
import logging
import os
import random
import re
import requests

from errbot import botcmd, BotPlugin


class XKCDClient(object):
    base_uri = 'https://xkcd.com'

    def __init__(self, base_uri=None):
        if base_uri is not None:
            if base_uri.endswith('/'):
                base_uri = base_uri[:-1]
            self.base_uri = base_uri


    def latest(self):
        url = 'info.0.json'
        return self.get(url)


    def random(self):
        latest = self.latest()
        latest_num = latest['num']
        random_num = random.randint(1, latest['num'])
        return self.comic(random_num)


    def comic(self, num):
        url = '{}/info.0.json'.format(num)
        return self.get(url)


    def get(self, url, params=None):
        return self.request('get', url, params=params)


    def post(self, url, data=None):
        return self.request('post', url, data=data)


    def request(self, method, url, data=None, params=None):
        method = getattr(requests, method.lower(), 'get')

        if url.startswith('/'):
            url = url[1:]

        logging.debug('Sending {} request to {}'.format(method, url))
        try:
            kwargs = {}
            if params is not None:
                kwargs.update({'params': params})
            if data is not None:
                kwargs.update({'json': data})

            resp = method(
                '{}/{}'.format(self.base_uri, url),
                **kwargs)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(e)
            return {}

        return resp.json()


class XKCD(BotPlugin):
    """Retrieve XKCD Comics"""

    client = None
    pattern = None

    def activate(self, *args, **kwargs):
        super(XKCD, self).activate(*args, **kwargs)
        self.client = XKCDClient()
        self.pattern = r'https?://xkcd.com/(\d+)\D*'


    def deactivate(self, *args, **kwargs):
        super(XKCD, self).deactivate(*args, **kwargs)
        self.client = None
        self.pattern = None


    #def callback_message(self, msg):
    #    author_nick = str(msg.frm.nick)
    #    ignore_nicks = [self.bot_identifier.nick]

    #    # Ignore all messages from the bot itself
    #    if author_nick in ignore_nicks:
    #        return

    #    if str(msg.to) == self.bot_identifier.nick:
    #        channel_id = self.build_identifier(str(msg.frm.nick))
    #    else:
    #        channel_id = self.build_identifier(str(msg.to));

    #    match = re.search(self.pattern, msg.body, re.IGNORECASE)
    #    if match is not None:
    #        comic = self._get_comic(channel_id, match)
    #        if comic:
    #            self.send(channel_id, comic['img'])


    def _get_comic(self, num):
        if num == 'latest':
            comic = self.client.latest()

        elif num and int(num) > 0:
            comic = self.client.comic(num)

        else:
            comic = self.client.random()

        return comic


    @botcmd(split_args_with=None)
    def xkcd(self, msg, args):
        """
        Retrieves an XKCD comic, latest, by num or random
        """

        num = None
        if len(args) > 0:
            num = args[0]

        comic = self._get_comic(num)

        if comic:
            url = '{}/{}/'.format(self.client.base_uri, comic['num'])
            yield '{}\n{}\n'.format(url, comic['alt'])

        else:
            yield 'That comic was not found'
