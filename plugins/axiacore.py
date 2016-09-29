#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: AxiaCore S.A.S. http://axiacore.com
import json
import random
import requests

from will import settings
from will.decorators import hear
from will.decorators import periodic
from will.decorators import randomly
from will.decorators import rendered_template
from will.decorators import require_settings
from will.decorators import respond_to
from will.plugin import WillPlugin

from pyquery import PyQuery as pq


class AxiaCorePlugin(WillPlugin):
    @hear('commit')
    def talk_on_commit(self, message):
        """
        commit: Show a cool commit message
        """
        doc = pq(url='http://whatthecommit.com/')
        text = doc('#content p:first').text()
        self.say(
            text,
            message=message,
        )

    @randomly(
        start_hour='7',
        end_hour='17',
        day_of_week='mon-fri',
        num_times_per_day=4,
    )
    def random_on_deploy(self):
        """
        deploy: Show what happens when we deploy
        """
        doc = pq(url='http://devopsreactions.tumblr.com/random')
        self.say('%s %s' % (
            doc('.post_title').text(), doc('.item img').attr('src')
        ))

    @require_settings('DOOR_URL', 'SAY_URL')
    @respond_to('^(op|open)?$')
    def open_the_door(self, message):
        """
        op or open ___: Open the door at the office
        """
        req = requests.get(settings.DOOR_URL)
        if req.ok:
            req = requests.get(settings.SAY_URL, params={
                'lang': 'es-es',
                'text': 'Siga que atras hay puesto',
            })
            self.reply(
                message, 'Say welcome %s!' % message.sender.nick.title()
            )
        else:
            self.reply(message, 'I could not open the door', color='red')

    @require_settings('PLAY_URL')
    @respond_to('^mp3 (?P<url>.*)$')
    def play_mp3(self, message, url):
        """
        mp3 ___: Play an mp3 url
        """
        req = requests.get(settings.PLAY_URL, params={
            'url': url,
        })
        if not req.ok:
            self.reply(message, 'I could not play it', color='red')

    @require_settings('SAY_URL')
    @respond_to('^say (?P<text>.*)$')
    def say_english(self, message, text):
        """
        say ___: Say an english text at the office
        """
        req = requests.get(settings.SAY_URL, params={
            'lang': 'en-us',
            'text': text,
        })
        if not req.ok:
            self.reply(message, 'I could not say it', color='red')

    @require_settings('SAY_URL')
    @respond_to('^diga (?P<text>.*)$')
    def say_spanish(self, message, text):
        """
        diga ___: Say a spanish text at the office
        """
        req = requests.get(settings.SAY_URL, params={
            'lang': 'es-es',
            'text': text,
        })
        if not req.ok:
            self.reply(message, 'I could not say it', color='red')

    @require_settings('SAY_URL')
    @periodic(hour='7', minute='0', day_of_week='mon-fri')
    def say_good_morning(self):
        requests.get(settings.SAY_URL, params={
            'lang': 'es-es',
            'text': 'Mompa les desea un feliz día. Los amo a todos.',
        })

    def __stop_playback(self):
        """
        Stop current playback.
        """
        req = requests.post(
            settings.AUDIO_URL,
            data=json.dumps({
                'id': 1,
                'jsonrpc': '2.0',
                'method': 'core.playback.stop',
            }),
        )

        return req.ok

    def __clear_tracklist(self):
        """
        Clear tracklist.
        """
        req = requests.post(
            settings.AUDIO_URL,
            data=json.dumps({
                'id': 1,
                'jsonrpc': '2.0',
                'method': 'core.tracklist.clear',
            }),
        )

        return req.ok

    @require_settings('AUDIO_URL')
    @respond_to('^silence$')
    def stop_the_beat(self, message):
        """
        silence: Stop the music at the office
        """
        success = self.__stop_playback()
        if not success:
            self.reply(message, 'I could not stop the playback', color='red')
            return

        success = self.__clear_tracklist()
        if not success:
            self.reply(message, 'I could not clear the tracklist', color='red')
            return

        self.reply(message, 'Silence please!')

    @require_settings('AUDIO_URL')
    @periodic(hour='18', minute='0')
    def stop_on_schedule(self):
        self.__stop_playback()
        self.__clear_tracklist()
        self.say('I just make sure it will be silent at night')

    @require_settings('AUDIO_URL')
    @respond_to('^play$|^play (?P<url>.*)$')
    def play_the_beat(self, message, url=None):
        """
        play or play ___: Play random radio or a url at the office
        """
        data = {
            'id': 1,
            'jsonrpc': '2.0',
            'method': '',
        }

        # Stop current playback
        data['method'] = 'core.playback.stop'
        req = requests.post(
            settings.AUDIO_URL,
            data=json.dumps(data),
        )
        if not req.ok:
            self.reply(message, 'I could not stop the playback', color='red')
            return

        # Clear tracklist
        data['method'] = 'core.tracklist.clear'
        req = requests.post(
            settings.AUDIO_URL,
            data=json.dumps(data),
        )
        if not req.ok:
            self.reply(message, 'I could not clear the tracklist', color='red')
            return

        # Get a stream to play
        if url is None:
            # Play some radio
            radio_list = [
                'http://www.977music.com/itunes/90s.pls',
                'http://www.977music.com/itunes/mix.pls',
                'http://www.977music.com/itunes/jazz.pls',
                'http://www.977music.com/977hicountry.pls',
                'http://www.977music.com/itunes/alternative.pls',
                'http://www.977music.com/itunes/oldies.pls',
                'http://www.977music.com/itunes/80s.pls',
                'http://www.977music.com/itunes/classicrock.pls',
                'http://www.977music.com/itunes/hitz.pls',
                'http://nprdmp.ic.llnwd.net/stream/nprdmp_live01_mp3',
                'http://icecast.omroep.nl/3fm-bb-mp3',
                'http://vprbbc.streamguys.net:8000/vprbbc24.mp3',
                'http://somafm.com/groovesalad.pls',
                'http://stream.kissfm.de/kissfm/mp3-128/internetradio/',
                'http://pr320.pinguinradio.com/listen.pls',
                'http://i50.letio.com/7000.aac',
                'http://94.23.184.165:8012/live',
                'http://superclasica.sytes.net:9798',
            ]
            url = random.choice(radio_list)

        # Add prefix for mopidy backends
        if 'youtube.com' in url:
            url = 'yt:%s' % url

        # Add new stream
        data['method'] = 'core.tracklist.add'
        data['params'] = {
            'tracks': None,
            'at_position': None,
            'uri': None,
            'uris': [url],
        }
        req = requests.post(
            settings.AUDIO_URL,
            data=json.dumps(data),
        )

        if not req.ok:
            self.reply(message, 'I could not add the stream', color='red')
            return

        track_name = req.json()['result'][0]['track'].get('name', url)

        # Play the beat
        del data['params']
        data['method'] = 'core.playback.play'
        req = requests.post(
            settings.AUDIO_URL,
            data=json.dumps(data),
        )

        if req.ok:
            self.reply(
                message, '"%s" will be playing for you %s' % (
                    track_name, message.sender.nick.title()
                )
            )
        else:
            self.reply(message, 'I could not play the stream', color='red')

    @randomly(
        start_hour='7',
        end_hour='17',
        day_of_week='mon-fri',
        num_times_per_day=4,
    )
    def hold_my_beer(self):
        """
        Randomly shows something funny
        """
        req = requests.get(
            'http://www.reddit.com/r/holdmybeer/top/.json?sort=top&t=day',
            headers={'User-Agent': 'Mozilla/5.0'},
        )
        if req.ok:
            elem = random.choice(req.json()['data']['children'])
            self.say('%s %s' % (elem['data']['title'], elem['data']['url']))
        else:
            self.say(req.reason, color='red')

    @respond_to('^emoji$')
    def show_emoji(self, message):
        """
        emoji: Shows the emoji used for commit messages
        """
        self.say(
            message=message,
            content=rendered_template('emoji_list.html', {}),
            html=True,
            notify=True,
        )

    @respond_to('^boss$')
    def show_boss(self, message):
        """
        boss: Shows who is responsible for merging Pull Requests
        """
        self.say(
            message=message,
            content=rendered_template('boss_list.html', {}),
            html=True,
            notify=True,
        )
