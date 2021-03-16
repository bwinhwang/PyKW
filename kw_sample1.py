#!/usr/bin/env python3
import argparse
from klocwork import KWServer, Project
import concurrent.futures
import functools
import asyncio


async def getMetrics(loop, project):
    issues = await loop.run_in_executor(None, project.getIssues)
    return (project, issues)

def main(server):

    projects = [p for p in server.getProjects() if 'x-report' in p.tags]
    #projects = server.getProjects()
    metrics = []

    executor = concurrent.futures.ThreadPoolExecutor()
    loop = asyncio.get_event_loop()
    loop.set_default_executor(executor)

    futures = []

    for p in projects:
        future = asyncio.ensure_future(getMetrics(loop, p))
        futures.append(future)

    coro = asyncio.wait(futures)
    results = loop.run_until_complete(coro)

    for r in results[0]:
        result = r.result()
        if isinstance(result[1], list):
            metrics.append((result[0], len(result[1])))
        else:
            metrics.append((result[0], None))

    metrics.sort(key=lambda i: i[1] if i[1] != None else -1, reverse=True)

    for m in metrics:
        print('{name:75} {length:>8} '.format(name=m[0].name, length=str(m[1])))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--host', default=None, help='Klocwork host')
    parser.add_argument('-p', '--port', default=8080, help='Klocwork port')
    parser.add_argument('-u', '--user', default=None, help="specify whom whill talk to server")
    args = parser.parse_args()
    s = KWServer(args.host, args.port, args.user, debug=False)
    main(s)
