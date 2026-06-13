import unittest

from app.services.chunk_parser import parse_chunks
from app.services.text_normalizer import join_pages


class ChunkParserTests(unittest.TestCase):
    def test_trailing_frontmatter_with_inline_and_reference_actions(self) -> None:
        markdown = """# ¿Cómo doy de alta un paciente?
Pregunta: Quiero registrar un nuevo paciente en MedSync.mx.
Respuesta: Entra al módulo de Pacientes, selecciona Nuevo paciente y completa los datos básicos. Después podrás crear o consultar su expediente clínico.

---
agent: support
intent: expediente_paciente
actions:
  - id: support.ir_expedientes
    type: route
    label: Ir a expedientes
    value: /expedientes
  - support.start_ticket
  - core.handoff
---
"""

        chunks = parse_chunks(markdown)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["agent"], "support")
        self.assertEqual(chunks[0]["intent"], "expediente_paciente")
        self.assertEqual(
            chunks[0]["answer"],
            "Entra al módulo de Pacientes, selecciona Nuevo paciente y completa los datos básicos. Después podrás crear o consultar su expediente clínico.",
        )
        self.assertEqual(
            chunks[0]["actions"],
            [
                {
                    "id": "support.ir_expedientes",
                    "type": "route",
                    "label": "Ir a expedientes",
                    "value": "/expedientes",
                },
                "support.start_ticket",
                "core.handoff",
            ],
        )

    def test_trailing_frontmatter_for_multiple_chunks(self) -> None:
        markdown = """# ¿Cómo doy de alta un paciente?
Pregunta: Quiero registrar un nuevo paciente en MedSync.mx.
Respuesta: Entra al módulo de Pacientes.

---
agent: support
intent: expediente_paciente
actions:
  - support.start_ticket
---

# Necesito una cotización
Pregunta: Quiero cotizar MedSync.mx para mi consultorio o clínica.
Respuesta: Solicita una cotización indicando número de médicos.

---
agent: attention
intent: capacitacion
actions:
  - core.request_callback
  - core.handoff
  - sales.book_demo
---
"""

        chunks = parse_chunks(markdown)

        self.assertEqual([chunk["agent"] for chunk in chunks], ["support", "attention"])
        self.assertEqual(
            [chunk["actions"] for chunk in chunks],
            [["support.start_ticket"], ["core.request_callback", "core.handoff", "sales.book_demo"]],
        )

    def test_leading_frontmatter_still_works(self) -> None:
        markdown = """---
agent: support
intent: problema_acceso
actions:
  - support.reset_steps
---
# No puedo iniciar sesion
Pregunta: Olvide mi contrasena.
Respuesta: Primero intenta restablecer el acceso.
"""

        chunks = parse_chunks(markdown)

        self.assertEqual(chunks[0]["agent"], "support")
        self.assertEqual(chunks[0]["intent"], "problema_acceso")
        self.assertEqual(chunks[0]["actions"], ["support.reset_steps"])

    def test_trailing_frontmatter_without_final_newline(self) -> None:
        markdown = """# ¿Dónde veo sesiones activas?
Pregunta: Necesito revisar sesiones iniciadas en la plataforma.
Respuesta: En Super Admin, abre Sesiones activas. Esta sección ayuda a monitorear accesos y revisar actividad de usuarios autorizados.

---
agent: attention
intent: super_admin_auditoria
actions:
  - id: superadmin.ir_auditoria
    type: route
    label: Ver auditoría
    value: /super-admin/audit
  - core.handoff
---"""

        chunks = parse_chunks(markdown)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["agent"], "attention")
        self.assertEqual(chunks[0]["intent"], "super_admin_auditoria")
        self.assertEqual(
            chunks[0]["actions"],
            [
                {
                    "id": "superadmin.ir_auditoria",
                    "type": "route",
                    "label": "Ver auditoría",
                    "value": "/super-admin/audit",
                },
                "core.handoff",
            ],
        )

    def test_join_pages_can_preserve_yaml_indentation_for_object_actions(self) -> None:
        markdown = """# ¿Dónde veo sesiones activas?
Pregunta: Necesito revisar sesiones iniciadas en la plataforma.
Respuesta: En Super Admin, abre Sesiones activas.

---
agent: attention
intent: super_admin_auditoria
actions:
  - id: superadmin.ir_auditoria
    type: route
    label: Ver auditoría
    value: /super-admin/audit
  - core.handoff
---"""

        text = join_pages([{"text": markdown}], preserve_inline_spacing=True)
        chunks = parse_chunks(text)

        self.assertEqual(
            chunks[0]["actions"],
            [
                {
                    "id": "superadmin.ir_auditoria",
                    "type": "route",
                    "label": "Ver auditoría",
                    "value": "/super-admin/audit",
                },
                "core.handoff",
            ],
        )


if __name__ == "__main__":
    unittest.main()
