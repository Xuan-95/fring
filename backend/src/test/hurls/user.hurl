GET http://{{host}}:{{port}}/health
HTTP 200

DELETE http://{{host}}:{{port}}/api/v1/users/99999
HTTP 204

POST http://{{host}}:{{port}}/api/v1/users/
{
    "id": 99999,
    "username": "Test",
    "email": "test@gmail.com"
}
HTTP 201

POST http://{{host}}:{{port}}/api/v1/users/
{
    "username": "Test",
    "email": "test@gmail.com"
}
HTTP 400

GET http://{{host}}:{{port}}/api/v1/users/
HTTP 200
[Asserts]
jsonpath "$[-1].id" == 99999
jsonpath "$[-1].username" == "Test"
jsonpath "$[-1].email" == "test@gmail.com"


GET http://{{host}}:{{port}}/api/v1/users/99999
HTTP 200
[Asserts]
jsonpath "$.id" == 99999
jsonpath "$.username" == "Test"
jsonpath "$.email" == "test@gmail.com"



