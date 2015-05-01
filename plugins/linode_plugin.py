from will import settings
from will.plugin import WillPlugin
from will.decorators import respond_to, rendered_template, require_settings

from linode import api


class LinodePlugin(WillPlugin):

    def __return_error(self, message, content):
        """
        Returns an error to the user
        """
        self.reply(message=message, content=content, color='red', notify=True)
        return

    def __randompass(self):
        """
        Generate a long random password that comply to Linode requirements
        """
        import random
        import string

        random.seed()
        lwr = ''.join(random.choice(string.ascii_lowercase) for x in range(6))
        upr = ''.join(random.choice(string.ascii_uppercase) for x in range(6))
        nbr = ''.join(random.choice(string.digits) for x in range(6))
        punct = ''.join(random.choice(string.punctuation) for x in range(6))
        p = lwr + upr + nbr + punct
        return ''.join(random.sample(p, len(p)))

    @require_settings('LINODE_API_KEY')
    @respond_to('^linode status$')
    def linode_status(self, message):
        """
        Get a list of available linodes.

        Usage: linode status
        """
        STATUS = {
            -1: 'Being Created',
            0: 'Brand New',
            1: 'Running',
            2: 'Powered Off',
        }

        linode_api = api.Api(settings.LINODE_API_KEY)

        linode_list = {}
        for linode in linode_api.linode_list():
            linode_list[linode['LABEL']] = {
                'id': linode['LINODEID'],
                'status': STATUS[linode['STATUS']],
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

    @require_settings('LINODE_API_KEY')
    @respond_to('^linode reboot (?P<label>[-\w]+)$')
    def linode_reboot(self, message, label):
        """
        Reboot a linode.

        Usage: linode reboot my-linode-label
        """
        linode_api = api.Api(settings.LINODE_API_KEY)
        linode_list = self.load('linode_list', {})

        if label not in linode_list:
            return self.__return_error(
                message=message,
                content='Linode %s does not exist' % label,
            )

        try:
            linode_api.linode_reboot(LinodeID=linode_list[label]['id'])
            self.reply(
                message=message,
                content='%s is now rebooting' % label,
                notify=True,
            )
            return
        except linode_api.ApiError:
            return self.__return_error(
                message=message,
                content='There was an error rebooting %s' % label,
            )

    @require_settings('LINODE_API_KEY')
    @respond_to('^linode create (?P<label>[-\w]+)$', admin_only=True)
    def linode_create(self, message, label=None):
        """
        Create a linode.

        Usage: linode create boom
        """
        PLAN = 1            # Linode 1024
        PAYMENT = 1         # Monthly
        DISTRO = 124        # Ubuntu 14.04 LTS
        KERNEL = 138        # Latest 64 bit (3.19.1-x86_64-linode53)
        DATACENTER = 6      # Newark, NJ, USA
        DATA_SIZE = 8192    # 8 GB
        SWAP_SIZE = 512     # 512 MB

        linode_api = api.Api(settings.LINODE_API_KEY)

        # Create linode
        response = linode_api.linode_create(
            DatacenterID=DATACENTER,
            PlanID=PLAN,
            PaymentTerm=PAYMENT,
        )
        linode_id = response['LinodeID']

        # Set the label
        linode_api.linode_update(
            LinodeId=linode_id,
            Label=label,
        )

        # Create distribution
        password = self.__randompass()
        response = linode_api.linode_disk_createfromdistribution(
              LinodeId=linode_id,
              DistributionID=DISTRO,
              Label='Ubuntu 14.04 LTS Disk',
              Size=DATA_SIZE,
              rootPass=password,
        )
        disk_list = []
        disk_list.append(response['DiskID'])

        # Create swap disk
        response = linode_api.linode_disk_create(
            LinodeId=linode_id,
            Type='swap',
            Label='Swap Disk',
            Size=SWAP_SIZE,
        )
        disk_list.append(response['DiskID'])

        # Create config
        linode_api.linode_config_create(
            LinodeId=linode_id,
            KernelId=KERNEL,
            Label='Ubuntu 14.04 LTS Profile',
            Disklist=disk_list,
        )

        # Boot
        linode_api.linode_boot(LinodeId=linode_id)

        # Get IP
        ip = linode_api.linode_ip_list(LinodeId=linode_id)[0]['IPADDRESS']

        self.reply(
            message=message,
            content='%s was created with <b>%s</b> and password <b>%s</b>' % (
                label,
                ip,
                password,
            ),
            html=True,
            notify=True,
        )

    @require_settings('LINODE_API_KEY')
    @respond_to('^linode dns-add (?P<full_domain>[a-z0-9]+\.[a-z0-9]+\.[a-z0-9]+) (?P<ip>\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})$')
    def linode_dns_add(self, message, full_domain, ip):
        """
        Add a DNS record for a domain in linode.

        Usage: linode dns-add my.domain.co 8.8.8.8
        """
        linode_api = api.Api(settings.LINODE_API_KEY)

        subdomain, domain = full_domain.split('.', 1)

        # Get domain ID
        domain_id = None
        for linode_domain in linode_api.domain_list():
            if domain == linode_domain['DOMAIN']:
                domain_id = linode_domain['DOMAINID']
                break

        if domain_id is None:
            return self.__return_error(
                message=message,
                content='Domain %s does not exist' % domain,
            )

        # Check if the subdomain already exist
        subdomain_list = linode_api.domain_resource_list(
            DomainID=domain_id,
        )
        for linode_subdomain in subdomain_list:
            if (
                subdomain == linode_subdomain['NAME']
                and linode_subdomain['TYPE'].upper() == 'A'
            ):
                return self.__return_error(
                    message=message,
                    content='Subdomain %s already exists' % subdomain,
                )

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
        except linode_api.ApiError:
            return self.__return_error(
                message=message,
                content='There was an error setting %s' % full_domain,
            )

    @require_settings('LINODE_API_KEY')
    @respond_to('^linode dns-remove (?P<full_domain>[a-z0-9]+\.[a-z0-9]+\.[a-z0-9]+)$')
    def linode_dns_remove(self, message, full_domain=None):
        """
        Remove a DNS record for a domain in linode.

        Usage: linode dns-remove my.domain.co
        """
        linode_api = api.Api(settings.LINODE_API_KEY)

        subdomain, domain = full_domain.split('.', 1)

        # Get domain ID
        domain_id = None
        for linode_domain in linode_api.domain_list():
            if domain == linode_domain['DOMAIN']:
                domain_id = linode_domain['DOMAINID']
                break

        if domain_id is None:
            return self.__return_error(
                message=message,
                content='Domain %s does not exist' % domain,
            )

        # Check if the subdomain already exists
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

        if resource_id is None:
            return self.__return_error(
                message=message,
                content='Subdomain %s does not exist' % subdomain,
            )

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
        except linode_api.ApiError:
            return self.__return_error(
                message=message,
                content='There was an error removing %s' % full_domain,
            )
