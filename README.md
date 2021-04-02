# API

## Users

### Create

> POST account/users

body:
```json
{
    "email": "email",
    "password": "password",
    ...
}
```

### Login

> POST account/token/login


body:
```json
{
    "email": "email",
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

> POST/GET? account/users/me

response `User object`


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
