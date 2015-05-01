from will import settings
from will.plugin import WillPlugin
from will.decorators import respond_to, rendered_template, require_settings

import re
from linode import api


class LinodePlugin(WillPlugin):

    STATUS = {
        -1: 'Being Created',
        0: 'Brand New',
        1: 'Running',
        2: 'Powered Off',
    }

    DNS_REGEX = \
        '^([a-z0-9]+\.[a-z0-9]+\.[a-z0-9]+)=(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})$'

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
            'dns-remove',
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

        if command == 'dns-add':
            regex = re.compile(self.DNS_REGEX)
            if not bool(regex.match(arg)):
                self.reply(
                    message=message,
                    content='The argument must be some.domain.com=ip_address',
                    color='red',
                    notify=True,
                )
                return

            full_domain, ip = arg.split('=')
            subdomain, domain = full_domain.split('.', 1)

            # Get domain ID
            domain_id = None
            for linode_domain in linode_api.domain_list():
                if domain == linode_domain['DOMAIN']:
                    domain_id = linode_domain['DOMAINID']
                    break

            if not domain_id:
                self.reply(
                    message=message,
                    content='Domain %s does not exist' % domain,
                    color='red',
                    notify=True,
                )
                return

            # Check if the subdomain already exist
            subdomain_list = linode_api.domain_resource_list(
                DomainID=domain_id,
            )
            for linode_subdomain in subdomain_list:
                if (
                    subdomain == linode_subdomain['NAME']
                    and linode_subdomain['TYPE'].upper() == 'A'
                ):
                    self.reply(
                        message=message,
                        content='Subdomain %s already exists' % subdomain,
                        color='red',
                        notify=True,
                    )
                    return

            try:
                linode_api.domain_resource_create(
                    DomainID=domain_id,
                    Type='A',
                    Name=subdomain,
                    Target=ip,
                )
                self.reply(
                    message=message,
                    content='%s will now respond from %s' % (full_domain, ip),
                    notify=True,
                )
                return
            except linode_api.ApiError:
                self.reply(
                    message=message,
                    content='There was an error setting %s' % full_domain,
                    color='red',
                    notify=True,
                )
                return

        if command == 'dns-remove':
            regex = re.compile('^([a-z0-9]+\.[a-z0-9]+\.[a-z0-9]+)$')
            if not bool(regex.match(arg)):
                self.reply(
                    message=message,
                    content='The argument must be some.domain.com',
                    color='red',
                    notify=True,
                )
                return

            full_domain, ip = arg.split('=')
            subdomain, domain = full_domain.split('.', 1)

            # Get domain ID
            domain_id = None
            for linode_domain in linode_api.domain_list():
                if domain == linode_domain['DOMAIN']:
                    domain_id = linode_domain['DOMAINID']
                    break

            if not domain_id:
                self.reply(
                    message=message,
                    content='Domain %s does not exist' % domain,
                    color='red',
                    notify=True,
                )
                return

            # Check if the subdomain already exist
            resource_id = None
            subdomain_list = linode_api.domain_resource_list(
                DomainID=domain_id,
            )
            for linode_subdomain in subdomain_list:
                if (
                    subdomain == linode_subdomain['NAME']
                    and linode_subdomain['TYPE'].upper() == 'A'
                ):
                    resource_id = linode_subdomain['ResourceID']
                    break

            if not resource_id:
                self.reply(
                    message=message,
                    content='Subdomain %s does not exist' % subdomain,
                    color='red',
                    notify=True,
                )
                return

            try:
                linode_api.domain_resource_delete(
                    DomainID=domain_id,
                    ResourceID=resource_id,
                )
                self.reply(
                    message=message,
                    content='%s was removed' % full_domain,
                    notify=True,
                )
                return
            except linode_api.ApiError:
                self.reply(
                    message=message,
                    content='There was an error removing %s' % full_domain,
                    color='red',
                    notify=True,
                )
                return
