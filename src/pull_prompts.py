"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

# Prompt de origem (baixa qualidade) que serve de ponto de partida.
SOURCE_PROMPT = "leonanluppi/bug_to_user_story_v1"
OUTPUT_FILE = "prompts/bug_to_user_story_v1.yml"


def _extract_prompts(pulled) -> tuple[str, str]:
    """Extrai (system_prompt, user_prompt) de um objeto retornado por hub.pull()."""
    system_parts, user_parts = [], []
    messages = getattr(pulled, "messages", None)

    if messages:
        for msg in messages:
            inner = getattr(msg, "prompt", None)
            text = getattr(inner, "template", None) or getattr(msg, "content", "")
            role = msg.__class__.__name__.lower()
            if "human" in role or "user" in role:
                user_parts.append(text)
            else:
                system_parts.append(text)
    else:
        system_parts.append(getattr(pulled, "template", str(pulled)))

    return "\n\n".join(system_parts).strip(), "\n\n".join(user_parts).strip()


def pull_prompts_from_langsmith():
    """Faz o pull do prompt do Hub e salva localmente em YAML."""
    print(f"Puxando prompt do LangSmith Hub: {SOURCE_PROMPT}")
    pulled = hub.pull(SOURCE_PROMPT)
    print("   ✓ Prompt carregado com sucesso")

    system_prompt, user_prompt = _extract_prompts(pulled)

    data = {
        "bug_to_user_story_v1": {
            "description": "Prompt inicial de BAIXA QUALIDADE puxado do LangSmith Hub (baseline).",
            "system_prompt": system_prompt,
            "user_prompt": user_prompt or "{bug_report}",
            "version": "v1",
            "source": SOURCE_PROMPT,
            "tags": ["bug-analysis", "user-story", "baseline"],
        }
    }

    if save_yaml(data, OUTPUT_FILE):
        print(f"   ✓ Prompt salvo em {OUTPUT_FILE}")
        return True

    print(f"   ❌ Falha ao salvar {OUTPUT_FILE}")
    return False


def main():
    """Função principal"""
    print_section_header("PULL DE PROMPTS DO LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    try:
        return 0 if pull_prompts_from_langsmith() else 1
    except Exception as e:
        print(f"\n❌ Erro ao puxar prompt '{SOURCE_PROMPT}': {e}")
        print("Verifique LANGSMITH_API_KEY no .env e sua conexão com a internet.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
