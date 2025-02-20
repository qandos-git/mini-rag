# mini-rag

# About
This repostory is my study note for @bakrianoo toturial in mini-rag.

to install the app use the instructions written in following repo:

[App instructions](https://github.com/bakrianoo/mini-rag)


# Concepts
`python-multipart` used to upload files to fastAPI

`.gitkeep ` file is used in Git to track empty directories. By default, Git does not track empty folders, so if you need to keep an empty directory in your repository (for structure or future use), you add a .gitkeep file inside it.


`uvicorn` High-performance ASGI (Asynchronous Server Gateway Interface) Server, used to run FastAPI app and deal with requests in devlopment enviroment.

### FastAPI 

Web framework used to invoke functions remotely. 

**How to use it?**

1. Install fastapi and uvicorn.
2. Initialize object from FastAPI module.
3. Define a function.
4. Use a decorator to define the type of the request type of this function (POST/GET).
5. Run the app using uvicorn `uvicorn file-name:object-name`

**What is Swager?**

Built-in documentaion from the FastAPI using the openapi standar. You can access it by adding `/doc` to the end of url. 

**What is PostMan?**

Free app provide user interface for testing multiple requests for specific project. 

The main advantage is that you can share the project.

Also it orgnize the work.


## Nested Routs
[Video link]()
## What?
Devide the routes into seprate files.
### Why?
We need to keep `main.py` file as small as possible and don't contain that much of logic.

So, if we have multiple routes we will create a package (directory) that contains all routes (as seprate modules)



