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

> GET account/confirm/?id=1&code=<code>

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
    "is_free": false|true
}
```