from will import settings
from will.plugin import WillPlugin
from will.decorators import respond_to, rendered_template, require_settings

from linode import api


class LinodePlugin(WillPlugin):

    STATUS = {
        -1: 'Being Created',
        0: 'Brand New',
        1: 'Running',
        2: 'Powered Off',
    }

    @require_settings('LINODE_API_KEY')
    @respond_to('^linode (?P<command>.*) (?P<machine>.*)')
    def linode_command(self, message, command=None, machine=None):
        """
        Get a list of available linodes.
        """
        command_list = (
            'status',
            'reboot',
        )
        if command not in command_list:
            self.say(
                'Give a command like: %s' % ', '.join(command_list),
                message=message,
            )

        linode_api = api.Api(settings.LINODE_API_KEY)

        if command == 'status':
            linode_list = self.load('linode_list', {})
            for linode in linode_api.linode_list():
                linode_list[linode['LABEL']] = {
                    'id': linode['LINODEID'],
                    'status': self.STATUS[linode['STATUS']],
                }
            self.save('linode_list', linode_list)

            self.say(rendered_template('linode_list.html', {
                'linode_list': linode_list,
            }), message=message, html=True)