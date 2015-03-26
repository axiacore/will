import random
import requests

from will import settings
from will.plugin import WillPlugin
from will.decorators import respond_to, periodic, hear, randomly, route, rendered_template, require_settings

from pyquery import PyQuery as pq


class AxiaCorePlugin(WillPlugin):

    @hear('commit')
    def talk_on_commit(self, message):
        doc = pq(url='http://whatthecommit.com/')
        text = doc('#content p:first').text()
        self.say(
            '@{0} try this commit message: {1}'.format(
                message.sender.nick,
                text,
            ),
            message=message,
        )

    @hear('pug')
    def talk_on_pug(self, message):
        req = requests.get('http://pugme.herokuapp.com/random')
        if req.ok:
            self.say(req.json()['pug'], message=message)

    @hear('deploy')
    def talk_on_deploy(self, message):
        doc = pq(url='http://devopsreactions.tumblr.com/random')
        self.say(doc('.post_title').text(), message=message)
        self.say(doc('.item img').attr('src'), message=message)

    @randomly(
        start_hour=9,
        end_hour=17, day_of_week='mon-fri', num_times_per_day=2
    )
    def random_fun(self, message):
        req = requests.get(
            'http://www.reddit.com/r/holdmybeer/top/.json?sort=top&t=week'
        )
        if req.ok:
            elem = random.choice(req.json()['data']['children'])
            self.say(elem['data']['url'], message=message)
            self.say(elem['data']['title'], message=message)

    @require_settings('DOOR_URL')
    @respond_to('open the door')
    def open_the_door(self, message):
        req = requests.get(settings.DOOR_URL)
        if req.ok:
            self.reply(message, 'Say welcome %s!' % message.sender.nick)
        else:
            self.reply(message, 'I could not open the door', color='red')
