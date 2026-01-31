GET http://{{host}}:{{port}}/health
HTTP 200

DELETE http://{{host}}:{{port}}/api/v1/tasks/99999
HTTP 204

POST http://{{host}}:{{port}}/api/v1/tasks/
{
    "id": 99999,
    "title": "Test task",
    "description": "This is a description for a test task"
}
HTTP 201

POST http://{{host}}:{{port}}/api/v1/tasks/
{
    "id": 99999,
    "title": "Test task",
    "description": "This is a description for a test task"
}
HTTP 400

GET http://{{host}}:{{port}}/api/v1/tasks/
HTTP 200
[Asserts]
jsonpath "$[-1].id" == 99999
jsonpath "$[-1].title" == "Test task"
jsonpath "$[-1].description" == "This is a description for a test task"
jsonpath "$[-1].status" == "todo"


GET http://{{host}}:{{port}}/api/v1/tasks/99999
HTTP 200
[Asserts]
jsonpath "$.id" == 99999
jsonpath "$.title" == "Test task"
jsonpath "$.description" == "This is a description for a test task"
jsonpath "$.status" == "todo"



