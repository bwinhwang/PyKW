#!/usr/bin/env python3
import urllib.request
import urllib.parse
import json
import re
import os
import socket
import argparse
import time


class Issue(object):
    '''{'severityCode': 4, 'id': 56640, 'file': 'project_base/1/workspace/jpcc.sds/utils/src/jsoncpp/json_valueiterator.inl', 'state': 'New', 'issueIds': [55732], 'url': 'http://highserver:8080/review/insight-review.html#issuedetails_goto:problemid=56640,project=sds__speech_service__jpcc_sds,searchquery=', 'code': 'MISRA.UMINUS.UNSIGNED', 'status': 'Analyze', 'severity': 'Review', 'owner': 'unowned', 'taxonomyName': 'MISRA C++ 2008', 'title': 'Operand of unary minus is unsigned', 'dateOriginated': 1561389612207, 'method': 'index', 'message': 'Operand of unary minus is unsigned', 'reference': '5-3-2 (C++ 2008 req.)'}'''

    def __init__(self, issue):
        self.id = str(issue["id"])
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

    def __str__(self):
        return self.code + ': ' + self.title


class Metric(object):
    def __init__(self, metric):
        self.file = metric["filePath"]
        self.entity = metric["entity"]
        self.entity_id = metric['entity_id']
        self.tag = metric["tag"]
        self.value = metric["metricValue"]

    def __str__(self):
        return self.tag + '  ' + str(self.value) + '  ' + self.file


class View:

    '''{'creator': 'klocwork', 'is_public': False, 'id': 9, 'query': '-module:"JsonLib"', 'name': 'onlineapplication'}'''
    def __init__(self, project, view):
        self.name = view['name']
        self.creator = view['creator']
        self.id = view['id']
        self.query = view['query']
        self.is_public = view['is_public']
        self.tags = view['tags'] if 'tags' in view.keys() in view else None

    def __str__(self):
        return self.name


class Module:
    def __init__(self, project, view):
        pass


class Project:

    '''{"id":"MASTER_klocwork","name":"MASTER_klocwork","creator":"wbh","description":"the template project"}'''
    def __init__(self, server, project):
        self._server = server
        self.name = project['name']
        self.id = project['id']
        self.description = project['description']
        self.creator = project['creator']
        self._views = []

    def __str__(self):
        return self.name

    @classmethod
    def view_from_json(cls, json_object):
        return View(cls, json_object)

    @classmethod
    def issue_from_json(cls, json_object):
        return Issue(json_object)

    @classmethod
    def metric_from_json(cls, json_object):
        return Metric(json_object)

    def getConfiguration(self):
        data = {'action': 'project_configuration', 'project': self.name}
        req = self._server.getUrlReq(data)
        rsp = urllib.request.urlopen(req)
        configurations = []

        for i in rsp:
            configurations.append(json.loads(i.decode('utf-8')))

        return configurations

    def getTaxonomies(self):
        data = {'action': 'taxonomies', 'project': self.name}
        req = self._server.getUrlReq(data)
        rsp = urllib.request.urlopen(req)
        taxonomies = []

        for i in rsp:
            taxonomies.append(json.loads(i.decode('utf-8')))

        return taxonomies

    def getIssues(self, view='critical', query=None, limit=None):

        data = {'action': 'search', 'project': self.name}
        if view:
            data.update({'view': view})
        if query:
            data.update({'query': query})
        if limit:
            data.update({'limit': limit})

        req = self._server.getUrlReq(data)
        rsp = urllib.request.urlopen(req)
        issues = []
        for i in rsp:
            issues.append(json.loads(i.decode('utf-8'), object_hook=Project.issue_from_json))
        return issues

    def getMetrics(self, view='metrics', query=None, limit=None, aggregate=None):

        data = {'action': 'metrics', 'project': self.name}
        if view:
            data.update({'view': view})
        if query:
            data.update({'query': query})
        if limit:
            data.update({'limit': limit})
        if aggregate:
            data.update({'aggregate': aggregate})

        req = self._server.getUrlReq(data)
        rsp = urllib.request.urlopen(req)
        metrics = []
        for i in rsp:
            metrics.append(json.loads(i.decode('utf-8'), object_hook=Project.metric_from_json))

        return metrics

    def getDefectsTypes(self):

        data = {'action':'defect_types', 'project':self.name}
        req = self._server.getUrlReq(data)
        rsp = urllib.request.urlopen(req)
        defects = []

        for i in rsp:
            defects.append(json.loads(i.decode('utf-8')))

        return defects

    def getClient(self):
        return self._server

    def getViews(self):

        data = {'action': 'views', 'project': self.name}
        req = self._server.getUrlReq(data)
        rsp = urllib.request.urlopen(req)

        self._views = []
        for i in rsp:
            self._views.append(json.loads(i.decode('utf-8'), object_hook=Project.view_from_json))

        return self._views

    def getView(self, name, force=False):

        if not self._views or force:
            self.getViews()

        for view in self._views:
            if name == view['name']:
                return view

        return None

    def createView(self, view):
        pass

    def updateView(self, view):

        if view.name == '*default*':
            print('Any operations on View default are skipped')
            return

        data = {'action': 'update_view', 'project': self.name,
                'name': view.name, 'query': view.query, 'tags': view.tags, 'is_public': view.is_public}

        req = self._server.getUrlReq(data)
        rsp = urllib.request.urlopen(req)

    def createModule(self, module):
        pass

    def updateModule(self, module):
        pass

    def genReport(self, build=None, filterQeury=None, view='critical', x='Category',
            xDrilldown=None, y='Severity', yDrilldown=None, group_issues=None):

        data = {'action': 'report', 'project': self.name}

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

        req = self._server.getUrlReq(data)
        rsp = urllib.request.urlopen(req)

        for i in rsp:
            print(json.loads(i.decode('utf-8')))

    def update(self):
        pass


class KWServer:
    def __init__(self, user='klocwork', host='10.57.69.62', port=8080, debug=False):
        self._user = user
        self._host = host
        self._port = port
        self._token = self._gettoken(host, port, user)
        self._version = self._getVersion()
        self._projects = []
        self._debug = debug
        self.updateProject()

    def __str__(self):
        return "Login as {0} at Klocwork server({3}) http://{1}:{2}".format(
                self._user, self._host, self._port, self._version)

    def _gettoken(self, host, port, user):
        ltoken = os.path.normpath(os.path.expanduser("~/.klocwork/ltoken"))
        ltokenFile = open(ltoken, 'r')
        for r in ltokenFile:
            rd = r.strip().split(';')
            regex = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
            result_rd = regex.match(rd[0])
            result_host = regex.match(host)
            if result_rd != result_host:
                if not result_host:
                    host = socket.gethostbyname(rd[0])
                else:
                    rd[0] = socket.gethostbyname(host)
            if rd[0] == host and rd[1] == str(port) and rd[2] == user:
                ltokenFile.close()
                return rd[3]
        ltokenFile.close()
        raise Exception('No valid token found! Use kwauth to login first!')
        return None

    def _getVersion(self):
        versions = json.loads(self._getUrlRsp({'action': 'version'}).read().decode('utf-8'))
        return versions['majorVersion']+'.'+versions['minorVersion']

    def _getUrlRsp(self, data):
        url = "http://{0}:{1}/review/api".format(self._host, self._port)
        base = {'user': self._user, 'ltoken': self._token}
        base.update(data)
        req = urllib.request.Request(url, urllib.parse.urlencode(base).encode("utf-8"))
        rsp = urllib.request.urlopen(req)

        return rsp

    def getUrlReq(self, data):
        url = "http://{0}:{1}/review/api".format(self._host, self._port)
        base = {'user': self._user, 'ltoken': self._token}
        base.update(data)
        if self._debug:
            print(base)
        req = urllib.request.Request(url, urllib.parse.urlencode(base).encode("utf-8"))

        return req

    def getProjects(self, force_fetch=False):
        if not force_fetch and not self._projects:
            return self._projects

        projects = self._getUrlRsp({'action': 'projects'})
        self._projects = []
        for p in projects:
            p2 = json.loads(p.decode('utf-8'))
            self._projects.append(Project(self, p2))

        return self._projects

    def updateProject(self):
        self.getProjects(True)

    def getProject(self, name):

        for project in self._projects:
            if name == project.name:
                return project

        return None


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--host', default='highserver', help='Klocwork host')
    parser.add_argument('-p', '--port', default=8080, help='Klocwork port')
    parser.add_argument('-u', '--user', help='Name of View', default='critical')
    args = parser.parse_args()

    print(KWServer())
    #server.getProject('sds__speech.service__jpcc-sds').genReport()
