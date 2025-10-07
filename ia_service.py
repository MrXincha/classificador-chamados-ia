import os
import google.generativeai as genai


def classify_ticket(description: str, categories: list) -> str:
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "Erro: API Key não configurada."

        genai.configure(api_key=api_key)

        # Constrói o "prompt" - a instrução que damos para a IA
        # Esta é uma das partes mais importantes!
        prompt = f"""
        Analise a seguinte descrição de um chamado técnico e classifique-o em uma das categorias listadas abaixo.
        Retorne APENAS o nome exato da categoria e nada mais.

        Descrição do Chamado:
        "{description}"

        Categorias Possíveis:
        {', '.join(categories)}

        Categoria:
        """

        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content(prompt)

        predicted_category = response.text.strip()

        if predicted_category in categories:
            return predicted_category
        else:
            print(f"Alerta: A IA retornou uma categoria inesperada: '{predicted_category}'")
            return "Dúvida Geral"

    except Exception as e:
        print(f"Ocorreu um erro ao chamar a API do Gemini: {e}")
        return "Dúvida Geral"