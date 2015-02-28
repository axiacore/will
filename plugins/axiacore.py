from will import settings
from will.plugin import WillPlugin
from will.decorators import respond_to, periodic, hear, randomly, route, rendered_template, require_settings

from jira.client import JIRA
from jira.exceptions import JIRAError


class AxiaCorePlugin(WillPlugin):

    @hear('what do you think')
    def tell_what_i_think(self, message):
        url = 'https://s3.amazonaws.com/uploads.hipchat.com/50553/341552/g7rcdoer2w1Kv5X/miguel-approves.png'
        self.say(url, message=message)

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
                self.say('Issue {0} does not exist'.format(key), color='red')
            else:
                raise
