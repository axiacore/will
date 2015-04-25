from will import settings
from will.plugin import WillPlugin
from will.decorators import respond_to, periodic, hear, randomly, route, rendered_template, require_settings

from linode import api


class LinodePlugin(WillPlugin):

    @require_settings('LINODE_API_KEY')
    @respond_to('^linode list$')
    def linode_list(self, message):
        linode_api = api.Api(settings.LINODE_API_KEY)

        self.say(rendered_template('linode_list.html', {
            'linode_list': linode_api.linode_list(),
            }), message=message, html=True)
