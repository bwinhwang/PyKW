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

# validate Python version
if sys.version_info.major != 3:
    print("PyKW requires Python 3")
    sys.exit(1)
elif sys.version_info.minor < 5:
    print("PyKW requires at least Python 3.5")
    sys.exit(1)


class Issue:

    __slots__ = ['id', 'message', 'file', 'method', 'code', 'severity', 'title',
    'severityCode', 'state', 'status', 'taxonomyName', 'url',
    'created', 'owner', '_project']

    def __init__(self, project, issue):
        self.id = issue["id"]
        self.message = issue["message"]
        self.file = issue["file"]
        self.method = issue["method"]
        self.code = issue["code"]
        self.severity = issue["severity"]
        self.title = issue['title']
        self.severityCode = issue["severityCode"]
        self.state = issue["state"]
        self.status = issue["status"]
        self.taxonomyName = issue["taxonomyName"]
        self.url = issue["url"]
        self.created = time.ctime(issue["dateOriginated"]/1000)
        self.owner = issue["owner"]
        self._project = project

    def __str__(self):
        return 'id: {0}|severity: {1}|state: {2}'.format(self.id, self.severity, self.state)

    def __repr__(self):
        return str(self.id)

    def __lt__(self, other):
        return self.id < self.id

    def getDetails(self):

        data = {'action': 'issue_details', 'id': self.id}
        return self._project.getItems(**data)[0]

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
        
        return self._project.setItems(**data)


class Metric:
    def __init__(self, project, metric):
        self.file = metric["filePath"]
        self.entity = metric["entity"]
        self.entity_id = metric['entity_id']
        self.tag = metric["tag"]
        self.value = metric["metricValue"]

    def __str__(self):
        return self.tag + '  ' + str(self.value) + '  ' + self.file

    def __lt__(self, other):
        return self.tag < other.tag


class MetricsStatistics:
    def __init__(self, project, statistics):
        self.tag = statistics['tag']
        self.sum = statistics['sum']
        self.max = statistics['max']
        self.min = statistics['min']
        self.entries = statistics['entries']

    def __str__(self):
        return self.tag

    def __repr__(self):
        return self.tag

    def __lt__(self, other):
        return self.tag < other.tag

    def __eq__(self, other):
        return self.tag == other.tag


class View:

    def __init__(self, project, view):
        self.project = project
        self.name = view['name']
        self.creator = view['creator']
        self.id = view['id']
        self.query = view['query']
        self.is_public = view['is_public']
        self.tags = view['tags'] if 'tags' in view.keys() in view else None

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def getIssues(self, query=None):
        '''query='state:New,Existing'''
        params = {'view': self.name}
        if query:
            params.update({'query': query})

        return self.project.getIssues(**params)

    def getAllIssues(self):
        return self.getIssues(query="state:New,Existing,Fixed")

    def getNewIssues(self):
        return self.getIssues(query="state:New")

    def update(self):

        data = {'action': 'update_view', 'name': self.name,
                'query': self.query, 'is_public': self.is_public}
        if self.tags:
            data.update({'tags', self.tags})

        return self.project.setItems(**data)


class Build:
    def __init__(self, project, build):
        self._project = project
        self.id = build['id']
        self.name = build['name']
        self.date = build['date']
        self.keepit = build['keepit']
        self.created = time.ctime(self.date/1000)

    def __str__(self):
        return 'id:{0} created on {1}'.format(self.id, self.created)

    def __repr__(self):
        return self.name

    def __lt__(self, other):
        return self.id < other.id

    def getDetails(self):
        return self._project.getConfiguration(build=self.name)[0]

    def getIssues(self, query=None):
        build_query = "build:{}".format(self.name)
        if query:
            build_query = ' '.join([build_query, query])

        return self._project.getIssues(query=build_query)

    def getNewIssues(self):
        return self.getIssues(query="state:New")


class Module:
    def __init__(self, project, module):
        self.name = module['name']
        self.paths = module['paths']

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def addPath(self, path):
        if path not in self.paths:
            self.paths.append(path)

    def removePath(self, path):
        if path in self.paths:
            self.paths.remove(path)


class Project:

    def __init__(self, server, project):
        self.server = server
        self.name = project['name']
        self.id = project['id']
        self.description = project['description']
        self.creator = project['creator']
        self.tags = project['tags'] if 'tags' in project.keys() else []
        self._views = []
        self._modules = []
        self._builds = []

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

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

    def update(self, newname=None, description=None, tags=None,
            auto_delete_builds=None, auto_delete_threshold=None):

        data = {'action': 'update_project'}
        if newname:
            data.update({'newname': newname})
        if description:
            data.update({'description': description})
        if tags:
            data.update({'tags': tags})
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

    def getIssues(self, view=None, query=None, limit=None):

        data = {'action': 'search'}
        if view:
            data.update({'view': view})
        if query:
            data.update({'query': query})
        if limit:
            data.update({'limit': limit})

        return self.getItems(self._issue_from_json, **data)

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

    def getBuilds(self, force=False):

        if not force and self._builds:
            return self._builds

        data = {'action': 'builds'}

        self._builds = self.getItems(self._build_from_json, **data)
        return self._builds

    def getBuild(self, name, force=False):

        if not self._builds and not force:
            self.getBuilds(force)

        for build in self._builds:
            if name == build.name:
                return build

        return None

    def getViews(self, force=False):

        if not force and self._views:
            return self._views

        data = {'action': 'views'}
        self._views = self.getItems(self._view_from_json, **data)
        return self._views

    def getView(self, name, force=False):

        if not self._views or force:
            self.getViews(force)

        for view in self._views:
            if name == view.name:
                return view

        return None

    def createView(self, view):
        pass

    def updateView(self, view):
        if self == view.project:
            view.update()

    def getModules(self, force=False):

        if not force and self._modules:
            return self._modules

        data = {'action': 'modules'}
        self._modules = self.getItems(self._module_from_json, **data)
        return self._modules

    def getModule(self, name, force=False):
        if not self._modules or force:
            self.getModules(force)

        for module in self._modules:
            if module.name == name:
                return module

        return None

    def createModule(self, module):
        pass

    def updateModule(self, module):
        pass

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


class User:
    def __init__(self, user):
        self.name = user['name']
        self.readonly = user['readonly']
        self.roles = user['roles']
        self.groups = user['groups']

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name 

    def getProjectsAsAdmin(self):

        return [p['projectId'] for p in self.roles if p['name'] == 'Project admin']


class KWServer:
    def __init__(self, host=None, port=None, user=None,  debug=False):
        self._host = host
        self._port = port
        self._user = user
        self._token = self._gettoken(host, port, user)
        self._projects = []
        self._users = []
        self._version = None
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
        if not self._version:
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

    def getUsers(self, force=None):

        if not force and self._users:
            return self._users

        data = {'action': 'users'}
        self._users = self.getItems(KWServer.user_from_json, **data)[1]

        return self._users

    def getProjects(self, force=False):
        
        if not force and self._projects:
            return self._projects

        data = {'action': 'projects'}
        self._projects = self.getItems(self._project_from_json, **data)[1]

        return self._projects

    # def getSummary(self):
        # size = len(self.getProjects())

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
