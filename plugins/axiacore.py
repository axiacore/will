#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: AxiaCore S.A.S. http://axiacore.com
import json
import random
import requests

from will import settings
from will.plugin import WillPlugin
from will.decorators import hear
from will.decorators import respond_to
from will.decorators import randomly
from will.decorators import require_settings
from will.decorators import periodic
from will.decorators import rendered_template

from pyquery import PyQuery as pq


class AxiaCorePlugin(WillPlugin):

    @hear('commit')
    def talk_on_commit(self, message):
        """
        Show a cool commit message: commit
        """
        doc = pq(url='http://whatthecommit.com/')
        text = doc('#content p:first').text()
        self.say(
            text,
            message=message,
        )

    @hear('culpa')
    def talk_on_petro(self, message):
        """
        Find someone to blame: culpa
        """
        base_url = 'https://s3.amazonaws.com/uploads.hipchat.com/50553/341552/'
        petro_list = (
            'MucOQkTfZh19ExH/petro-1.jpg',
            'O0fYobd2noZDzqW/petro-2.jpg',
            'zG31qjiNMAAATPy/petro-3.jpg',
            'CeggogfkfI3uKSb/petro-4.jpeg',
            'jA7DdXUwjMzctwx/petro-5.jpg',
            'Fr6tAtcKvdtjwJ5/petro-6.jpeg',
            'DquhpnqGVomkVLu/petro-7.jpg',
        )
        self.say('La culpa siempre es de petro', message=message)
        self.say(base_url + random.choice(petro_list), message=message)

    @hear('deploy')
    def talk_on_deploy(self, message):
        """
        Show what happens when deploy: deploy
        """
        doc = pq(url='http://devopsreactions.tumblr.com/random')
        self.say(doc('.post_title').text(), message=message)
        self.say(doc('.item img').attr('src'), message=message)

    @require_settings('DOOR_URL', 'SAY_URL')
    @respond_to('^(op|open|abra)( (?P<text>.*))?$')
    def open_the_door(self, message, text):
        """
        Open the door at the office: op or open or abra
        """
        req = requests.get(settings.DOOR_URL)
        if req.ok:
            req = requests.get(settings.SAY_URL, params={
                'lang': 'es-es',
                'text': text,
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
        Play an mp3 url: play http://www.noiseaddicts.com/samples_1w72b820/3694.mp3
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
        Say a text at the office: say hello
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
        Say a text at the office: diga hola
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

    @periodic(hour='12', minute='0', day_of_week='mon-fri')
    def lunch_time(self):
        say_list = [
            u'Seguimos entregando, seguimos llevando el almuerzo calidoso.',
            u'Llego la hora de raspar la olla. ¿Quien va primero?',
            u'Tengo un filo, que si me agacho me corto.',
            u'Heee, todo bien mijitos que no les voy a cortar la cara con la mela',
            u'Otra vez lentejas y agua de panela.',
            u'Llego la mazamorra calientica.',
            u'A la order el boje, llevelo pues pa acabar con este poquitico',
            u'Lleve la mela, a luca no mas, a luca',
            u'Que pasó papás, lo que es con la gurbia es con migo oooomee.',
        ]

        req = requests.get(settings.SAY_URL, params={
            'lang': 'es-es',
            'text': random.choice(say_list),
        })
        if not req.ok:
            return self.say('I could not say it', color='red')

        req = requests.get(
            'http://domicilios.com/establecimientos/producto/370375/19136',
            headers={'User-Agent': 'Mozilla/5.0'},
        )

        data = {}
        letters = 'ABCDEFGHI'
        for index, group in enumerate(req.json()['grupoextras']):
            choices = []
            for number, option in enumerate(group['extras']):
                choices.append(
                    u'{0}{1}: {2}'.format(
                        letters[index],
                        number,
                        option['nombre']
                    )
                )
            data[group['nombre']] = choices

        self.say(
            content=rendered_template('lunch_menu.html', {'data': data}),
            html=True,
            notify=True,
        )

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
    @respond_to('^stop$')
    def stop_the_beat(self, message):
        """
        Stop the music at the office: stop
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
    @periodic(hour='17', minute='0', day_of_week='mon-fri')
    def stop_on_schedule(self):
        self.__stop_playback()
        self.__clear_tracklist()
        self.say('I just make sure it will be silent at night')

    @require_settings('AUDIO_URL')
    @respond_to('^play$|^play (?P<url>.*)$')
    def play_the_beat(self, message, url=None):
        """
        Play music at the office: play or play URL
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
            self.say(elem['data']['title'])
            self.say(elem['data']['url'])
        else:
            self.say(req.reason, color='red')

    @respond_to('^emoji$')
    def show_emoji(self, message):
        """
        Show emoji list
        """
        emoji_list = '\n(lollipop) :lollipop: when improving code format and structure, \n(art) :art: when making visual changes, \n(bug) :bug: when fixing bugs, \n(memo) :memo: when writing documentation, \n(fire) :fire: when removing unused code, \n(sunny) :sunny: alternative emoji for a general improvement, \n(whitecheckmark) :white_check_mark: when fixing tests \n'

        self.reply(message, emoji_list)
