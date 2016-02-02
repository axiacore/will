#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: AxiaCore S.A.S. http://axiacore.com
from will import settings
from will.plugin import WillPlugin
from will.decorators import respond_to, require_settings

import json
import requests


class BitbucketPlugin(WillPlugin):

    @require_settings('BITBUCKET_USER', 'BITBUCKET_PASS')
    @respond_to('^create repo (?P<customer>[\w-]+) (?P<project>[\w-]+)$')
    def create_repository(self, message, customer, project):
        """
        Create a new repository: create repo Google Billing
        """
        self.say(
            message=message,
            content="I'm creating a new repo. Hang in there tiger...",
        )

        bb = 'https://api.bitbucket.org'
        url = bb + '/2.0/repositories/{0}/{1}/'.format(
            'axiacore',
            '{0}-{1}'.format(customer.lower(), project.lower()),
        )
        data = {
            'scm': 'git',
            'name': '{0} - {1}'.format(customer.title(), project.title()),
            'is_private': True,
            'fork_policy': 'no_forks',
        }

        # Create the repository
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

        repo_name = response['name']
        repo_full_name = response['full_name']
        url = bb + '/2.0/repositories/{0}/branch-restrictions/'.format(
            repo_full_name,
        )

        # Only allow administrators to push to master branch
        data = {
            'groups': [{
                'owner': {'username': 'axiacore'},
                'slug': 'administrators',
            }],
            'kind': 'push',
            'pattern': 'master',
        }
        response = requests.post(
            url,
            data=json.dumps(data),
            headers={'Content-Type': 'application/json'},
            auth=(settings.BITBUCKET_USER, settings.BITBUCKET_PASS),
        )

        # Prevent deletion of the master branch
        data = {
            'kind': 'delete',
            'pattern': 'master',
        }
        response = requests.post(
            url,
            data=json.dumps(data),
            headers={'Content-Type': 'application/json'},
            auth=(settings.BITBUCKET_USER, settings.BITBUCKET_PASS),
        )

        # Prevent force rewrite of the master branch
        data = {
            'kind': 'force',
            'pattern': 'master',
        }
        response = requests.post(
            url,
            data=json.dumps(data),
            headers={'Content-Type': 'application/json'},
            auth=(settings.BITBUCKET_USER, settings.BITBUCKET_PASS),
        )

        # Add the deployment keys
        gh = 'https://raw.githubusercontent.com'
        key_url = gh + '/AxiaCore/public-keys/master/development_keys'
        url = bb + '/1.0/repositories/{0}/deploy-keys/'.format(
            repo_full_name,
        )
        for key in requests.get(key_url).content.splitlines():
            response = requests.post(
                url,
                data={'key': key},
                auth=(settings.BITBUCKET_USER, settings.BITBUCKET_PASS),
            )

        # Add the jenkins hook
        jk = 'https://jenkins.axiacode.com/git/notifyCommit?url='
        jk_url = jk + 'bitbucket.org:{0}.git'.format(
            repo_full_name,
        )
        url = bb + '/1.0/repositories/{0}/services/'.format(
            repo_full_name,
        )
        response = requests.post(
            url,
            data={
                'type': 'POST',
                'URL': jk_url,
            },
            auth=(settings.BITBUCKET_USER, settings.BITBUCKET_PASS),
        )

        self.reply(
            message=message,
            content='{0} repository was just created for you.'.format(
                repo_name,
            )
        )
        self.say(
            message=message,
            content='Clone URL: git@bitbucket.org:{0}.git'.format(
                repo_full_name,
            )
        )
