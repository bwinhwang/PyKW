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

__author__ = "bwinhwang@gmail.com"
__all__ = ['Build', 'Issue', 'KWServer', 'Metric', 'MetricsStatistics',
        'Project', 'User', 'View', ]


# validate Python version
if sys.version_info.major != 3:
    print("PyKW requires Python 3")
    sys.exit(1)
elif sys.version_info.minor < 5:
    print("PyKW requires at least Python 3.5")
    sys.exit(1)


class Utils:

    @staticmethod
    def toString(param):
        if isinstance(param, list) or isinstance(param, tuple):
            new = ','.join(map(str, param))
        else:
            new = str(param)

        return new


class BaseObject:

    def __str__(self):

        if hasattr(self, 'name'):
            return self.name
        if hasattr(self, 'id'):
            return str(self.id)
        if hasattr(self, 'tag'):
            return str(self.tag)

        return self.__class__.__name__

    def __repr__(self):
        return self.__str__()

    def __getattr__(self, attr):
        ''' tags if quite common in various objects'''
        if attr == 'tags':
            return []
        else:
            raise AttributeError(attr)


class JSONObject(BaseObject):

    def __init__(self, dict):
        vars(self).update(dict)


class User(JSONObject):

    __all__ = ['name', 'readonly', 'roles', 'groups']

    def getProjectsAsAdmin(self):

        return [p['projectId'] for p in self.roles if p['name'] == 'Project admin']


class Issue(JSONObject):

    __all__ = ['id', 'message', 'file', 'method', 'code', 'severity', 'title',
    'severityCode', 'state', 'status', 'taxonomyName', 'url',
    'created', 'owner','dateOriginated', 'project']

    def __init__(self, project, json_object):
        JSONObject.__init__(self, json_object)
        self.created = time.ctime(self.dateOriginated/1000)
        self.project = project

    def __lt__(self, other):
        return self.id < self.id

    def getDetails(self):

        try:
            return self.details
        except AttributeError:
            data = {'action': 'issue_details', 'id': self.id}
            self.details = self.project.getItems(**data)[0]

        return self.details

    def getName(self):
        return self.getDetails()['name']

    def getLocation(self):

        return self.getDetails()['location']

    def getStatus(self):
        return self.status

    def getState(self):

        return self.getDetails()['state']

    def getHistory(self):

        data = self.getDetails()

        if 'history' in data.keys():
            return data['history'][0]['comment']
        else:
            return ''

    def update(self, owner=None, status=None, comment=None, bug_tracker_id=None):

        data = {'action': 'update_status', 'ids': self.id}

        if owner:
            data.update({'owner': owner})
        if status:
            data.update({'status': status})
        if comment:
            data.update({'comment': comment})
        if bug_tracker_id:
            data.update({'bug_tracker_id': bug_tracker_id})

        return self.project.setItems(**data)


class Metric(JSONObject):

    __all__ = ['project', 'filePath', 'entity', 'entity_id', 'tag', 'metricValue']

    def __init__(self, project, json_object):
        JSONObject.__init__(self, json_object)
        self.project = project

    def __lt__(self, other):
        return self.tag < other.tag


class MetricsStatistics(JSONObject):

    __all__ = ['project']

    def __init__(self, project, json_object):
        JSONObject.__init__(self, json_object)
        self.project = project

    def __lt__(self, other):
        return self.tag < other.tag


class View(JSONObject):

    __all__ = ['project', 'name', 'creator', 'id', 'query', 'is_public', 'tags']

    def __init__(self, project, json_object):
        JSONObject.__init__(self, json_object)
        self.project = project

    def getIssues(self, query=None):
        '''query='state:New,Existing'''
        params = {'view': self.name}
        if query:
            params.update({'query': query})

        return self.project.search(**params)

    def getAllIssues(self):
        return self.getIssues(query="state:New,Existing,Fixed")

    def getNewIssues(self):
        return self.getIssues(query="state:New")

    def doDelete(self):
        data = {'action': 'delete_view', 'name': self.name}
        return self.project.setItems(**data)

    def doUpdate(self):
        data = {'action': 'update_view', 'name': self.name,
                'query': self.query, 'is_public': self.is_public}
        if self.tags:
            data.update({'tags', Utils.toString(self.tags)})

        return self.project.setItems(**data)

    def doCreate(self):
        data = {'action': 'update_view', 'name': self.name,
                'query': self.query, 'is_public': self.is_public}
        if self.tags:
            data.update({'tags', Utils.toString(self.tags)})

        return self.project.setItems(**data)


class Build(JSONObject):

    __all__ = ['project', 'id', 'name', 'date', 'keepit', 'created']

    def __init__(self, project, json_object):
        JSONObject.__init__(self, json_object)
        self.project = project
        self.created = time.ctime(self.date/1000)

    def __lt__(self, other):
        return self.id < other.id

    def getDetails(self):
        return self.project.getConfiguration(build=self.name)[0]

    def getIssues(self, query=None):
        build_query = "build:{}".format(self.name)
        if query:
            build_query = ' '.join([build_query, query])

        return self.project.search(query=build_query)

    def getNewIssues(self):
        return self.getIssues(query="state:New")


class Module(JSONObject):

    __all__ = ['paths', 'name']

    def __init__(self, project, json_object):
        JSONObject.__init__(self, json_object)
        self.project = project

    def doCreate(self, **params):
        self._action(action='create_module', **params)

    def doUpdate(self, **params):
        self._action(action='update_module', **params)

    def doDelete(self):
        self._action(action='delete_module')

    def _action(self, **params):
        data = {'name': self.name, 'paths': ','.join(self.paths)}
        data.update(**params)
        self.project.setItems(**data)

    def addPath(self, path):
        if path not in self.paths:
            self.paths.append(path)

    def removePath(self, path):
        if path in self.paths:
            self.paths.remove(path)


class Project(JSONObject):

    __all__ = ['server', 'name', 'id', 'description', 'creator', 'tags']

    def __init__(self, server, json_object):
        JSONObject.__init__(self, json_object)
        self.server = server

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return self.name < other.name

    def _module_from_json(self, json_object):
        return Module(self, json_object)

    def _metric_from_json(self, json_object):
        return Metric(self, json_object)

    def _issue_from_json(self, json_object):
        return Issue(self, json_object)

    def _view_from_json(self, json_object):
        return View(self, json_object)

    def _metricstats_from_json(self, json_object):
        return MetricsStatistics(self, json_object)

    def _build_from_json(self, json_object):
        return Build(self, json_object)

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

    def search(self, view=None, query=None, limit=None):

        data = {'action': 'search'}
        if view:
            data.update({'view': view})
        if query:
            data.update({'query': query})
        if limit:
            data.update({'limit': limit})

        return self.getItems(self._issue_from_json, **data)

    def getIssues(self, view=None, query=None, limit=None):

        return self.search(view, query, limit)

    def updateIssues(self, ids, status=None, comment=None, owner=None, bug_tracker_id=None):
        data = {'action': 'update_status'}
        if type(ids) == str:
            data.update({'ids': ids})
        elif type(ids) == list:
            s = None
            for i in ids:
                s += str(i)+','
            s = s[:-1]
            data.update({'ids': s})
        elif type(ids) == int:
            data.update({'ids': str(ids)})
        else:
            raise Exception('Unkown parameter type')

        if owner:
            data.update({'owner': owner})
        if status:
            data.update({'status': status})
        if comment:
            data.update({'comment': comment})
        if bug_tracker_id:
            data.update({'bug_tracker_id': bug_tracker_id})

        return self.setItems(**data)

    def getIssueDetails(self, id):
        data = {'action': issue_details}
        data.update({'id': id})

        return self.getItems(**data)

    def getMetrics(self, view=None, query=None, limit=None, aggregate=None):

        data = {'action': 'metrics'}
        if view:
            data.update({'view': view})
        if query:
            data.update({'query': query})
        if limit:
            data.update({'limit': limit})
        if aggregate:
            data.update({'aggregate': aggregate})

        return self.getItems(self._metric_from_json, **data)

    def getMetricsTotal(self, view=None):
        data = {'action': 'metrics', 'aggregate': 'True'}
        if view:
            data.update({'view': view})

        return self.getItems(self._metricstats_from_json, **data)

    def getBuilds(self):
        try:
            return self._builds
        except AttributeError:
            data = {'action': 'builds'}
            self._builds = self.getItems(self._build_from_json, **data)
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
            self._views = self.getItems(self._view_from_json, **data)
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
            self._modules = self.getItems(self._module_from_json, **data)
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

    #TODO
    def genReport(self, build=None, filterQeury=None, view=None, x='Category',
            xDrilldown=None, y='Severity', yDrilldown=None, group_issues=None):
        '''
        build
        name of the build you want to focus your report on
        filterQuery
        the filter query you want to set for the report (search criteria are: State, Status, Severity, Module, Owner, Category, Code, Reference)
        view
        the view you want to set for the report
        x
        the value you want to set along the x-axis (options are: Module, Category, Severity, State, Status, Owner, Error Code)
        xDrilldown
        row drill-down item id (default: root item)
        y
        the variable you want to set along the y-axis (options are: Module, Category, Severity, State, Status, Owner, Error Code)
        yDrilldown
        column drill-down item id (default: root item)
        group_issues
        show grouped issues
        '''
        data = {'action': 'report'}

        if build:
            data.update({'build': build})

        if filterQeury:
            data.update({'filterQeury': filterQeury})

        if view:
            data.update({'view': view})

        if x:
            data.update({'x': x})

        if xDrilldown:
            data.update({'xDrilldown': xDrilldown})

        if y:
            data.update({'y': y})

        if yDrilldown:
            data.update({'yDrilldown': yDrilldown})

        if group_issues:
            data.update({'group_issues': group_issues})

        return self.getItems(**data)


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

    @classmethod
    def user_from_json(cls, json_object):
        if 'readonly' in json_object.keys():
            return User(json_object)
        else:
            return json_object

    def _project_from_json(self, json_object):
        return Project(self, json_object)

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
            return self._user
        except AttributeError:
            data = {'action': 'users'}
            self._users = self.getItems(KWServer.user_from_json, **data)[1]

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
