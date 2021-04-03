# API

## Users

### Create

> POST account/users

body:
```json
{
    "email": "email",
    "password": "password",
    "username": "",
    "first_name": "",
    "last_name": "",
    "email": "",
    "phone"
}
```

### Login

> POST account/token/login


body:
```json
{
    "phone": "phone",
    "password": "password",
}
```

response:
```json
{
    "auth_token": "...token..."
}
```

### Me

> POST/GET? account/about/me

response `User object`
```json
{
    "id": 1,
    "visits": [
        {
            "id": 7,
            "date": "2021-04-02T19:11:09.554183+03:00",
            "duration": 3600,
            "end": "2021-04-02T20:11:09.554199+03:00",
            "is_free": true,
            "is_active": false,
            "staff": 1
        },
        {
            "id": 8,
            "date": "2021-04-02T19:12:36.615214+03:00",
            "duration": 3600,
            "end": "2021-04-02T20:12:36.615139+03:00",
            "is_free": false,
            "is_active": true,
            "staff": 1
        }
    ],
    "children": [],
    "used_invintation": {
        "id": 1,
        "value": "9RA7YM",
        "used": false,
        "visited": true,
        "creator": 1
    },
    "my_invintations": [
        {
            "id": 1,
            "value": "9RA7YM",
            "used": false,
            "visited": true,
            "creator": 1
        }
    ],
    "password": "pbkdf2_sha256$216000$BosoQ250chl0$h8/cvLJjpNlhWY0nLsu9DRPN8oYw6dDqALI9t5/kd+4=",
    "last_login": "2021-04-03T16:03:50.481545+03:00",
    "is_superuser": true,
    "first_name": "lapp",
    "last_name": "lapp",
    "is_staff": true,
    "is_active": true,
    "date_joined": "2021-04-01T16:52:35+03:00",
    "phone": "lapp",
    "email": "lapp@lapp.com",
    "username": "some2",
    "phone_code": "123456",
    "phone_confirmed": true,
    "device_token": "",
    "groups": [],
    "user_permissions": []
}
```

### Confirm Phone

#### Get a code

> POST account/confirm/

body:
```json
{
    "phone":"89XXXXXXXXX"
}
```

response:
```json
{
    "id": 1
}
```

#### Confirm

> GET account/confirm/?id=1&code=`<code>`

response (`200`):
```json
{
    "message": "Phone number confirmed"
}
```

response (`403`):
```json
{
    "message": "Wrong code|id"
}
```

### Update

> PUT account/manage/

body:
```json
{
    "username": "",
    "first_name": "",
    "last_name": "",
    "email": "",
    "children": [
      {
        "id": 1,
        "updates": {
          "sex": "M",
          "age": 10
        }
      },
      {
        "add": {
          "sex": "M",
          "age": 10,
          "name": "name"
        }
      },
      {
        "id": 2,
        "delete": true,
      }
    ]
}
```


## Reset password
### Create application to reset password

> POST account/reset_password/

body:
```json
  "phone": "89XXXXXXXXX"
```

response:
```json
{
  "message": "The code was sent to your phone",
  "code": "user_code"
}
```
> note: save `code(user_code)`

the user phone will receive a `code`

### Check code(sms)

> GET account/reset_password/?code=`<code>`
>> Use code from sms, not from response

response(ok):
```json
{
  "message": "Code is valid"
}
```

response(not ok)400:
```json
{
  "message": "Code is invalid"
}
```

### Set a new password

> PUT account/reset_password/

body:
```json
{
  "code": "code from sms",
  "user_code": "code from response",
  "password": "a new password"
}
```

## Visits

### Get QR (Hash):

> GET mobile/visits

response:
```json
{
    "hash": "4dff4ea340f0a823f15d3f4f01ab62eae0e5da579ccb851f8db9dfe84c58b2b37b89903a740e1ee172da793a6e79d560e5f7f9bd058a12a280433ed6fa46510a"
}
```

### Get User Info

> POST mobile/visits/add

body:
```json
{
    "hash": "4dff4ea340f0a823f15d3f4f01ab62eae0e5da579ccb851f8db9dfe84c58b2b37b89903a740e1ee172da793a6e79d560e5f7f9bd058a12a280433ed6fa46510a"
}
```

### Confirm Visit

> PUT mobile/visits/add

body:
```json
{
    "duration": 3600(sec),
    "user_id": "1 (from ^)",
}
```

response:
```json
{
    "id": 9,
    "date": "2021-03-30T05:11:03.071080Z",
    "duration": 3600,
    "end": "2021-03-30T06:11:03.071080Z",
    "is_free": false|true,
    "is_active": false|true,
    "staff": 1
}
```

### Get All last visits

> GET mobile/visits/add

response:
```json
[
    {
        "id": 8,
        "visiter": [
            {
                "id": 1,
                "password": "pbkdf2_sha256$216000$JMz2HXQylK2Y$6cZgFoS3GSEU+EP3Sa56QmnpKtHvE0J7Hk7TgoMelEI=",
                "last_login": "2021-04-02T16:41:24.153292+03:00",
                "is_superuser": true,
                "first_name": "lapp",
                "last_name": "lapp",
                "is_staff": true,
                "is_active": true,
                "date_joined": "2021-04-01T16:52:35+03:00",
                "phone": "lapp",
                "email": "lapp@lapp.com",
                "username": "lapp",
                "phone_code": "123456",
                "phone_confirmed": true,
                "device_token": "",
                "used_invintation": 1,
                "groups": [],
                "user_permissions": [],
                "my_invintations": [
                    1
                ],
                "children": [],
                "visits": [
                    7,
                    8
                ]
            }
        ],
        "date": "2021-04-02T19:12:36.615214+03:00",
        "duration": 3600,
        "end": "2021-04-02T20:12:36.615139+03:00",
        "is_free": false,
        "is_active": true,
        "staff": 1
    }
]
```

## Invitatins

### Get my invites
> GET account/invite/

response:
```json
[
    {
        "id": 1,
        "value": "9RA7YM",
        "used": false,
        "visited": true,
        "creator": 1
    }
]
```

### Create invite
> POST account/invite/

body:
```json

```

response:
```json
{
    "id": 1,
    "value": "9RA7YM",
    "used": false,
    "visited": true,
    "creator": 1
}
```
