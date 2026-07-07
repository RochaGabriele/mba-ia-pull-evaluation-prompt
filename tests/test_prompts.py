"""
Testes automatizados para validação de prompts.
"""
import re
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

V2_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_v2_prompt():
    """Retorna o dicionário (achatado) do prompt otimizado v2."""
    data = load_prompts(str(V2_FILE))
    if "bug_to_user_story_v2" in data:
        return data["bug_to_user_story_v2"]
    for value in data.values():
        if isinstance(value, dict) and "system_prompt" in value:
            return value
    return data


class TestPrompts:
    def _prompt(self):
        return get_v2_prompt()

    def _system(self):
        return (self._prompt().get("system_prompt") or "").lower()

    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        prompt = self._prompt()
        assert "system_prompt" in prompt, "Campo 'system_prompt' ausente"
        assert (prompt.get("system_prompt") or "").strip(), "system_prompt está vazio"

    def test_prompt_has_role_definition(self):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system = self._system()
        markers = ["você é", "voce e", "atue como", "product manager",
                   "product owner", "especialista", "engenheiro", "analista"]
        assert any(m in system for m in markers), "O prompt não define uma persona/role"

    def test_prompt_mentions_format(self):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system = self._system()
        markers = ["user story", "como um", "como o", "eu quero", "para que",
                   "critérios de aceitação", "dado que", "markdown"]
        assert any(m in system for m in markers), "O prompt não especifica o formato de User Story/Markdown"

    def test_prompt_has_few_shot_examples(self):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system = self._system()
        tem_keyword = "exemplo" in system or "few-shot" in system
        tem_par = ("relato de bug" in system or "bug report" in system) and "user story" in system
        assert tem_keyword and tem_par, "O prompt não contém exemplos few-shot de entrada/saída"

    def test_prompt_no_todos(self):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        combined = " ".join(str(v) for v in self._prompt().values())
        assert "[TODO]" not in combined, "Ainda há um placeholder [TODO] no prompt"
        assert not re.search(r"\bTODO\b", combined), "Ainda há um marcador TODO no prompt"

    def test_minimum_techniques(self):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = self._prompt().get("techniques_applied", [])
        assert isinstance(techniques, list), "techniques_applied deve ser uma lista"
        assert len(techniques) >= 2, f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}"

    def test_structure_is_valid(self):
        """Bônus: valida a estrutura completa via utils.validate_prompt_structure."""
        is_valid, errors = validate_prompt_structure(self._prompt())
        assert is_valid, f"Estrutura inválida: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
