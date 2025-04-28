import importlib
import os

class TemplateParser():
    def __init__(self, language: str = None, default_language:str = "en"):
        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.default_language = default_language
        self.language = None

        self.set_language(language)


    def set_language(self, language: str):
        if not language:
            self.language = self.default_language

        language_path = os.path.join(self.current_path, "locales", language)
      
        if os.path.exists(language_path): 
            self.language = language
        else:  
            self.language = self.default_language



    #group = rag.py
    #key = system_prompt, document_prompt, footer_prompt
    #vars = doc_num, chunk_text

    def get(self, group: str, key: str, vars: dict={}):
        if not group or not key:
            return None
        
        group_path = os.path.join(self.current_path, "locales", self.language, f"{group}.py" )
       
        if not os.path.exists(group_path):
            return None
        
        try:
            module = importlib.import_module(f"stores.llm.templates.locales.{self.language}.{group}")
            key_attribute = getattr(module, key, None)
            if not key_attribute:
                return None
            return key_attribute.substitute(vars)
        except (ImportError, AttributeError):
            return None
