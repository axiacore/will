import random
import requests

from will import settings
from will.plugin import WillPlugin
from will.decorators import respond_to, periodic, hear, randomly, route, rendered_template, require_settings

from pyquery import PyQuery as pq

from jira.client import JIRA
from jira.exceptions import JIRAError


class AxiaCorePlugin(WillPlugin):

    @hear('what do you think')
    def tell_what_i_think(self, message):
        url = 'https://s3.amazonaws.com/uploads.hipchat.com/50553/341552/g7rcdoer2w1Kv5X/miguel-approves.png'
        self.say(url, message=message)

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

    @hear('cute')
    def talk_on_cute(self, message):
        req = requests.get('http://www.reddit.com/r/aww/.json')
        if req.ok:
            self.say(
                random.choice(req.json()['data']['children'])['data']['url'],
                message=message
            )

    @require_settings('JIRA_URL', 'JIRA_USER', 'JIRA_PASSWORD')
    @hear('(\s|^)(?P<key>[A-Z]+-[0-9]+)', case_sensitive=True)
    def link_jira_issue(self, message, key):
        jira = JIRA(
            basic_auth=(settings.JIRA_USER, settings.JIRA_PASSWORD),
            options={'server': settings.JIRA_URL},
        )
        try:
            url = '[{0}] {1}browse/{2}'.format(
                jira.issue(key).fields.status.name,
                settings.JIRA_URL,
                key,
            )
            self.say(url, message=message)
        except JIRAError as exc:
            if exc.status_code == 404:
                self.say(
                    'Issue {0} does not exist'.format(key),
                    message=message,
                    color='red',
                )
            else:
                raise
