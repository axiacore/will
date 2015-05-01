#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: AxiaCore S.A.S. http://axiacore.com
from will import settings
from will.plugin import WillPlugin
from will.decorators import respond_to, require_settings

import requests


class BitbucketPlugin(WillPlugin):

    @require_settings('BITBUCKET_USER', 'BITBUCKET_PASS')
    @respond_to('^create repo (?P<customer>[\w]+) (?P<project>[\w]+)$')
    def create_repository(self, message, customer, project):
        """
        Create a new repository: create repo Google Billing
        """
        self.say(
            message=message,
            content="I'm creating a new repo. Hang in there tiger...",
        )

        team = 'axiacore'
        bb = 'https://api.bitbucket.org'
        slug = '{0}-{1}'.format(customer.lower(), project.lower())
        name = '{0} - {1}'.format(customer.title(), project.title())
        url = bb + '/2.0/repositories/{0}/{1}'.format(
            team,
            slug,
        )
        data = {
            'scm': 'git',
            'name': name,
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

        repo_slug = response['slug']
        repo_name = response['name']
        url = bb + '/2.0/repositories/{0}/{1}/branch-restrictions'.format(
            team,
            repo_slug,
        )

        # TODO: needs the push permission set to admins

        # Prevent deletion of the master branch
        response = requests.post(
            url,
            data={'kind': 'delete', 'pattern': 'master'},
            auth=(settings.BITBUCKET_USER, settings.BITBUCKET_PASS),
        )

        # Prevent force rewrite of the master branch
        response = requests.post(
            url,
            data={'kind': 'force', 'pattern': 'master'},
            auth=(settings.BITBUCKET_USER, settings.BITBUCKET_PASS),
        )

        # Add the deployment keys
        gh = 'https://raw.githubusercontent.com'
        key_url = gh + '/AxiaCore/public-keys/master/development_keys'
        url = bb + '/1.0/repositories/{0}/{1}/deploy-keys'.format(
            team,
            repo_slug,
        )
        for key in requests.get(key_url).content.splitlines():
            response = requests.post(
                url,
                data={'key': key},
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
            content='Clone URL: git@bitbucket.org:{0}/{1}.git'.format(
                team,
                repo_slug,
            )
        )
