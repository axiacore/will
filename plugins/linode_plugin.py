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
    @respond_to('^linode(?: (?P<command>[-\w]+))?(?: (?P<arg>[=-\w]+))?')
    def linode_command(self, message, command=None, arg=None):
        """
        Get a list of available linodes.
        """
        command_list = (
            'status',
            'reboot',
            'dns-add',
        )
        if command not in command_list:
            self.reply(
                message=message,
                content='Give a command like: %s' % ', '.join(command_list),
                color='red',
                notify=True,
            )
            return

        linode_api = api.Api(settings.LINODE_API_KEY)
        linode_list = self.load('linode_list', {})

        if command == 'status':
            linode_list = {}
            for linode in linode_api.linode_list():
                linode_list[linode['LABEL']] = {
                    'id': linode['LINODEID'],
                    'status': self.STATUS[linode['STATUS']],
                }
            self.save('linode_list', linode_list)

            self.say(
                message=message,
                content=rendered_template('linode_list.html', {
                    'linode_list': linode_list,
                }),
                html=True,
                notify=True,
            )
            return

        if command == 'reboot':
            if arg not in linode_list:
                self.reply(
                    message=message,
                    content='Linode %s does not exist' % arg,
                    color='red',
                    notify=True,
                )
                return

            try:
                linode_api.linode_reboot(LinodeID=linode_list[arg]['id'])
                self.reply(
                    message=message,
                    content='%s is now rebooting' % arg,
                    notify=True,
                )
                return
            except linode_api.ApiError:
                self.reply(
                    message=message,
                    content='There was an error rebooting %s' % arg,
                    color='red',
                    notify=True,
                )
                return
