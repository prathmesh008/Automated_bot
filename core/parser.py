import os
import PyPDF2
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from .schema import UserProfile

def extract_text(file_path: str) -> str:
    """Extracts raw text from a file."""
    if file_path.endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    elif file_path.endswith('.pdf'):
        text = ""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text()
        return text
    return ""

def parse_resume(file_path: str, api_key: str) -> Optional[UserProfile]:
    """Parses a resume and returns a structured UserProfile."""
    raw_text = extract_text(file_path)
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.6-flash",
        google_api_key=api_key,
        temperature=0.1
    )
    
    parser = PydanticOutputParser(pydantic_object=UserProfile)
    
    prompt = PromptTemplate(
        template="""
        You are an expert technical recruiter and resume parser.
        Extract the following information from the provided resume text into a structured format.
        Pay special attention to technical skills, project links, and quantifying impact in descriptions.
        
        {format_instructions}
        
        Resume Text:
        {resume_text}
        """,
        input_variables=["resume_text"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    
    chain = prompt | llm | parser
    
    try:
        profile = chain.invoke({"resume_text": raw_text})
        return profile
    except Exception as e:
        print(f"Error parsing resume: {e}")
        return None

if __name__ == "__main__":
    # Test execution
    pass
