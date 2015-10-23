#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Author: AxiaCore S.A.S. http://axiacore.com
import time

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
    @respond_to('^jenkins jobs$')
    def jenkins_list(self, message):
        """
        Get a list of available jenkins jobs: jenkins jobs
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

    @require_settings('JENKINS_USER', 'JENKINS_TOKEN')
    @respond_to('^jenkins build (?P<label>[-\w]+)$')
    def jenkins_build(self, message, label):
        """
        Build a jenkins job: jenkins build axiacore-website-testing
        """
        self.say(
            message=message,
            content="I'm building a jenkins job. Hang in there bro...",
        )

        jenkins_list = self.load('jenkins_list', {})

        if label not in jenkins_list:
            return self.__return_error(
                message=message,
                content='Job %s does not exist' % label,
            )

        response = requests.post(
            jenkins_list[label]['url'] + 'build',
            auth=(settings.JENKINS_USER, settings.JENKINS_TOKEN),
            verify=False,
        )
        if response.ok:
            job = jenkins_list[label]['name']
            self.reply(
                message=message,
                content='%s is now building.' % job,
                color='yellow',
            )

            polling_url = response.headers['Location']
            while True:
                response = requests.post(
                    polling_url,
                    auth=(settings.JENKINS_USER, settings.JENKINS_TOKEN),
                    verify=False,
                )
                if response.ok and response.json()['task']['color']:
                    color = response.json()['task']['color']
                    if color.endswith('_anime'):
                        time.sleep(2)
                    elif color == 'blue':
                        self.reply(
                            message=message,
                            content='%s build success. %s' % (
                                job,
                                response.json()['executable']['url'],
                            ),
                            color='green',
                            notify=True,
                        )
                        return
                    elif color == 'red':
                        self.reply(
                            message=message,
                            content='%s build failed. %s' % (
                                job,
                                response.json()['executable']['url'],
                            ),
                            color='red',
                            notify=True,
                        )
                        return
                    else:
                        return self.__return_error(
                            message=message,
                            content='Status %s not recognized' % color,
                        )
                else:
                    return self.__return_error(
                        message=message,
                        content='Cannot get build result.',
                    )
