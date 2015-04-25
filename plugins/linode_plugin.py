from will import settings
from will.plugin import WillPlugin
from will.decorators import respond_to, rendered_template, require_settings

from linode import api


class LinodePlugin(WillPlugin):

    @require_settings('LINODE_API_KEY')
    @respond_to('^linode list$')
    def linode_list(self, message):
        """
        Get a list of available linodes.
        """
        status = {
            -1: 'Being Created',
            0: 'Brand New',
            1: 'Running',
            2: 'Powered Off',
        }
        linode_api = api.Api(settings.LINODE_API_KEY)

        linode_list = self.load('linode_list', {})
        for linode in linode_api.linode_list():
            linode_list[linode['LABEL']] = {
                'id': linode['LINODEID'],
                'status': status[linode['STATUS']],
            }
        self.save('linode_list', linode_list)

        self.say(rendered_template('linode_list.html', {
            'linode_list': linode_list,
        }), message=message, html=True)
