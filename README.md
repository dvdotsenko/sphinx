
# Chat API's documentation!

Contents:


## Summary


### Terms

User - a database record containing given user’s name, password and metadata
Contact Point - user’s one of many phone numbers, email addresses and other globally-unique addressing handles.
named arguments collection - aka key-value map, Python dictionary, JavaScript Object, or Java HashMap
Contact Point Types - An Enum of label = value:

```
user_direct = 1
email_address = 2
phone_number = 3
```


### API Basics:

Server-bound API calls are made over JSON RPC protocol 2.0. Server exposes the API over versioned end-point. Authentication for the API calls is provided through inclusion of HTTP header in conformance with OAuth 2.0 Bearer Token specification `https://tools.ietf.org/html/rfc6750`

Example unauthenticated request and response:

```
Remote Address:74.125.207.141:80
Request URL:http://pta-naples.appspot.com/api/
Request Method:POST
Status Code:200 OK

Request Headers
Accept:application/json, text/javascript, */*; q=0.01
Accept-Encoding:gzip, deflate
Accept-Language:en-US,en;q=0.8
Connection:keep-alive
Content-Length:133
Content-Type:application/json
Host:pta-naples.appspot.com
Origin:http://pta-naples.appspot.com
Referer:http://pta-naples.appspot.com/
User-Agent:Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36
X-Requested-With:XMLHttpRequest

Request Payload
{"jsonrpc":"2.0","method":"users.register","params":{"name":"Name Name","email_address":"test@example.com","password":"pass"},"id":1}

Response Headers
view source
Alternate-Protocol:80:quic,p=0
Cache-Control:no-cache
Content-Encoding:gzip
Content-Length:246
Content-Type:application/json
Date:Fri, 22 May 2015 13:52:16 GMT
Server:Google Frontend
Vary:Accept-Encoding

Response Payload
{"jsonrpc": "2.0", "id": 1, "error": {"message": "Internal error.", "code": -32603, "data": "While processing the follwoing message (\"users.register\",\"{u'password': u'pass', u'email_address': u'test@example.com', u'name': u'Name Name'}\",\"1\") encountered the following error message \"User with email address test@example.com is already present\""}}
```

Example authenticated request and response:

```
Remote Address:74.125.70.141:80
Request URL:http://pta-naples.appspot.com/api/
Request Method:POST
Status Code:200 OK

Request Headers
Accept:application/json, text/javascript, */*; q=0.01
Accept-Encoding:gzip, deflate
Accept-Language:en-US,en;q=0.8
Authorization:Bearer eyJhb....p8GTw
Connection:keep-alive
Content-Length:70
Content-Type:application/json
Host:pta-naples.appspot.com
Origin:http://pta-naples.appspot.com
Referer:http://pta-naples.appspot.com/
User-Agent:Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36
X-Requested-With:XMLHttpRequest

Request Payload
[{"jsonrpc":"2.0","method":"tests.add_numbers","params":[1,2],"id":1}]

Response Headers
Alternate-Protocol:80:quic,p=0
Cache-Control:no-cache
Content-Encoding:gzip
Content-Length:58
Content-Type:application/json
Date:Fri, 22 May 2015 14:00:55 GMT
Server:Google Frontend
Vary:Accept-Encoding

Response Payload
[{"jsonrpc": "2.0", "result": 3, "id": 1}]
```


### API Endpoint

Testing JSON RPC endpoint: `http://pta-naples.appspot.com/api/`
Interactive UI allowing you to play with the API: `http://pta-naples.appspot.com/`


### Authentication Flow

Example full cycle registration, login, "get 'me' data" (JSON-RPC calls):

Register User:

```
users.register(**data)
```

where `data` is a named arguments collection of following possible arguments:

```
name - full name
password - desired password for the User account
contact_points - A list of one or more named arguments collections with the following attributes:
    value - string with the value of Contact Point
    type - one of Contact Point Type values
```

Return value is a key value collection representing the new User

User Login:

```
users.login(**data)
```

where `data` is a named arguments collection of following possible arguments:

```
contact_point_value - literal value of one of Contact Points User allowed to act as login name
password - User’s password
```

Return value is a key value collection representing the headers further authenticated calls must include to make authenticated calls

About Me API:

```
users.me()
```

Return value is a key value collection representing the new User


## API

### `tests.`**`add_numbers`**(_`*args`_)

Adds together as many numbers are are passed to the method call

Example:

```
add_numbers(1,23,4)
```

**Parameters**:
**args** (_list_) -- a list of None or more numbers to add

**Returns**:
the resulting sum

### `users.`**`login`**(_`**data`_)

Exchanges existing user login data for valid credentials.

Expects named arguments. Python call example:

```
.login(
    contact_point_value="test@example.com",
    password="pass"
)
```

Response example:

```
{
    "Authorization": "Bearer eyJh...hw2rw"
}
```

**Parameters**:
*   **contact_point_value** -- literal value of one of Contact Points User allowed to act as login name

*   **password** -- literal plain-text password for the account linked to that contact point.

**Returns**:
A hash object containing key-value pairs of headers client must
send back to authenticate subsequent requests

### `users.`**`me`**()

_(requires user session / authentication)_

Returns user record data for the logged in user:

```
{
  "gender": null,
  "id": "b3856cc0-baa2-4895-b4a5-94a7e1bda1eb",
  "date_of_birth": "2000-01-01T00:00:00",
  "name": "name",
  "contact_points_keys": [
    [
      "ContactPoint",
      "TEST@EXAMPLE.COM"
    ],
    [
      "ContactPoint",
      "13105551212"
    ],
    [
      "ContactPoint",
      "B3856CC0-BAA2-4895-B4A5-94A7E1BDA1EB"
    ]
  ]
}
```

**Returns**:
Serialized user record data

### `users.`**`recover_password`**(_`contact_point_value, contact_point_type=None`_)

Sends password recovery email to user.

**Parameters**:
*   **contact_point_value** (_str_) -- Value of the contact point user is choosing to send the password recovery request to.

*   **contact_point_type** (_int_) --

    (Optional) Type of contact point. One of:

    ```
    user_direct = 1
    email_address = 2
    phone_number = 3
    ```

### `users.`**`register`**(_`**data`_)

Exchanges new user data for valid login credentials.

Expects named arguments:

```
{
    "user_id": "fullname123",
    "name": "Full Name",
    "password": "pass",
    "date_of_birth": "2000-01-01",
    "gender": "1",
    "contact_points": [
      {
        "value": "test@example.com",
        "type": 2
      },
      {
        "value": "+1 (310) 555-1212",
        "type": 3
      }
    ]
}
```

Response example:

```
{
    "Authorization": "Bearer eyJh...hw2rw"
}
```

**Parameters**:
*   **user_id** (_str_) -- (Optional) Acts as username for the account. Autogenerated if not provided.

*   **name** (_str_) -- Full name of the user

*   **date_of_birth** (_str_) -- (Optional) ISO String containing date of birth of the user.

*   **gender** (_int_) -- (Optional) An enum indicating gender of the user (1 = male, 2 = female)

*   **password** (_str_) -- literal plain-text password for the account linked to that contact point.

*   **contact_points** (_list_) --

    A list of one or more objects representing contact points user chose to add to the account.
    Type attribute values are per ContactPointType enum:

    ```
    email_address = 2
    phone_number = 3
    ```

**Returns**:
A hash object containing key-value pairs of headers client must
send back to authenticate subsequent requests


# Indices and tables

*   `Index`

*   `Module Index`

*   `Search Page`
