import os
import re
from dotenv import load_dotenv
from serpapi import GoogleSearch

load_dotenv()

SERP_API_KEY = os.getenv("SERP_API_KEY")

def buscar_presenca_online(nome_empresa):
    resultado = {
        "SITE": None,
        "LINKEDIN": None,
        "TEM_SITE": False,
        "TEM_LINKEDIN": False,
    }

    try:
        query = f"{nome_empresa} site oficial linkedin"

        search = GoogleSearch({
            "q": query,
            "api_key": SERP_API_KEY,
            "engine": "google",
            "num": 10,
        })

        dados = search.get_dict()
        resultados = dados.get("organic_results", [])

        for item in resultados:
            link = item.get("link", "")

            # Identificação de canais corporativos no LinkedIn
            if "linkedin.com/company/" in link.lower():
                resultado["LINKEDIN"] = link
                resultado["TEM_LINKEDIN"] = True

            # Identificação de sites institucionais descartando redes sociais comuns
            elif (
                "linkedin.com" not in link.lower()
                and "facebook.com" not in link.lower()
                and "instagram.com" not in link.lower()
                and "youtube.com" not in link.lower()
            ):
                if resultado["SITE"] is None:
                    resultado["SITE"] = link
                    resultado["TEM_SITE"] = True

        return resultado

    except Exception as e:
        print(f"\n[red]Erro no módulo de busca externa (SerpAPI): {e}[/red]")
        return resultado