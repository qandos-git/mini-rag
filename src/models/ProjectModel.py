from .BaseDataModel import BaseDataModel
from .db_schemes import Project
from sqlalchemy.future import select
from sqlalchemy import func

class ProjectModel(BaseDataModel):
    
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)


    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        return instance
    

    async def create_project(self, project: Project):
        async with self.db_client() as session:
            async with session.begin():
                session.add(project)
            await session.refresh(project)
        return project
    

    async def get_project_or_create_one(self, project_id: int):
        async with self.db_client() as session:
                query = select(Project).where(
                    Project.project_id==project_id
                    )
                result = await session.execute(query)
                project = result.scalar_one_or_none()

                if project is None: #If no record is found, create a new project
                    project = Project(project_id=project_id)
                    project = await self.create_project(project=project) #use the create_project method to create a new project
                    return project #Return the project object with the _id field updated from Project collection in the database
        return project

       

    async def get_all_projects(self, page: int = 1, page_size: int = 10): #get all projects with pagination for efficient data retrieval
        async with self.db_client() as session:
                total_projects =await session.execute(select(
                    func.count(Project.project_id)
                )).scalar_one()
                total_pages = (total_projects + page_size - 1) // page_size
                query = select(Project).offset((page - 1) * page_size ).limit(page_size)
                projects = await session.execute(query).scalars().all()
      
        return projects, total_pages 



