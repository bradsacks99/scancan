![ScanCan](https://github.com/bradsacks99/ScanCan/blob/main/scancan/static/scancan-logo.png)

# An HTTP API for a containerized ClamAV

ScanCan provides a light weight RESTful API for ClamAV (https://docs.clamav.net/) in a container.
## Building the can

### ClamAV Virus defininitions on a mount (recommended)
```commandline
docker build  -t scancan .
docker rm scancan;docker run -it --volume=/pathtoclamvirusdefs:/opt/clamav --volume=/pathtoamountyouwanttoscan:/opt/files -p portyouwant:8080 --name scancan scancan
```
You should then update the virus definitions on the mount using freshclam (https://docs.clamav.net/manual/Usage/SignatureManagement.html#freshclam). ClamAV will pick up the new definitions automatically.

### Running freshcalm on a cron in the container (not recommended)
```commandline
docker build --build-arg basev=cron -t scancan .
docker rm scancan;docker run -it --volume=/pathtoamountyouwanttoscan:/opt/files -p portyouwant:8080 --name scancan scancan
```
*Note* there are issues with this approach:
1. It's not well tested
2. If you are running multiple containers you'll get blocked from downloading at the same time.

# Usage

## ClamAV API documentation is available on:
http://host:hostport/docs

<!-- Generator: Widdershins v4.0.1 -->

<h1 id="scancan">ScanCan v0.1.0</h1>

> Scroll down for code samples, example requests and responses. Select a language for code samples from the tabs above or the mobile navigation menu.

Virus Scanning API for ClamAV

<h1 id="scancan-default">Default</h1>

## GET health

<a id="opIdhealth_health_get"></a>

> Code samples

```shell
# You can also use wget
curl -X GET /health \
  -H 'Accept: application/json'

```

```http
GET /health HTTP/1.1

Accept: application/json

```

```javascript

const headers = {
  'Accept':'application/json'
};

fetch('/health',
{
  method: 'GET',

  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Accept' => 'application/json'
}

result = RestClient.get '/health',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Accept': 'application/json'
}

r = requests.get('/health', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('GET','/health', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/health");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("GET");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("GET", "/health", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`GET /health`

*Health*

GET /health: determine the health of ScanCan
    Returns:
        result (object)

> Example responses

> 200 Response

```json
null
```

<h3 id="health_health_get-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|

<h3 id="health_health_get-responseschema">Response Schema</h3>

<aside class="success">
This operation does not require authentication
</aside>

## POST scanpath

<a id="opIdscan_path_scanpath__path__post"></a>

> Code samples

```shell
# You can also use wget
curl -X POST /scanpath/{path} \
  -H 'Accept: application/json'

```

```http
POST /scanpath/{path} HTTP/1.1

Accept: application/json

```

```javascript

const headers = {
  'Accept':'application/json'
};

fetch('/scanpath/{path}',
{
  method: 'POST',

  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Accept' => 'application/json'
}

result = RestClient.post '/scanpath/{path}',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Accept': 'application/json'
}

r = requests.post('/scanpath/{path}', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('POST','/scanpath/{path}', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/scanpath/{path}");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("POST");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("POST", "/scanpath/{path}", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`POST /scanpath/{path}`

*Scan Path*

POST /scanpath: scan a mounted path with ClamAV
    Parameters:
        path (str): a path
    Returns:
        result (Object)

<h3 id="scan_path_scanpath__path__post-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|path|path|string|true|none|

> Example responses

> 200 Response

```json
null
```

<h3 id="scan_path_scanpath__path__post-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

<h3 id="scan_path_scanpath__path__post-responseschema">Response Schema</h3>

<aside class="success">
This operation does not require authentication
</aside>

## GET scanurl

<a id="opIdscan_url_scanurl__get"></a>

> Code samples

```shell
# You can also use wget
curl -X GET /scanurl/?url=string \
  -H 'Accept: application/json'

```

```http
GET /scanurl/?url=string HTTP/1.1

Accept: application/json

```

```javascript

const headers = {
  'Accept':'application/json'
};

fetch('/scanurl/?url=string',
{
  method: 'GET',

  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Accept' => 'application/json'
}

result = RestClient.get '/scanurl/',
  params: {
  'url' => 'string'
}, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Accept': 'application/json'
}

r = requests.get('/scanurl/', params={
  'url': 'string'
}, headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('GET','/scanurl/', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/scanurl/?url=string");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("GET");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("GET", "/scanurl/", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`GET /scanurl/`

*Scan Url*

GET /scanurl: scan a url with ClamAV
    Parameters:
        url (str): a url
    Returns:
        result (Object)

<h3 id="scan_url_scanurl__get-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|url|query|string|true|none|

> Example responses

> 200 Response

```json
null
```

<h3 id="scan_url_scanurl__get-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

<h3 id="scan_url_scanurl__get-responseschema">Response Schema</h3>

<aside class="success">
This operation does not require authentication
</aside>

## POST scancont

<a id="opIdcont_scan_contscan__path__post"></a>

> Code samples

```shell
# You can also use wget
curl -X POST /contscan/{path} \
  -H 'Accept: application/json'

```

```http
POST /contscan/{path} HTTP/1.1

Accept: application/json

```

```javascript

const headers = {
  'Accept':'application/json'
};

fetch('/contscan/{path}',
{
  method: 'POST',

  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Accept' => 'application/json'
}

result = RestClient.post '/contscan/{path}',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Accept': 'application/json'
}

r = requests.post('/contscan/{path}', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('POST','/contscan/{path}', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/contscan/{path}");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("POST");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("POST", "/contscan/{path}", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`POST /contscan/{path}`

*Cont Scan*

POST /contscan: scan a mounted path with ClamAV, continue if found
    Parameters:
        path (str): a path
    Returns:
        result (Object)

<h3 id="cont_scan_contscan__path__post-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|path|path|string|true|none|

> Example responses

> 200 Response

```json
null
```

<h3 id="cont_scan_contscan__path__post-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

<h3 id="cont_scan_contscan__path__post-responseschema">Response Schema</h3>

<aside class="success">
This operation does not require authentication
</aside>

## POST scanfile (uploaded file)

<a id="opIdscan_upload_file_scanfile_post"></a>

> Code samples

```shell
# You can also use wget
curl -X POST /scanfile \
  -H 'Content-Type: multipart/form-data' \
  -H 'Accept: application/json'

```

```http
POST /scanfile HTTP/1.1

Content-Type: multipart/form-data
Accept: application/json

```

```javascript
const inputBody = '{
  "file": "string"
}';
const headers = {
  'Content-Type':'multipart/form-data',
  'Accept':'application/json'
};

fetch('/scanfile',
{
  method: 'POST',
  body: inputBody,
  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Content-Type' => 'multipart/form-data',
  'Accept' => 'application/json'
}

result = RestClient.post '/scanfile',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Content-Type': 'multipart/form-data',
  'Accept': 'application/json'
}

r = requests.post('/scanfile', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Content-Type' => 'multipart/form-data',
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('POST','/scanfile', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/scanfile");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("POST");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Content-Type": []string{"multipart/form-data"},
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("POST", "/scanfile", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`POST /scanfile`

*Scan Upload File*

POST /scanfile: scan a file stream with ClamAV
    Parameters:
        file (bytes): an uploaded file
    Returns:
        result (Object)

> Body parameter

```yaml
file: string

```

<h3 id="scan_upload_file_scanfile_post-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|body|body|[Body_scan_upload_file_scanfile_post](#schemabody_scan_upload_file_scanfile_post)|true|none|

> Example responses

> 200 Response

```json
null
```

<h3 id="scan_upload_file_scanfile_post-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

<h3 id="scan_upload_file_scanfile_post-responseschema">Response Schema</h3>

<aside class="success">
This operation does not require authentication
</aside>

## GET license

<a id="opIdshow_license_license_get"></a>

> Code samples

```shell
# You can also use wget
curl -X GET /license \
  -H 'Accept: text/plain'

```

```http
GET /license HTTP/1.1

Accept: text/plain

```

```javascript

const headers = {
  'Accept':'text/plain'
};

fetch('/license',
{
  method: 'GET',

  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Accept' => 'text/plain'
}

result = RestClient.get '/license',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Accept': 'text/plain'
}

r = requests.get('/license', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Accept' => 'text/plain',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('GET','/license', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/license");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("GET");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Accept": []string{"text/plain"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("GET", "/license", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`GET /license`

*Show License*

GET /license: view the ScanCan license
    Returns:
        license (string)

> Example responses

> 200 Response

```
"string"
```

<h3 id="show_license_license_get-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|string|

<aside class="success">
This operation does not require authentication
</aside>

# Schemas

<h2 id="tocS_Body_scan_upload_file_scanfile_post">Body_scan_upload_file_scanfile_post</h2>
<!-- backwards compatibility -->
<a id="schemabody_scan_upload_file_scanfile_post"></a>
<a id="schema_Body_scan_upload_file_scanfile_post"></a>
<a id="tocSbody_scan_upload_file_scanfile_post"></a>
<a id="tocsbody_scan_upload_file_scanfile_post"></a>

```json
{
  "file": "string"
}

```

Body_scan_upload_file_scanfile_post

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|file|string(binary)|true|none|none|

<h2 id="tocS_HTTPValidationError">HTTPValidationError</h2>
<!-- backwards compatibility -->
<a id="schemahttpvalidationerror"></a>
<a id="schema_HTTPValidationError"></a>
<a id="tocShttpvalidationerror"></a>
<a id="tocshttpvalidationerror"></a>

```json
{
  "detail": [
    {
      "loc": [
        "string"
      ],
      "msg": "string",
      "type": "string"
    }
  ]
}

```

HTTPValidationError

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|detail|[[ValidationError](#schemavalidationerror)]|false|none|none|

<h2 id="tocS_ValidationError">ValidationError</h2>
<!-- backwards compatibility -->
<a id="schemavalidationerror"></a>
<a id="schema_ValidationError"></a>
<a id="tocSvalidationerror"></a>
<a id="tocsvalidationerror"></a>

```json
{
  "loc": [
    "string"
  ],
  "msg": "string",
  "type": "string"
}

```

ValidationError

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|loc|[anyOf]|true|none|none|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|integer|false|none|none|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|msg|string|true|none|none|
|type|string|true|none|none|


