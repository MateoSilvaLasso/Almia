import os
from dotenv import load_dotenv
from typing import TypedDict, Optional, List
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex, Document
from llama_index.core.tools import QueryEngineTool
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.llms import ChatMessage, ImageBlock
from llama_index.llms.gemini import Gemini
from llama_index.llms.groq import Groq
import cloudinary
import cloudinary.uploader
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from selenium.webdriver.common.by import By



class PerfilAnalyzer:
    def __init__(self, linkedin_url: str, name: str):
        load_dotenv()
        #self.hv_path = hv_path
        self.linkedin_url = linkedin_url
        self.name = name
        #self.image_path = image_path
        self.llm = Groq(model="llama3-8b-8192", token=os.getenv("GOOGLE_API_KEY"))
        self.embed_model = GoogleGenAIEmbedding(model='gemini-embedding-exp', api_key=os.getenv("GOOGLE_API_KEY"))
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model
        self.response_text = None
        self.image_url = None
        self.gemini_pro = Gemini(model_name="models/gemini-2.0-flash", api_key=os.getenv("GOOGLE_API_KEY"))

    def scrap_linkedin(self) -> str:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--start-maximized")
        driver = webdriver.Chrome(options=options)
        driver.get("https://www.linkedin.com/login")

        #print("Inicia sesión en LinkedIn. Tienes 30 segundos...")
        #time.sleep(3)

        driver.find_element(By.ID, "username").send_keys("pedroperezarroba03@gmail.com")
        driver.find_element(By.ID, "password").send_keys("Seguridad_Baja.03")
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(5)

        driver.get(self.linkedin_url)
        time.sleep(5)

        driver.save_screenshot(filename='linkedin_profile.png')

        def scroll_down(driver, pause_time=1, scroll_times=5):
            for _ in range(scroll_times):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(pause_time)

        scroll_down(driver)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        texts = "\n".join([section.get_text(separator='\n', strip=True) for section in soup.find_all('section')])
        driver.quit()
        return texts

    def build_agents(self, linkedin_docs: List[Document]) -> FunctionAgent:
        
        index_linkedin = VectorStoreIndex.from_documents(linkedin_docs)

       
        tool_linkedin = QueryEngineTool.from_defaults(
            query_engine=index_linkedin.as_query_engine(),
            name="LinkedIn",
            description="Query the LinkedIn profile for professional background."
        )

        return FunctionAgent(
            tools=[tool_linkedin],
            llm=self.llm,
            name="Compare Professional Background",
            system_prompt="""Eres un agente experto en analizar perfiles profesionales destinado a analizar el perfil de LinkedIn de una persona en busca de optimización profesional, siempre usa emojis de este tipo que es lo que nos identifica 🚀 y siempre habla en español.

                Actúa de forma cercana, como si estuvieras ayudando a alguien que conoces, pero sin dejar de sonar profesional.

                Usa las herramientas proporcionadas (el perfil de LinkedIn) para:

                ✅ Comparar y dar retroalimentación sobre:

                Palabras clave en el título y extracto

                Sección “Acerca de” redactada

                Experiencia laboral con roles bien definidos

                Destacados (videos, PDFs, enlaces)

                Educación

                Licencias y certificaciones

                Habilidades (Skills)

                Proyectos

                Secciones adicionales (recomendaciones, voluntariado, publicaciones, etc.).

                ✅ Calificar:

                Asígnale 1 punto por cada criterio incluido en el perfil.

                Máximo: 9 puntos.

                Finalmente, proporciona:

                La puntuación total.

                Un resumen de las secciones que están muy bien.

                Sugerencias de mejora para las que están incompletas o ausentes (por ejemplo: “Puedes destacar más tus habilidades con …”)

                ✅ Clasificar:

                Si tiene más de 8/9:

                "¡Muy buen trabajo! Tu perfil tiene una base muy sólida 👏. Aun así, puedes dar algunos toques finales para destacar aún más."

                Si tiene 7 o menos:

                "Tu perfil tiene mucho margen de mejora 🚀. Un LinkedIn optimizado puede aumentar hasta 7 veces tus probabilidades de destacar ante los reclutadores."

                ✅ Importante:

                Por favor, ignora la foto de perfil, eso lo podremos revisar más adelante.

                Tú decides en cada situación qué herramienta es más adecuada para dar tus recomendaciones. 
                """
        )

    def upload_profile_image(self) -> str:
        cloudinary.config(
            cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
            api_key=os.getenv('CLOUDINARY_API_KEY'),
            api_secret=os.getenv('CLOUDINARY_API_SECRET')
        )
        upload_result = cloudinary.uploader.upload("./linkedin_profile.png")
        self.image_url = upload_result['secure_url']
        return self.image_url

    async def analizar(self) -> str:
        
        linkedin_text = self.scrap_linkedin()
        linkedin_docs = [Document(text=linkedin_text + f"linkedin de {self.name}", metadata={"source": f"{self.name}"})]

        agent = self.build_agents(linkedin_docs)
        self.response_text = await agent.run(
           f"Analiza a {self.name}, su perfil de LinkedIn"
        )

        self.upload_profile_image()
        time.sleep(5) 

        #print(f'image url : {self.image_url}')
        #print(str(self.response_text))

        messages_h = [
            ChatMessage(role='user', content=f"Analiza a {self.name}, su perfil de LinkedIn y Hoja de vida. ¿Qué aspectos de su perfil profesional crees que podría mejorar?"),
            ChatMessage(role='assistant', content=str(self.response_text)),
            
        ]

        msg= ChatMessage(
            role='user',
            content="Te estoy entregando una imagen de un perfil profesional de Linkedin de alguien, por favor describe la imagen y dame alguna recomendación de mejorar para esta,solo de la imagen de perfil. responde en español. por favor toma el puntaje que me diste anteriormente y sumale los puntos que consideres que merece",
        )

        msg.blocks.append(
            ImageBlock(
                url=self.image_url,
                #alt_text=f"Imagen de perfil de {self.name}"
            )
        )

        image_response = self.gemini_pro.chat(messages=messages_h + [msg])
        return {
            "resultado": {
                "texto": str(self.response_text),
                "imagen": str(image_response.message.content)
        }
}

