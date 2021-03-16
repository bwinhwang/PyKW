#
# Copyright 2019 bwinhwang@gmail.com
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import json
import re
import os
import socket
import argparse
import time
import sys
import urllib.request
import urllib.parse
import urllib
from collections import namedtuple
from functools import partial


__author__ = "bwinhwang@gmail.com"
__all__ = ['KWServer', 'Project']


# validate Python version
if sys.version_info.major != 3:
    print("PyKW requires Python 3")
    sys.exit(1)
elif sys.version_info.minor < 7:
    print("PyKW requires at least Python 3.7")
    sys.exit(1)


class Utils:
    @staticmethod
    def toString(param):
        if isinstance(param, list) or isinstance(param, tuple):
            new = ','.join(map(str, param))
        else:
            new = str(param)
        return new

_User = namedtuple('User', ['name', 'readonly', 'roles', 'groups'])

_Issue = namedtuple("Issue", ['id', 'message', 'file',
    'method', 'code', 'severity', 'title', 'severityCode', 'state', 'status',
    'taxonomyName', 'url', 'owner','supportLevel','supportLevelCode', 'dateOriginated',"issueIds"])

_IssueDetails = namedtuple("IssueDetails", ['id', 'code', 'name', 'location', 'build',
    'severity', 'owner', 'state', 'status', 'history'], defaults=[''])

_Metric = namedtuple("Metric", ['filePath', 'entity', 'entity_id', 'tag', 'metricValue'],
        defaults=[''])

_MetricsStatistics = namedtuple("MetricsStatistics",['tag', 'sum', 'min', 'max', 'entries'],
        defaults=[''])

_View = namedtuple("View", ['name', 'creator', 'id', 'query', 'is_public', 'tags'], defaults=[''])

_Build = namedtuple("Build",  ['id', 'name', 'date', 'keepit'])

_Module = namedtuple("Module", ['paths', 'name'])

_Project = namedtuple('Project',  ['server', 'name', 'id', 'creator', 'description', 'tags'],
            defaults = ['',''])

def _item_from_json(_object, json_object):
    return _object(**json_object)

class Project(_Project):

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return self.name < other.name

    def __repr__(self):
        return self.name

    def getItems(self, json_hook=None, **kwargs):

        kwargs.update({'project': self.name})
        return self.server.getItems(json_hook, **kwargs)[1]

    def setItems(self, **kwargs):

        kwargs.update({'project': self.name})
        return self.server.setItems(**kwargs)

    def delete(self):
        data = {'action': 'delete_project', 'name': self.name}
        return self.setItems(**data)

    def update(self, newname=None, description=None, tags=None,
            auto_delete_builds=None, auto_delete_threshold=None):

        data = {'action': 'update_project', 'name': self.name}
        if newname:
            data.update({'newname': newname})
        if description:
            data.update({'description': description})
        if tags:
            data.update({'tags': Utils.toString(tags)})
        if auto_delete_builds:
            data.update({'auto_delete_builds': auto_delete_threshold})
        if auto_delete_threshold:
            data.update({'auto_delete_threshold': auto_delete_threshold})

        return self.setItems(**data)

    #TODO
    def getChurnsReport(self, view=None, component=None):
        data = {'action': 'fchurns', 'project': self.name}

        if view:
            data.update({'view': view})

        return self.getItems(**data)

    def getConfiguration(self, build=None):
        data = {'action': 'project_configuration'}

        if build:
            data.update({'build': build})

        return self.getItems(**data)

    def getTaxonomies(self):
        data = {'action': 'taxonomies'}
        return self.getItems(**data)

    def search(self, view=None, build=None, query=None, limit=None):

        data = {'action': 'search'}
        if view:
            if isinstance(view, _View):
                data.update({'view': view.name})
            else:
                data.update({'view': view})
        if build:
            if isinstance(build, _Build):
                data.update({'buid': build.name})
            else:
                data.update({'build': build})

        if query:
            data.update({'query': query})
        if limit:
            data.update({'limit': limit})

        return self.getItems(partial(_item_from_json, _Issue), **data)

    def getIssues(self, query='state:New,Existing'):

        return self.search(query=query)

    def getAllIssues(self):
        return self.getIssues(query="state:New,Existing,Fixed")

    def getNewIssues(self):
        return self.getIssues(query="state:New")

    def getIssueDetails(self, issue):
        data = {'action': 'issue_details'}
        data.update({'id': issue.id})

        return self.getItems(partial(_item_from_json, _IssueDetails), **data)

    def getMetrics(self, view=None, query=None, limit=None, aggregate=None):
        """
        return results by query
        """
        data = {'action': 'metrics'}
        if view:
            if isinstance(view, _View):
                data.update({'view': view.name})
            else:
                data.update({'view': view})
        if query:
            data.update({'query': query})
        if limit:
            data.update({'limit': limit})
        if aggregate:
            data.update({'aggregate': aggregate})

        return self.getItems(partial(_item_from_json, _Metric), **data)

    def getMetricsTotal(self, query=None, view=None):
        """
        return the whole aggregated metrics
        """
        data = {'action': 'metrics', 'aggregate': 'True'}
        if query:
            data.update({'query': query})
        if view:
            data.update({'view': view})

        return self.getItems(partial(_item_from_json, _MetricsStatistics), **data)

    def getBuilds(self):
        try:
            return self._builds
        except AttributeError:
            data = {'action': 'builds'}

            self._builds = self.getItems(partial(_item_from_json, _Build), **data)
        return self._builds

    def getBuild(self, name):
        for build in self.getBuilds():
            if name == build.name:
                return build
        return None

    def getViews(self):
        try:
            return self._views
        except AttributeError:
            data = {'action': 'views'}
            self._views = self.getItems(partial(_item_from_json, _View), **data)
        return self._views

    def getView(self, name):
        for view in self.getViews():
            if name == view.name:
                return view
        return None

    def getModules(self):
        try:
            return self._modules
        except AttributeError:
            data = {'action': 'modules'}
            self._modules = self.getItems(partial(_item_from_json, _Module), **data)
        return self._modules

    def getModule(self, name):
        for module in self.getModules():
            if module.name == name:
                return module
        return None

    def getDefectsTypes(self):

        data = {'action': 'defect_types'}
        return self.getItems(**data)

    def getServer(self):
        return self.server

    def doCreation(self):
        pass

    def doUpdate(self, item):
        pass

    def doDelete(self):
        pass



class KWServer:
    def __init__(self, host=None, port=None, user=None,  debug=False):
        self._host = host
        self._port = port
        self._user = user
        self._token = self._gettoken(host, port, user)
        self._debug = debug

    def __str__(self):
        return "Login as {0} at Klocwork server({3}) http://{1}:{2}".format(
                self._user, self._host, self._port, self._getVersion())

    def _user_from_json(self, json_object):
        if 'readonly' in json_object.keys():
            return _User(**json_object)
        else:
            return json_object

    def _project_from_json(self, json_object):
        return Project(server = self, **json_object)

    def _gettoken(self, host, port, user):
        ltoken_file = os.path.normpath(os.path.expanduser("~/.klocwork/ltoken"))
        found_token = None
        with open(ltoken_file) as f:
            for line in f:
                rd = line.strip().split(';')
                regex = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
                result_rd = regex.match(rd[0])
                if not result_rd:
                    rd[0] = socket.gethostbyname(rd[0])
                if host:
                    result_host = regex.match(str(host))
                    if not result_host:
                        result_host = socket.gethostbyname(str(host))
                    if result_host == rd[0]:
                        found_token = rd[3]
                else:
                    self._host = rd[0]
                    found_token = rd[3]

                if port and str(port) == rd[1]:
                    found_token = rd[3]
                else:
                    self._port = rd[1]

                if user and rd[2] == user:
                    found_token = rd[3]
                else:
                    self._user = rd[2]

                if found_token:
                    break

        if not found_token:
            raise Exception('No valid token found! Use kwauth to login first!')
        return found_token

    def _getVersion(self):
        try:
            return self._version
        except AttributeError:
            versions = json.loads(self.getUrlRsp({'action': 'version'}).read().decode('utf-8'))
            self._version = versions['majorVersion']+'.'+versions['minorVersion']
        return self._version

    def getUrlRsp(self, data):
        url = "http://{0}:{1}/review/api".format(self._host, self._port)
        base = {'user': self._user, 'ltoken': self._token}
        base.update(data)

        if self._debug:
            print(url)
            print(json.dumps(base, sort_keys=True, indent=2))

        req = urllib.request.Request(url, urllib.parse.urlencode(base).encode("utf-8"))

        rsp = urllib.request.urlopen(req)

        if self._debug:
            print(rsp.status)
            print(rsp.msg)
            print(json.dumps(rsp.getheaders(), sort_keys=True, indent=2))

        return rsp

    def getItems(self, json_hook=None, **kwargs):

        url = "http://{0}:{1}/review/api".format(self._host, self._port)
        kwargs.update({'user': self._user, 'ltoken': self._token})

        if self._debug:
            print(url)
            print("json_hook =", json_hook)
            print(json.dumps(kwargs, sort_keys=True, indent=2))

        req = urllib.request.Request(url, urllib.parse.urlencode(kwargs).encode("utf-8"))
        items = []
        result = False
        exception = None
        try:
            rsp = urllib.request.urlopen(req)
            if rsp.status == 200:
                for line in rsp:
                    items.append(json.loads(line.decode('utf-8'), object_hook=json_hook))
            if self._debug:
                print(rsp.status)
                print(rsp.msg)
                #print(json.dumps(rsp.getheaders(), sort_keys=True, indent=2))

        except urllib.error.HTTPError as e:
            #TODO
            if self._debug:
                print(e)
            exception = e

        return (result, items, exception)

    def setItems(self, **kwargs):

        url = "http://{0}:{1}/review/api".format(self._host, self._port)
        kwargs.update({'user': self._user, 'ltoken': self._token})

        if self._debug:
            print(url)
            print(json.dumps(kwargs, sort_keys=True, indent=2))

        req = urllib.request.Request(url, urllib.parse.urlencode(kwargs).encode("utf-8"))
        exception = None
        result = False
        try:
            rsp = urllib.request.urlopen(req)
            if rsp.status == 200:
                result = True

            if self._debug:
                print(rsp.status)
                print(rsp.msg)
                #print(json.dumps(rsp.getheaders(), sort_keys=True, indent=2))

        except urllib.error.HTTPError as e:
            #TODO
            if self._debug:
                print(e)
            exception = e

        return (result, exception)

    def getUsers(self):
        try:
            return self._users
        except AttributeError:
            data = {'action': 'users'}
            self._users = self.getItems(self._user_from_json, **data)[1]

        return self._users

    def getProjects(self):
        try:
            return self._projects
        except AttributeError:
            data = {'action': 'projects'}
            self._projects = self.getItems(self._project_from_json, **data)[1]
        return self._projects

    def getProject(self, name):

        for project in self.getProjects():
            if name == project.name:
                return project

        return None


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--host', help='Klocwork host')
    parser.add_argument('-p', '--port', help='Klocwork port')
    parser.add_argument('-u', '--user', help="specify whom will talk to server")
    args = parser.parse_args()

    print(KWServer(args.host, args.port, args.user))
