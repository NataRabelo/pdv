import importlib.util
from pathlib import Path
import unittest


PERMISSIONS_FILE = Path(__file__).resolve().parents[1] / "app" / "security" / "permissions.py"
SPEC = importlib.util.spec_from_file_location("permission_catalog", PERMISSIONS_FILE)
permission_catalog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(permission_catalog)

DEFAULT_PERMISSION_DEFINITIONS = permission_catalog.DEFAULT_PERMISSION_DEFINITIONS
build_permission_groups = permission_catalog.build_permission_groups
normalize_permission_codes = permission_catalog.normalize_permission_codes


class _PermissionStub:
    def __init__(self, permission_id, codigo, nome=None, descricao=None, ativo=True):
        self.id = permission_id
        self.codigo = codigo
        self.nome = nome or codigo
        self.descricao = descricao
        self.ativo = ativo


class PermissionHierarchyTestCase(unittest.TestCase):
    def test_financeiro_relatorio_depende_do_geral(self):
        effective_codes = normalize_permission_codes({"visualizar_relatorio_financeiro"})

        self.assertNotIn("visualizar_relatorio_financeiro", effective_codes)

        effective_codes = normalize_permission_codes({
            "visualizar_financeiro",
            "visualizar_relatorio_financeiro",
        })

        self.assertIn("visualizar_financeiro", effective_codes)
        self.assertIn("visualizar_relatorio_financeiro", effective_codes)

    def test_dependencia_em_cadeia_remove_filhos_orfaos(self):
        effective_codes = normalize_permission_codes({
            "visualizar_pdv",
            "criar_cupom",
        })

        self.assertIn("visualizar_pdv", effective_codes)
        self.assertNotIn("criar_cupom", effective_codes)

        effective_codes = normalize_permission_codes({
            "visualizar_pdv",
            "visualizar_cupom",
            "criar_cupom",
        })

        self.assertIn("visualizar_cupom", effective_codes)
        self.assertIn("criar_cupom", effective_codes)

    def test_todas_as_permissions_padrao_estao_cobertas_no_catalogo(self):
        grouped_permissions = build_permission_groups([
            _PermissionStub(index, item["codigo"], item["nome"])
            for index, item in enumerate(DEFAULT_PERMISSION_DEFINITIONS, start=1)
        ])

        grouped_codes = {
            permission["codigo"]
            for group in grouped_permissions
            for permission in group["permissions"]
        }
        default_codes = {item["codigo"] for item in DEFAULT_PERMISSION_DEFINITIONS}

        self.assertEqual(default_codes, grouped_codes)


if __name__ == "__main__":
    unittest.main()
