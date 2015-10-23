#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: AxiaCore S.A.S. http://axiacore.com
from will import settings
from will.plugin import WillPlugin
from will.decorators import respond_to, rendered_template, require_settings

import requests


class JenkinsPlugin(WillPlugin):

    def __return_error(self, message, content):
        """
        Returns an error to the user
        """
        self.reply(message=message, content=content, color='red', notify=True)
        return

    @require_settings('JENKINS_URL', 'JENKINS_USER', 'JENKINS_TOKEN')
    @respond_to('^jenkins list$')
    def jenkins_list(self, message):
        """
        Get a list of available jenkins jobs: jenkins list
        """
        self.say(
            message=message,
            content="I'm getting the jenkins jobs. Hang in there tiger...",
        )

        response = requests.get(
            settings.JENKINS_URL + 'view/All/api/json',
            auth=(settings.JENKINS_USER, settings.JENKINS_TOKEN),
            verify=False,
        )

        if not response.ok:
            return self.__return_error(
                message=message,
                content='Could not connect to jenkins',
            )

        jenkins_list = {}
        for job in response.json()['jobs']:
            if job['color'] != 'disabled':
                slug = job['name'].lower().replace(' ', '')
                jenkins_list[slug] = {
                    'name': job['name'],
                    'url': job['url'],
                }

        self.save('jenkins_list', jenkins_list)

        self.say(
            message=message,
            content=rendered_template('jenkins_list.html', {
                'jenkins_list': jenkins_list,
            }),
            html=True,
            notify=True,
        )
