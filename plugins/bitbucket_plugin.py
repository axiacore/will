from will import settings
from will.plugin import WillPlugin
from will.decorators import respond_to, rendered_template, require_settings

import requests


class BitbucketPlugin(WillPlugin):

    @require_settings('BITBUCKET_USER', 'BITBUCKET_PASS')
    @respond_to('^create repo (?P<customer>[\w]+) (?P<project>[\w]+)$')
    def linode_status(self, message, customer, project):
        """
        Create a new repository: create repo Google Billing
        """
        self.say(
            message=message,
            content="I'm creating a new repo. Hang in there tiger...",
        )

        team = 'axiacore'
        slug = '{0}-{1}'.format(customer.lower(), project.lower())
        name = '{0} - {1}'.format(customer.title(), project.title())
        url = 'https://api.bitbucket.org/2.0/repositories/{0}/{1}'.format(
            team,
            slug,
        )
        data = {
            'scm': 'git',
            'name': name,
            'is_private': True,
            'fork_policy': 'no_forks',
        }

        response = requests.post(
            url,
            data=data,
            auth=(settings.BITBUCKET_USER, settings.BITBUCKET_PASS),
        ).json()

        if 'error' in response:
            self.reply(
                message=message,
                content=response['error']['message'],
                color='red',
                notify=True,
            )
            return

        self.reply(
            message=message,
            content='{0} repository was just created for you.'.format(
                response['name'],
            )
        )
        self.say(
            message=message,
            content='Clone URL: git@bitbucket.org:{0}/{1}.git'.format(
                team,
                response['slug'],
            )
        )
