#!/usr/bin/env python3
from xml.sax.saxutils import escape
import sys, os.path, time, argparse, sys, os, socket, re
import time
from Klocwork import KWServer


def generateXML(output, issues):
    with open(output, 'w+') as file:
        file.write("<?xml version=\"1.0\" encoding=\"UTF-8\" ?><errorList xmlns=\"http://www.klocwork.com/inForce/report/1.0\">")
        if issues:
            for issue in issues:
                file.write("<problem>\n")
                file.write("<problemID>" + issue.id + "</problemID>\n")
                file.write("<file>" + issue.file + "</file>\n")
                file.write("<method>" + issue.method + "</method>\n")
                file.write("<code>" + issue.code + "</code>\n")
                file.write("<message>" + issue.message + "</message>\n")
                file.write("<citingStatus>" + issue.status + "</citingStatus>\n")
                file.write("<state>" + issue.state + "</state>\n")
                file.write("<owner>" + issue.owner + "</owner>\n")
                file.write("<severity>" + issue.severity + "</severity>\n")
                file.write("<severitylevel>" + str(issue.severityCode) + "</severitylevel>\n")
                file.write("<displayAs>" + issue.severity + "</displayAs>\n")
                file.write("<taxonomies>\n")
                file.write("<taxonomy name=\"" + issue.taxonomyName + "\" metaInf=\"\" />\n")
                file.write("</taxonomies>\n")
                file.write("<url>" + issue.url + "</url>\n")
                file.write("</problem>\n")
        file.write("</errorList>")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--host', default='highserver', help='Klocwork host')
    parser.add_argument('-p', '--port', default=8080, help='Klocwork port')
    parser.add_argument('-c', '--project', required=True, help='Klocwork project')
    parser.add_argument('-o', '--output', help='XML output filename', default='klocwork_result.xml')
    parser.add_argument('-u', '--user', required=False, help='Klocwork user', default='wbh')
    args = parser.parse_args()

    newissues = []
    for issue in KWServer().getProject(args.project).getIssues():
        if issue.state == 'New':
            newissues.append(issue)

    if newissues:
        print("New issues found")

    generateXML(args.output, newissues) 
