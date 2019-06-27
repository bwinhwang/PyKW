#!/usr/bin/env python3
import argparse
from klocwork import KWServer, Project, MetricsStatistics
import xlwt
from xlwt import Workbook
import concurrent.futures
import functools
import asyncio

async def getMetrics(loop, project):
    metrics  = await loop.run_in_executor(None, project.getMetricsTotal)
    return (project, metrics)

def main(server, output):

    #projects = [p for p in server.getProjects() if 'x-report' in p.tags]
    projects = server.getProjects()

    executor = concurrent.futures.ThreadPoolExecutor()
    loop = asyncio.get_event_loop()
    loop.set_default_executor(executor)
     
    futures = []

    for p in projects:
        future = asyncio.ensure_future(getMetrics(loop, p))
        futures.append(future)

    coro = asyncio.wait(futures)
    results = loop.run_until_complete(coro)

    metrics = [r.result() for r in results[0]]
    
    cvs = {}
    # for project, p_metrics  in metrics.items():
        # for tag, metric in p_metrics.items():
            # if tag in cvs.keys():
                # cvs[tag].append({project.name : metric})
            # else:
                # cvs[tag] = [{project.name : metric}]

    for i in metrics:
        for metric in i[1]:
            if metric.tag in cvs.keys():
                cvs[metric.tag].append((i[0].name, metric))
            else:
                cvs[metric.tag] = [(i[0].name, metric)]

    wb = Workbook()
    for k, v in cvs.items():
        sheet = wb.add_sheet(k)
        sheet.write(0, 0, 'project')
        sheet.write(0, 1, 'entries')
        sheet.write(0, 2, 'sum')
        sheet.write(0, 3, 'max')
        sheet.write(0, 4, 'min')
        row = 1
        for i in v:
            stats = i[1]
            sheet.write(row, 0, i[0])
            sheet.write(row, 1, stats.entries)
            sheet.write(row, 2, stats.sum)
            sheet.write(row, 3, stats.max)
            sheet.write(row, 4, stats.min)
            row += 1
    wb.save(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--host', default=None, help='Klocwork host')
    parser.add_argument('-p', '--port', default=None, help='Klocwork port')
    parser.add_argument('-u', '--user', default=None, help="specify whom whill talk to server")
    parser.add_argument('-o', '--output', help='excel output filename', default='metrics.xls')
    args = parser.parse_args()
    s = KWServer(args.host, args.port, args.user, debug=False)
    main(s, args.output)
