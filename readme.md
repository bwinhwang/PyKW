# PyKW

PyKW is a Python wrapper of Klocwork Web API which gives you the ability to organize and manipulate the Klocwork server data, especially helpful to manage hundreds or thousands projects.

## Getting Started
### Prerequisites
* Python3.5 or later

* Make a sucessful login to the Klocwork server so proper credential is generated in your $HOME/.klocwork directory which will be read by PyKW. 

	```
	kwauth --url http://example:8080
	```

### Installing

Just copy klocwork.py file to your workspace

```
$ cp klocwork.py myworkspace/
```


### How to use
Please start the interpreter from the directory where file 'klocwork.py' exists   

    $ python3
	Python 3.5.2 (default, Nov 23 2017, 16:37:01) 
	[GCC 5.4.0 20160609] on linux
	Type "help", "copyright", "credits" or "license" for more information.
	>>> import klocwork

create the server instance 

	>>> s=klocwork.KWServer()
	>>> print(s)
	Login as wbh at Klocwork server(19.1.0) http://10.57.69.62:8080

get whole projects

	>>> s.getProjects()
	[onlineservices__cns-applications, onlineservices__tsd-onlineservices-webapp-storage, sal__tsd-sal-carplay, ...]
get a special project

	>>> p=s.getProject('onlineservices__cns-applications')

have a look into the project

	>>> p.getViews()
	[*default*, critical, external code, generated code, metrics, misra, porting, zerofindings]
	>>> p.getBuilds()
	[2019-07-17-26, 2019-07-11-25, 2019-07-08-23]
	>>> p.getTaxonomies()
	[{'name': 'C and C++', 'is_custom': False}, {'name': 'C#', 'is_custom': False}, {'name': 'Java', 'is_custom': False}, {'name': 'MISRA Checkers Package', 'is_custom': False}]
	>>> p.getModules()
	[*default*, external_code, generated_code, test_code]

have a look into a build

	>>> b=p.getBuild('2019-07-17-26')
	>>> b.getDetails()
	{'taxonomies': 'C and C++, MISRA Checkers Package, Metrics', 'build': '2019-07-17-26', 'linesOfCode': '49741', 'numberOfEntities': '141956', 'creationDate': 'Wed Jul 17 23:42:46 HKT 2019', 'version': '19.1.0.57', 'linesOfComments': '8339', 'numberOfClasses': '24178', 'numberOfFunctions': '11379', 'cFilesAnalyzed': '349', 'numberOfFiles': '1638', 'systemFilesAnalyzed': '1289'}

get the list of new issues found in this build

	>>> b.getIssues(query="state:New")
	[44995, 46736, 46737, 46738, 46739, 46740, 46741, 46742, 46743, 46744, ...]

give a summary of issues whose severity is 'critical'

	>>> for i in b.getIssues(query='severity:Critical'):
	...   print(i.getDetails())
	... 
	{'code': 'ABV.GENERAL', 'build': '2019-07-17-26', 'severity': 'Critical (1)', 'name': 'Buffer Overflow - Array Index Out of Bounds', 'status': 'Analyze', 'state': 'Existing', 'location': 'project_base/1/workspace/tsd.onlineservices.applications/src/PersistentConnectionMessage/MqttDispatcher/MqttHeaderBodyPackaging.cpp', 'id': '27593', 'owner': 'unowned'}
	>>>
 



## Examples
### kw_samples1.py
this sample will list the new issues number in the latest build

	$ ./kw_sample1.py 
	hmi__tsd-dsi-cpp                                                               73062 
	basic-services__rsi-library__tsd-vw-rsi-viwi-common                            45067 
	basic-services__rsi-library__tsd-vw-rsi-viwi-client                            10199 
	vehicle-connectivity__automotive-ethernet__tsd-ethernet-mid.1                   8519 
	basic-services__common-base__common-base                                        8243 
	system__tsd-common                                                              7087 
	phone__bt-mediacontroller__tsd-bt-media                                         6536 
	
***More lines are collapsed***

### kw_samples2.py
this sample will generate a cvs file includes all metrics statistics report for whole projects

## License

This project is licensed under the [Apache License Version 2.0](http://www.apache.org/licenses/LICENSE-2.0)
