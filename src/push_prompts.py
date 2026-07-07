"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()

V2_FILE = "prompts/bug_to_user_story_v2.yml"


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    if not username:
        print("❌ USERNAME_LANGSMITH_HUB não configurado no .env")
        return False

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido:")
        for err in errors:
            print(f"   - {err}")
        return False

    # Constrói o ChatPromptTemplate: system (persona/regras/few-shot) + user ({bug_report}).
    chat_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", prompt_data["system_prompt"]),
            ("human", prompt_data.get("user_prompt", "{bug_report}")),
        ]
    )

    repo = f"{username}/{prompt_name}"
    description = prompt_data.get("description", "")
    techniques = prompt_data.get("techniques_applied", [])
    tags = list(prompt_data.get("tags", [])) + [f"technique:{t}" for t in techniques]

    print(f"   Publicando (PÚBLICO): {repo}")
    try:
        url = hub.push(
            repo,
            chat_prompt,
            new_repo_is_public=True,
            new_repo_description=description,
            tags=tags,
        )
    except TypeError:
        # Fallback para versões do langchain sem suporte a tags no hub.push.
        url = hub.push(repo, chat_prompt, new_repo_is_public=True, new_repo_description=description)

    print(f"   ✓ Push concluído: {repo}")
    print(f"   ✓ URL: {url}")
    if techniques:
        print(f"   ✓ Técnicas: {', '.join(techniques)}")
    return True


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    for field in ("description", "system_prompt", "version"):
        if not prompt_data.get(field):
            errors.append(f"Campo obrigatório ausente ou vazio: {field}")

    system_prompt = (prompt_data.get("system_prompt") or "").strip()
    if "TODO" in system_prompt:
        errors.append("system_prompt ainda contém TODOs")

    techniques = prompt_data.get("techniques_applied", [])
    if len(techniques) < 2:
        errors.append(f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}")

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS (PÚBLICO)")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    data = load_yaml(V2_FILE)
    if not data:
        print(f"❌ Não foi possível carregar {V2_FILE}")
        return 1

    all_ok = True
    for prompt_name, prompt_data in data.items():
        print(f"\n→ {prompt_name}")
        if isinstance(prompt_data, dict):
            all_ok = push_prompt_to_langsmith(prompt_name, prompt_data) and all_ok

    if all_ok:
        print("\n✅ Push concluído. Verifique em: https://smith.langchain.com/prompts")
        print("   Próximo passo: python src/evaluate.py")
        return 0

    print("\n❌ Houve falhas no push.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
