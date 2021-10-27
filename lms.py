#!/usr/bin/env python3

import logging
from requests import Session
from requests.compat import urljoin
import socket
from datetime import timedelta
from sys import version_info, argv

if version_info < (3, 0):
    exit('Python 3 required')

__version__ = '1.1.0'

_LOGGER = logging.getLogger(__name__)
TIMEOUT = timedelta(seconds=5)


def _discover():
    _LOGGER.info('Discovering server')
    ip = '<broadcast>'
    port = 3483
    query = b'eJSON\0'
    response = b'EJSON'
    timeout = TIMEOUT
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(timeout.seconds)
            sock.bind(('', 0))
            sock.sendto(query, (ip, port))
            while True:
                try:
                    data, (ip, _) = sock.recvfrom(1024)
                    if not data.startswith(response):
                        continue
                    length = data[5:6][0]
                    port = int(data[0 - length:])
                    return ip, port
                except socket.timeout:
                    break
    except OSError as err:
        _LOGGER.warning('Discovery failed: %s', err)
    return None, None


# FIXME: Support async/await

class Server:

    def __init__(self, host=None, port=9000, username=None, password=None):
        if not host:
            host, port = _discover()
            if not host:
                exit('Could not initialize server')
            _LOGGER.info('Server at %s:%d discovered', host, port)
        self._host = host
        self._port = port
        self._session = Session()
        self._username = username
        self._password = password
        self._state = {}
        self._players = {}
        if username and password:
            self._session.auth = (username, password)

    def __str__(self):
        return '%s:%d (%s)' % (
            self._host, self._port, self.version) + '\n' + '\n'.join(
                ' - ' + str(p) for p in self.players)

    def query(self, *command, **kwparams):

        command = list(command)
        player = kwparams.pop('player', '')

        # handle tagged params
        command.extend(map(lambda p: ':'.join(map(str, p)),
                           kwparams.items()))

        url = 'http://{}:{}/jsonrpc.js'.format(self._host, self._port)
        data = dict(id='1',
                    method='slim.request',
                    params=[player, command])
        _LOGGER.debug('URL: %s Data: %s', url, data)
        try:
            result = self._session.post(
                url, json=data, timeout=TIMEOUT.seconds)
            result.raise_for_status()
            result = result.json()
            _LOGGER.debug(result)
            return result['result']
        except OSError as e:
            _LOGGER.warning('Could not query server: %s', e)
            return {}

    def update(self):
        self._state = self.server_status
        if self._state:
            self._players = {player['playerid']: Player(self, player)
                             for player in self._state['players_loop']}
            self.update_players()

    def update_players(self):
        for player in self.players:
            player.update()

    def can(self, what):
        return self.players[0].can(what)

    @property
    def _url(self):
        if self._username and self._password:
            return 'http://{username}:{password}@{server}:{port}/'.format(
                username=self._username,
                password=self._password,
                server=self._host,
                port=self._port)
        return 'http://{server}:{port}/'.format(
            server=self._host,
            port=self._port)

    @property
    def version(self):
        return self._state.get('version')

    @property
    def server_status(self):
        return self.query('serverstatus', '-')

    @property
    def players_status(self):
        return self.query('players', 'status')

    @property
    def favorites(self):
        return self.query('favorites', 'items')

    @property
    def players(self):
        return list(self._players.values())

    def player(self, player_id):
        return self._players[player_id]


class Player:

    def __init__(self, server, player):
        self._server = server
        self._state = player

    def __str__(self):
        return '%s (%s %s:%s:%s %d%%): %s - %s (%3d%%: %s / %s)' % (
            self.name, self.player_id, self.model, self.ip, self.port,
            self.wifi_signal_strength,
            self.artist or '', self.title or '',
            self.position_pct,
            self.position, self.duration)

    @property
    def player_id(self):
        return self._state['playerid']

    @property
    def is_synced(self):
        return 'sync_master' in self._state

    def sync_to(self, other):
        self.query('sync', other.player_id)

    def unsync(self):
        self.query('sync', '-')

    @property
    def name(self):
        return self._state['name']

    @property
    def address(self):
        return self._state.get('player_ip', "IP unkown:Port unkown").split(':')

    @property
    def ip(self):
        return self.address[0]

    @property
    def port(self):
        return self.address[1]

    @property
    def model(self):
        return self._state['modelname']

    @property
    def is_on(self):
        return self._state.get('power') == 1

    @property
    def mode(self):
        return self._state.get('mode')

    @property
    def is_playing(self):
        return self.mode == 'play'

    @property
    def is_stopped(self):
        return self.mode == 'stop'

    @property
    def is_paused(self):
        return self.mode == 'pause'

    @property
    def is_shuffle(self):
        return self._state.get('playlist_shuffle') == 1

    @property
    def is_repeat(self):
        return self._state.get('playlist_repeat') == 1

    def can(self, what):
        return self.query('can', what, 'items', '?')

    def query(self, *params, **kwparams):
        return self._server.query(*params, **kwparams, player=self.player_id)

    def update(self):
        tags = 'adKl'  # artist, duration, artwork, album
        response = self.query(
            'status', '-', '1', 'tags:{tags}'
            .format(tags=tags))

        if response is False:
            return

        try:
            self._state.update(response['playlist_loop'][0])
        except KeyError:
            pass

        try:
            self._state.update(response['remoteMeta'])
        except KeyError:
            pass

        self._state.update(response)

    @property
    def track_id(self):
        return self._state['id']

    @property
    def volume(self):
        if 'mixer volume' in self._state:
            return int(self._state['mixer volume'])

    @property
    def is_muted(self):
        return str(self._state.get('mixer volume', '')).startswith('-')

    @property
    def position(self):
        if 'time' in self._state:
            return int(float(self._state['time']))

    @property
    def position_pct(self):
        return 100 * self.position / self.duration if self.duration else 0

    @property
    def duration(self):
        if 'duration' in self._state:
            return int(float(self._state['duration']))

    @property
    def artwork_url(self):
        if 'artwork_url' in self._state:
            url = self._state['artwork_url']
        elif 'id' in self._state:
            url = '/music/{track_id}/cover.jpg'.format(
                track_id=self._state['id'])
        else:
            url = '/music/current/cover.jpg?player={player}'.format(
                player=self.player_id)
        return urljoin(self._server._url, url)

    @property
    def title(self):
        return self._state.get('title') or self._state.get('current_title')

    @property
    def artist(self):
        return self._state.get('artist')

    @property
    def album_name(self):
        return self._state.get('album')

    def volume_up(self):
        return self.query('mixer', 'volume', '+5')

    def volume_down(self):
        return self.query('mixer', 'volume', '-5')

    def set_volume(self, volume):
        return self.query('mixer', 'volume', volume)

    def mute(self, mute=True):
        return self.query('mixer', 'muting', '1' if mute else '0')

    def unmute(self):
        return self.mute(False)

    def play(self):
        return self.query('play')

    def pause(self):
        return self.query('pause', '1')

    def next(self):
        return self.query('playlist', 'index', '+1')

    def previous(self):
        return self.query('playlist', 'index', '-1')

    def seek(self, position):
        return self.query('time', position)

    def turn_off(self):
        return self.query('power', '0')

    def turn_on(self):
        return self.query('power', '1')

    def play_uri(self, url):
        return self.query('playlist', 'play', url)

    def enqueue_uri(self, url):
        return self.query('playlist', 'add', url)

    @property
    def wifi_signal_strength(self):
        return int(self._state.get('signalstrength'))


if __name__ == '__main__':
    if '-vv' in argv:
        logging.basicConfig(level=logging.DEBUG)
    elif '-v' in argv:
        logging.basicConfig(level=logging.INFO)
    server = Server()

    # print(server)
    # from pprint import pprint
    # print(server.query('can', 'spotty', 'items', '?'))
    # player = server.players[0]
    # pprint(player.query('spotty', 'items', 0, 255))
    # print('---')
    # pprint(player.query('spotty', 'items', 0, 255,
    # dict(item_id=0, want_url=1)))
    # pprint(player.query('spotty', 'items', 0, 255,
    # dict(item_id='0.0', want_url=1, search='Queen')))
