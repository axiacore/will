#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: AxiaCore S.A.S. http://axiacore.com
from will import settings
from will.plugin import WillPlugin
from will.decorators import respond_to, require_settings

import json
import requests


class BitbucketPlugin(WillPlugin):
    @require_settings('BITBUCKET_API_KEY', 'BITBUCKET_TEAM', 'JENKINS_URL')
    @respond_to('^create repo (?P<customer>[\w-]+) (?P<project>[\w-]+)$')
    def create_repository(self, message, customer, project):
        """
        create repo ___ ___: Create a new repository for a customer and a project
        """
        self.say(
            message=message,
            content="I'm creating a new repo. Hang in there tiger...",
        )

        bb = 'https://api.bitbucket.org'
        url = bb + '/2.0/repositories/{0}/{1}/'.format(
            settings.BITBUCKET_TEAM,
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
            headers={'Autorization': settings.BITBUCKET_API_KEY},
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
            headers={
                'Autorization': settings.BITBUCKET_API_KEY,
                'Content-Type': 'application/json',
            },
        )

        # Prevent deletion of the master branch
        data = {
            'kind': 'delete',
            'pattern': 'master',
        }
        response = requests.post(
            url,
            data=json.dumps(data),
            headers={
                'Autorization': settings.BITBUCKET_API_KEY,
                'Content-Type': 'application/json',
            },
        )

        # Prevent force rewrite of the master branch
        data = {
            'kind': 'force',
            'pattern': 'master',
        }
        response = requests.post(
            url,
            data=json.dumps(data),
            headers={
                'Autorization': settings.BITBUCKET_API_KEY,
                'Content-Type': 'application/json',
            },
        )

        # Add the jenkins hook
        jk_url = '{0}git/notifyCommit?url=bitbucket.org:{1}.git'.format(
            settings.JENKINS_URL,
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
            headers={'Autorization': settings.BITBUCKET_API_KEY},
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
