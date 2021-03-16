# PyKW

PyKW is a Python wrapper of Klocwork Web API which gives you the ability to organize and manipulate the Klocwork server data, especially helpful to manage hundreds or thousands projects.

## Getting Started
### Prerequisites
* Python3.7 or later

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
	Python 3.8.5 (default, Jan 27 2021, 15:41:15)
	[GCC 9.3.0] on linux
	Type "help", "copyright", "credits" or "license" for more information.
	>>> import klocwork

create the server instance 

	>>> s=klocwork.KWServer()
	>>> print(s)
	Login as wbh at Klocwork server(20.3.0) http://10.70.9.61:8080

get whole projects

	>>> s.getProjects()
	[mqb_sop2_bm_basic-services__common-base__common-base, onlineservices__cns-applications, onlineservices__tsd-onlineservices-webapp-storage, sal__tsd-sal-carplay, ...]
get a special project

	>>> p=s.getProject('mqb_sop2_bm_basic-services__common-base__common-base')

have a look into the project

	>>> p.getViews()
	[*default*, critical, external code, generated code, metrics, misra, porting, zerofindings]
	>>> p.getBuilds()
	[Build(id=115, name='2020-09-11-98', date=1615877561684, keepit=False), Build(id=114, name='2020-09-11-97', date=1615860867501, keepit=False)]
	>>> p.getTaxonomies()
	[{'name': 'C and C++', 'is_custom': False}, {'name': 'C#', 'is_custom': False}, {'name': 'Java', 'is_custom': False}, {'name': 'MISRA Checkers Package', 'is_custom': False}]

search issues

	>>> p.getIssues(query="state:New")
	[...]
 



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
