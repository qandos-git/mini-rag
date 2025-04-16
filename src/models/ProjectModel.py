from .BaseDataModel import BaseDataModel
from .enums.DataBaseEnum import DataBaseEnum
from .db_schemes import Project

class ProjectModel(BaseDataModel):
    
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_PROJECT_NAME.value]

    async def create_project(self, project: Project):
        result = await self.collection.insert_one(project.dict(by_alias=True, exclude_unset=True)) #returns InsertOne object that contains metadata about the insertion operation
        project._id = result.inserted_id #Set the _id field of the project object to the inserted_id of the Project collection in the database
        return project #Return the project object with the _id field updated from Project collection in the database
    

    async def get_project_or_create_one(self, project_id: str):
        record = await self.collection.find_one({
            "project_id": project_id
            })             #Search in the collection for project with the specified project_id

        if record is None: #If no record is found, create a new project
            project = Project(project_id=project_id)
            project = await self.create_project(project=project) #use the create_project method to create a new project
            return project #Return the project object with the _id field updated from Project collection in the database
        
        return Project(**record) #** unpacks the record dictionary into the constructor of Project class. 
        #This creates a new instance of the Project class with the data from the record dictionary.
        #This is useful for creating an object from a dictionary where the keys of the dictionary match the parameter names of the class constructor.


    async def get_all_projects(self, page: int = 1, page_size: int = 10): #get all projects with pagination for efficient data retrieval

        total_projects = await self.collection.count_documents({}) #Count the total number of documents in the collection
        
        total_pages = (total_projects + page_size - 1) // page_size

        cursor = self.collection.find().skip((page - 1) * page_size).limit(page_size)  #retrieve all documents in specified page with specified page size
    
        projects = []
        async for project in cursor: #Convert MongoDB documents into Project objects
            projects.append(Project(**project))
       
        return projects, total_pages #Return the list of projects and the total number of pages




