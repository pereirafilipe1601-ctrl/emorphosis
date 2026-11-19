"""
EMORPHOSIS — Testes automatizados para scripts/notion_hub.py
Executa sem rede (usa mocks) e valida schemas da Notion API 2026-03-11,
uploads single-part/multi-part, bootstrap, tarefas, ideias e sync do DEVLOG.md.

Rodar:
  python -m unittest scripts/test_notion_hub.py -v
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import notion_hub as nh  # noqa: E402


class FakeNotionClient(nh.NotionClient):
    """Cliente fake em memória para validar todas as chamadas de API sem rede."""

    def __init__(self) -> None:
        super().__init__(token="ntn_test_token_only")
        self.calls: list[tuple[str, str, dict | None]] = []
        self.uploads: list[dict] = []
        self.fail_first_task_db = False
        self.fail_column_list = False
        self.children_by_parent: dict[str, list[dict]] = {}
        self.deleted_blocks: list[str] = []
        self.page_by_id: dict[str, dict] = {}
        self.query_results_override: list[dict] | None = None
        self._page_counter = 0

    def request_json(self, method: str, path: str, payload: dict | None = None) -> dict:
        self.calls.append((method, path, payload))
        if method == "GET" and path == "/users/me":
            return {"object": "user", "id": "bot-1", "name": "Emorphosis Agent"}

        if method == "GET" and path.startswith("/pages/"):
            pid = path.split("/")[-1]
            if pid in self.page_by_id:
                return self.page_by_id[pid]
            return {
                "object": "page",
                "id": pid,
                "url": f"https://www.notion.so/{pid.replace('-', '')}",
                "cover": None,
                "properties": {
                    "Ideia": {"type": "title", "title": [{"plain_text": "Audio glitch no mapa"}]},
                    "Formatos": {"type": "multi_select", "multi_select": [{"name": "Áudio"}]},
                    "Pilar": {"type": "multi_select", "multi_select": [{"name": "H0M3 / Mapa"}]},
                    "Autor": {"type": "select", "select": {"name": "Filipe"}},
                    "Anexos / Capa": {
                        "type": "files",
                        "files": [
                            {
                                "name": "voz.ogg",
                                "type": "file",
                                "file": {"url": "https://cdn.notion.so/voz.ogg", "expiry_time": "2026-11-19T10:00:00Z"},
                            }
                        ],
                    },
                },
            }

        if method == "GET" and "/blocks/" in path and "/children" in path:
            bid = path.split("/blocks/")[1].split("/children")[0]
            return {
                "object": "list",
                "results": self.children_by_parent.get(bid, []),
                "has_more": False,
                "next_cursor": None,
            }

        if method == "DELETE" and path.startswith("/blocks/"):
            bid = path.split("/blocks/")[1]
            self.deleted_blocks.append(bid)
            return {"object": "block", "id": bid, "in_trash": True}

        if method == "PATCH" and path.startswith("/blocks/") and path.endswith("/children"):
            if self.fail_column_list and payload:
                if any(b.get("type") == "column_list" for b in payload.get("children", [])):
                    raise nh.NotionAPIError(400, "validation_error", "column_list unsupported in test")
            return {"object": "list", "results": []}

        if method == "POST" and path == "/databases":
            title_txt = "".join(t["text"]["content"] for t in (payload or {}).get("title", []))
            if "Task" in title_txt:
                if self.fail_first_task_db:
                    self.fail_first_task_db = False
                    raise nh.NotionAPIError(400, "validation_error", "status group unsupported on create")
                return {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "data_sources": [{"id": "22222222-2222-2222-2222-222222222222", "name": title_txt}],
                }
            return {
                "id": "33333333-3333-3333-3333-333333333333",
                "data_sources": [{"id": "44444444-4444-4444-4444-444444444444", "name": title_txt}],
            }

        if method == "GET" and path == "/data_sources/22222222-2222-2222-2222-222222222222":
            return {
                "id": "22222222-2222-2222-2222-222222222222",
                "properties": {
                    "Status": {"id": "st_id", "type": "status"},
                    "Ideia Origem": {
                        "id": "rel_id",
                        "type": "relation",
                        "relation": {
                            "data_source_id": "44444444-4444-4444-4444-444444444444",
                            "dual_property": {"synced_property_id": "back_rel_id"},
                        },
                    },
                },
            }

        if method == "GET" and path == "/data_sources/44444444-4444-4444-4444-444444444444":
            return {
                "id": "44444444-4444-4444-4444-444444444444",
                "properties": {
                    "Status": {"id": "idea_st_id", "type": "select"},
                    "Anexos / Capa": {"id": "idea_files_id", "type": "files"},
                },
            }

        if method == "POST" and path == "/pages":
            self._page_counter += 1
            pid = f"aaaaaaaa-aaaa-aaaa-aaaa-{self._page_counter:012d}"
            return {"id": pid, "url": f"https://www.notion.so/{pid.replace('-', '')}"}

        if method == "POST" and path.endswith("/query"):
            if self.query_results_override is not None:
                return {
                    "results": self.query_results_override,
                    "has_more": False,
                    "next_cursor": None,
                }
            return {
                "results": [
                    {
                        "id": "bbbbbbbb-bbbb-bbbb-bbbb-000000000001",
                        "url": "https://www.notion.so/task1",
                        "properties": {
                            "Tarefa": {"type": "title", "title": [{"plain_text": "Integrar Notion Dev Hub"}]},
                            "Status": {"type": "status", "status": {"name": "Concluído"}},
                            "Prioridade": {"type": "select", "select": {"name": "Alta"}},
                            "Responsável": {"type": "select", "select": {"name": "Filipe"}},
                            "Área": {"type": "multi_select", "multi_select": [{"name": "Infra / Deploy"}]},
                            "Branch / PR": {"type": "url", "url": "https://github.com/pereirafilipe1601-ctrl/emorphosis"},
                            "Registrado no DEVLOG": {"type": "checkbox", "checkbox": False},
                        },
                    }
                ],
                "has_more": False,
                "next_cursor": None,
            }

        return {"ok": True}

    def upload_file(self, file_path: Path) -> dict:
        block_type, fmt_label = nh.classify_media_block(file_path)
        info = {
            "id": f"fu-{len(self.uploads) + 1}",
            "filename": file_path.name,
            "size": file_path.stat().st_size,
            "mime_type": nh.guess_mime_type(file_path),
            "block_type": block_type,
            "format_label": fmt_label,
        }
        self.uploads.append(info)
        return info


class NotionHubTests(unittest.TestCase):
    def test_extract_notion_id_variants(self) -> None:
        expected = "248104cd-477e-80fd-b757-e945d38000bd"
        self.assertEqual(nh.extract_notion_id(expected), expected)
        self.assertEqual(nh.extract_notion_id("248104cd477e80fdb757e945d38000bd"), expected)
        self.assertEqual(
            nh.extract_notion_id(
                "https://www.notion.so/emorphosis/EMORPHOSIS-DEV-HUB-248104cd477e80fdb757e945d38000bd?v=99999999999999999999999999999999"
            ),
            expected,
        )
        with self.assertRaises(ValueError):
            nh.extract_notion_id("not-an-id")

    def test_media_classification_and_voice_notes(self) -> None:
        self.assertEqual(nh.classify_media_block(Path("nota_voz.ogg")), ("audio", "Áudio"))
        self.assertEqual(nh.classify_media_block(Path("demo.m4a")), ("audio", "Áudio"))
        self.assertEqual(nh.classify_media_block(Path("reel.mp4")), ("video", "Vídeo"))
        self.assertEqual(nh.classify_media_block(Path("look.webp")), ("image", "Foto / Print"))
        self.assertEqual(nh.classify_media_block(Path("briefing.pdf")), ("pdf", "PDF / Doc"))
        self.assertEqual(nh.classify_media_block(Path("dados.zip")), ("file", "PDF / Doc"))
        self.assertEqual(nh.guess_mime_type(Path("nota_voz.ogg")), "audio/ogg")

    def test_upsert_env_preserves_existing_keys_and_comments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text(
                "# Comentário original\nFTP_HOST=ftp.example.com\nNOTION_API_KEY=ntn_secret\nNOTION_ROOT_PAGE_ID=\n",
                encoding="utf-8",
            )
            nh.upsert_env_values(
                {
                    "NOTION_ROOT_PAGE_ID": "aaaa-bbbb",
                    "NOTION_TASKS_DS_ID": "cccc-dddd",
                },
                path=env_file,
            )
            text = env_file.read_text(encoding="utf-8")
            self.assertIn("# Comentário original", text)
            self.assertIn("FTP_HOST=ftp.example.com", text)
            self.assertIn("NOTION_API_KEY=ntn_secret", text)
            self.assertIn("NOTION_ROOT_PAGE_ID=aaaa-bbbb", text)
            self.assertIn("NOTION_TASKS_DS_ID=cccc-dddd", text)

    def test_multipart_body_framing(self) -> None:
        body, ctype = nh.build_multipart_body(
            fields=[("part_number", "2")],
            file_field=("file", "clip.mp4", "video/mp4", b"\x00\x01VIDEO"),
        )
        self.assertTrue(ctype.startswith("multipart/form-data; boundary="))
        self.assertIn(b'name="part_number"\r\n\r\n2\r\n', body)
        self.assertIn(b'name="file"; filename="clip.mp4"\r\nContent-Type: video/mp4\r\n\r\n\x00\x01VIDEO', body)

    def test_upload_file_single_and_multi_part_api_calls(self) -> None:
        client = nh.NotionClient(token="ntn_test")
        recorded: list[tuple[str, str, str | None]] = []

        def fake_raw(method: str, path: str, body: bytes | None = None, content_type: str | None = None, max_retries: int = 3) -> dict:
            recorded.append((method, path, content_type))
            if path == "/file_uploads":
                return {"id": "upload-xyz", "status": "pending"}
            return {"id": "upload-xyz", "status": "uploaded"}

        with tempfile.TemporaryDirectory() as tmp:
            small = Path(tmp) / "foto.png"
            small.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 100)
            with mock.patch.object(client, "_raw_request", side_effect=fake_raw):
                res = client.upload_file(small)
            self.assertEqual(res["block_type"], "image")
            self.assertEqual([p for _, p, _ in recorded], ["/file_uploads", "/file_uploads/upload-xyz/send"])

            # Simula arquivo > 20 MiB baixando temporariamente os limites para testar streaming multi_part
            recorded.clear()
            big = Path(tmp) / "video.mp4"
            big.write_bytes(b"A" * 250)
            with mock.patch.object(nh, "SINGLE_PART_MAX_BYTES", 100), mock.patch.object(
                nh, "MULTI_PART_CHUNK_BYTES", 100
            ), mock.patch.object(client, "_raw_request", side_effect=fake_raw):
                res_big = client.upload_file(big)
            self.assertEqual(res_big["block_type"], "video")
            self.assertEqual(
                [p for _, p, _ in recorded],
                [
                    "/file_uploads",
                    "/file_uploads/upload-xyz/send",
                    "/file_uploads/upload-xyz/send",
                    "/file_uploads/upload-xyz/send",
                    "/file_uploads/upload-xyz/complete",
                ],
            )

    def test_bootstrap_with_status_fallback_views_seed_and_env(self) -> None:
        client = FakeNotionClient()
        client.fail_first_task_db = True
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text("NOTION_API_KEY=ntn_fake\n", encoding="utf-8")
            ids = nh.cmd_bootstrap(
                client=client,
                page_id_raw="https://www.notion.so/EMORPHOSIS-HUB-99999999999999999999999999999999",
                seed=True,
                save_env=True,
                env_path=env_file,
            )
            self.assertEqual(ids["NOTION_ROOT_PAGE_ID"], "99999999-9999-9999-9999-999999999999")
            self.assertEqual(ids["NOTION_TASKS_DS_ID"], "22222222-2222-2222-2222-222222222222")
            self.assertEqual(ids["NOTION_IDEAS_DS_ID"], "44444444-4444-4444-4444-444444444444")

            # Verifica que back-relation foi renomeada para "Tarefas Geradas"
            patch_ideas = [
                p for m, path, p in client.calls
                if m == "PATCH" and path == "/data_sources/44444444-4444-4444-4444-444444444444"
            ]
            self.assertTrue(any(p and p.get("properties", {}).get("back_rel_id", {}).get("name") == "Tarefas Geradas" for p in patch_ideas))

            # Verifica 6 views criadas (3 Tasks + 3 Ideas)
            view_calls = [p for m, path, p in client.calls if m == "POST" and path == "/views"]
            self.assertEqual(len(view_calls), 6)

            # Verifica 1 ideia + 3 tarefas de seed criadas via data_source_id
            page_calls = [p for m, path, p in client.calls if m == "POST" and path == "/pages"]
            self.assertEqual(len(page_calls), 4)
            self.assertTrue(all(p["parent"]["type"] == "data_source_id" for p in page_calls))

            # Verifica capa, ícone da página raiz, ícones verdes dos bancos e capa Fit Lab
            root_patches = [
                p for m, path, p in client.calls
                if m == "PATCH" and path == "/pages/99999999-9999-9999-9999-999999999999"
            ]
            self.assertTrue(root_patches)
            self.assertIn("cover", root_patches[-1])
            self.assertIn("icon", root_patches[-1])
            uploaded_names = [u["filename"] for u in client.uploads]
            self.assertIn("notion-cover.png", uploaded_names)
            self.assertIn("notion-icon.png", uploaded_names)
            self.assertIn("aevus-jaqueta.png", uploaded_names)
            db_patches = [
                (path, p) for m, path, p in client.calls
                if m == "PATCH" and path.startswith("/databases/")
            ]
            self.assertEqual(len(db_patches), 2)
            self.assertTrue(all(p["icon"]["icon"]["color"] == "green" for _, p in db_patches))

    def test_create_idea_with_audio_image_and_link_sets_cover_and_blocks(self) -> None:
        client = FakeNotionClient()
        with tempfile.TemporaryDirectory() as tmp:
            img = Path(tmp) / "referencia.png"
            img.write_bytes(b"PNGDATA")
            aud = Path(tmp) / "brainstorm.ogg"
            aud.write_bytes(b"OGGDATA")

            nh.create_idea(
                client=client,
                ideas_ds_id="44444444-4444-4444-4444-444444444444",
                title="Efeito de som glitch no botão",
                formats=["Link / Ref"],
                pillars=["Visual / Glitch"],
                author="Filipe",
                link="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                notes="Testar som curto ao abrir modal\n- [ ] Gravar sample",
                files=[aud, img],
            )
            _, _, payload = [c for c in client.calls if c[0] == "POST" and c[1] == "/pages"][-1]
            assert payload is not None
            self.assertEqual(payload["cover"], {"type": "file_upload", "file_upload": {"id": "fu-2"}})
            fmt_names = {o["name"] for o in payload["properties"]["Formatos"]["multi_select"]}
            self.assertEqual(fmt_names, {"Link / Ref", "Áudio", "Foto / Print"})
            block_types = [b["type"] for b in payload["children"]]
            self.assertEqual(block_types, ["paragraph", "to_do", "embed", "audio", "image"])

    def test_promote_idea_links_and_updates_status(self) -> None:
        client = FakeNotionClient()
        nh.promote_idea_to_task(
            client=client,
            tasks_ds_id="22222222-2222-2222-2222-222222222222",
            idea_page_id="55555555-5555-5555-5555-555555555555",
            priority="Alta",
        )
        create_call = [p for m, path, p in client.calls if m == "POST" and path == "/pages"][-1]
        self.assertEqual(create_call["properties"]["Ideia Origem"]["relation"], [{"id": "55555555-5555-5555-5555-555555555555"}])
        self.assertEqual(create_call["properties"]["Área"]["multi_select"], [{"name": "H0M3 / Mapa"}])
        patch_idea = [p for m, path, p in client.calls if m == "PATCH" and path == "/pages/55555555-5555-5555-5555-555555555555"][-1]
        self.assertEqual(patch_idea["properties"]["Status"]["select"]["name"], "Virou Tarefa")

    def test_devlog_sync_apply_prepends_cleanly(self) -> None:
        client = FakeNotionClient()
        with tempfile.TemporaryDirectory() as tmp:
            devlog = Path(tmp) / "DEVLOG.md"
            devlog.write_text("# DEVLOG\n\nIntro\n\n---\n\n## [2026-11-18] — Antiga\n", encoding="utf-8")
            done, entry = nh.sync_devlog(
                client=client,
                tasks_ds_id="22222222-2222-2222-2222-222222222222",
                author="Filipe (+ Antigravity)",
                apply=True,
                devlog_path=devlog,
            )
            self.assertEqual(len(done), 1)
            self.assertIn("Integrar Notion Dev Hub", entry)
            final_text = devlog.read_text(encoding="utf-8")
            self.assertLess(final_text.index("Integrar Notion Dev Hub"), final_text.index("## [2026-11-18] — Antiga"))
            # Confirma checkbox marcado como true no Notion
            patch_task = [
                p for m, path, p in client.calls
                if m == "PATCH" and path == "/pages/bbbbbbbb-bbbb-bbbb-bbbb-000000000001"
            ][-1]
            self.assertTrue(patch_task["properties"]["Registrado no DEVLOG"]["checkbox"])

    def test_attach_to_idea_preserves_existing_files_and_sets_cover(self) -> None:
        client = FakeNotionClient()
        with tempfile.TemporaryDirectory() as tmp:
            pic = Path(tmp) / "capa.jpg"
            pic.write_bytes(b"JPGDATA")
            vid = Path(tmp) / "demo.mov"
            vid.write_bytes(b"MOVDATA")
            nh.attach_to_idea(
                client=client,
                page_id="55555555-5555-5555-5555-555555555555",
                files=[pic, vid],
                embeds=["https://vimeo.com/123456"],
                notes="Anexado depois da reunião",
            )
            patch_call = [
                p for m, path, p in client.calls
                if m == "PATCH" and path == "/pages/55555555-5555-5555-5555-555555555555"
            ][-1]
            assert patch_call is not None
            # Preserva voz.ogg + adiciona capa.jpg e demo.mov
            names = [f["name"] for f in patch_call["properties"]["Anexos / Capa"]["files"]]
            self.assertEqual(names, ["voz.ogg", "capa.jpg", "demo.mov"])
            self.assertEqual(patch_call["cover"], {"type": "file_upload", "file_upload": {"id": "fu-1"}})

            append_call = [
                p for m, path, p in client.calls
                if m == "PATCH" and path == "/blocks/55555555-5555-5555-5555-555555555555/children"
            ][-1]
            assert append_call is not None
            self.assertEqual([b["type"] for b in append_call["children"]], ["paragraph", "embed", "image", "video"])

    def test_cli_main_tasks_list_json(self) -> None:
        fake = FakeNotionClient()
        fake_env = {
            "NOTION_API_KEY": "ntn_fake",
            "NOTION_TASKS_DS_ID": "22222222-2222-2222-2222-222222222222",
        }
        with mock.patch.object(nh, "load_env", return_value=fake_env), mock.patch.object(
            nh, "NotionClient", return_value=fake
        ), mock.patch("sys.stdout", new_callable=nh.io.StringIO) as out:
            rc = nh.main(["tasks", "list", "--json"])
            self.assertEqual(rc, 0)
            parsed = json.loads(out.getvalue())
            self.assertEqual(len(parsed), 1)
            self.assertEqual(parsed[0]["title"], "Integrar Notion Dev Hub")

    def test_cmd_theme_restyles_root_page_idempotently_and_preserves_custom_blocks(self) -> None:
        client = FakeNotionClient()
        root_id = "8a89378c-be6b-83f3-bc24-81a553d09ed0"
        ideas_db_id = "33333333-3333-3333-3333-333333333333"
        tasks_db_id = "11111111-1111-1111-1111-111111111111"
        fitlab_id = "cccccccc-cccc-cccc-cccc-000000000001"

        client.children_by_parent = {
            root_id: [
                {
                    "id": "old-banner",
                    "type": "callout",
                    "callout": {"rich_text": [{"plain_text": "EMORPHOSIS // DEV HUB"}]},
                },
                {"id": "old-cols", "type": "column_list", "has_children": True, "column_list": {}},
                {"id": "old-div-top", "type": "divider", "divider": {}},
                {
                    "id": "old-h-ideas",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"plain_text": "01 // IDEA & MEDIA VAULT"}]},
                },
                {"id": ideas_db_id, "type": "child_database", "child_database": {"title": "Idea & Media Vault"}},
                {"id": "old-div-mid", "type": "divider", "divider": {}},
                {
                    "id": "old-h-tasks",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"plain_text": "02 // DEV TASK TRACKER"}]},
                },
                {"id": tasks_db_id, "type": "child_database", "child_database": {"title": "Dev Task Tracker"}},
                {"id": "user-div", "type": "divider", "divider": {}},
                {
                    "id": "user-note",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"plain_text": "Notas manuais da equipe"}]},
                },
                {"id": "old-div-foot", "type": "divider", "divider": {}},
                {
                    "id": "old-toggle",
                    "type": "toggle",
                    "toggle": {"rich_text": [{"plain_text": "03 // TERMINAL CHEATSHEET & VISUAL"}]},
                },
            ],
            "old-cols": [
                {"id": "col-1", "type": "column", "has_children": True, "column": {}},
            ],
            "col-1": [
                {
                    "id": "col-1-callout",
                    "type": "callout",
                    "callout": {"rich_text": [{"plain_text": "00 // TERMINAL_NAV"}]},
                }
            ],
        }
        client.query_results_override = [
            {
                "id": fitlab_id,
                "cover": None,
                "properties": {
                    "Ideia": {"type": "title", "title": [{"plain_text": "Expandir biblioteca do Fit Lab"}]},
                    "Anexos / Capa": {"type": "files", "files": []},
                },
            }
        ]
        client.page_by_id[fitlab_id] = {
            "object": "page",
            "id": fitlab_id,
            "url": "https://www.notion.so/fitlabseed",
            "cover": None,
            "properties": {
                "Ideia": {"type": "title", "title": [{"plain_text": "Expandir biblioteca do Fit Lab"}]},
                "Formatos": {"type": "multi_select", "multi_select": [{"name": "Texto / Briefing"}]},
                "Anexos / Capa": {"type": "files", "files": []},
            },
        }

        env = {
            "NOTION_ROOT_PAGE_ID": root_id,
            "NOTION_IDEAS_DB_ID": ideas_db_id,
            "NOTION_IDEAS_DS_ID": "44444444-4444-4444-4444-444444444444",
            "NOTION_TASKS_DB_ID": tasks_db_id,
            "NOTION_TASKS_DS_ID": "22222222-2222-2222-2222-222222222222",
        }
        nh.cmd_theme(client, env)

        # Chrome antigo removido, mas bancos e nota customizada (+ divider dela) preservados
        self.assertEqual(
            set(client.deleted_blocks),
            {"old-banner", "old-cols", "old-div-top", "old-h-ideas", "old-div-mid", "old-h-tasks", "old-div-foot", "old-toggle"},
        )
        self.assertNotIn(ideas_db_id, client.deleted_blocks)
        self.assertNotIn(tasks_db_id, client.deleted_blocks)
        self.assertNotIn("user-div", client.deleted_blocks)
        self.assertNotIn("user-note", client.deleted_blocks)

        # Uploads e branding aplicados na página raiz e bancos
        self.assertEqual([u["filename"] for u in client.uploads], ["notion-cover.png", "notion-icon.png", "aevus-jaqueta.png"])
        root_patch = [p for m, path, p in client.calls if m == "PATCH" and path == f"/pages/{root_id}"][-1]
        assert root_patch is not None
        self.assertIn("cover", root_patch)
        self.assertIn("icon", root_patch)
        fitlab_patch = [p for m, path, p in client.calls if m == "PATCH" and path == f"/pages/{fitlab_id}"][-1]
        assert fitlab_patch is not None
        self.assertIn("cover", fitlab_patch)

        # Posicionamento exato dos novos blocos HUD na página raiz
        root_appends = [
            p for m, path, p in client.calls
            if m == "PATCH" and path == f"/blocks/{root_id}/children"
        ]
        self.assertEqual(len(root_appends), 3)
        self.assertEqual(root_appends[0]["position"], {"type": "start"})
        self.assertEqual([b["type"] for b in root_appends[0]["children"]], ["callout", "column_list", "divider", "heading_2"])
        self.assertEqual(root_appends[1]["position"], {"type": "after_block", "after_block": {"id": ideas_db_id}})
        self.assertEqual([b["type"] for b in root_appends[1]["children"]], ["divider", "heading_2"])
        self.assertEqual(root_appends[2]["position"], {"type": "after_block", "after_block": {"id": tasks_db_id}})
        self.assertEqual([b["type"] for b in root_appends[2]["children"]], ["divider", "toggle"])

    def test_cmd_theme_fallback_without_columns_and_cli_skip_layout(self) -> None:
        client = FakeNotionClient()
        root_id = "8a89378c-be6b-83f3-bc24-81a553d09ed0"
        ideas_db_id = "33333333-3333-3333-3333-333333333333"
        client.fail_column_list = True
        client.children_by_parent[root_id] = [
            {"id": ideas_db_id, "type": "child_database", "child_database": {"title": "Idea & Media Vault"}}
        ]
        env = {"NOTION_ROOT_PAGE_ID": root_id, "NOTION_IDEAS_DB_ID": ideas_db_id}

        nh.cmd_theme(client, env)
        root_appends = [
            p for m, path, p in client.calls
            if m == "PATCH" and path == f"/blocks/{root_id}/children"
        ]
        # Primeira tentativa com column_list falha, fallback envia 2 callouts empilhados
        self.assertEqual([b["type"] for b in root_appends[1]["children"]], ["callout", "callout", "callout", "divider", "heading_2"])

        # Testa --skip-layout via CLI main()
        client_skip = FakeNotionClient()
        client_skip.children_by_parent[root_id] = [
            {"id": ideas_db_id, "type": "child_database", "child_database": {"title": "Idea & Media Vault"}}
        ]
        skip_env = {
            "NOTION_API_KEY": "ntn_fake",
            "NOTION_ROOT_PAGE_ID": root_id,
        }
        with mock.patch.object(nh, "load_env", return_value=skip_env), mock.patch.object(
            nh, "NotionClient", return_value=client_skip
        ), mock.patch("sys.stdout", new_callable=nh.io.StringIO):
            rc = nh.main(["theme", "--skip-layout"])
            self.assertEqual(rc, 0)
        self.assertEqual(client_skip.deleted_blocks, [])
        self.assertEqual(
            [c for c in client_skip.calls if c[0] == "PATCH" and c[1] == f"/blocks/{root_id}/children"],
            [],
        )
        self.assertEqual([u["filename"] for u in client_skip.uploads], ["notion-cover.png", "notion-icon.png"])

    def test_enrich_fitlab_seed_cover_skips_when_already_populated(self) -> None:
        client = FakeNotionClient()
        client.query_results_override = [
            {
                "id": "cccccccc-cccc-cccc-cccc-000000000009",
                "cover": {"type": "file", "file": {"url": "https://cdn.notion.so/jaqueta.png"}},
                "properties": {
                    "Anexos / Capa": {
                        "type": "files",
                        "files": [{"name": "aevus-jaqueta.png", "type": "file"}],
                    }
                },
            }
        ]
        nh._enrich_fitlab_seed_cover(client, "44444444-4444-4444-4444-444444444444")
        self.assertEqual(client.uploads, [])

    def test_cli_theme_missing_custom_cover_returns_error(self) -> None:
        fake_env = {"NOTION_API_KEY": "ntn_fake", "NOTION_ROOT_PAGE_ID": "8a89378c-be6b-83f3-bc24-81a553d09ed0"}
        with mock.patch.object(nh, "load_env", return_value=fake_env), mock.patch.object(
            nh, "NotionClient", return_value=FakeNotionClient()
        ), mock.patch("sys.stderr", new_callable=nh.io.StringIO) as err:
            rc = nh.main(["theme", "--cover", "/caminho/que/nao/existe/cover.png"])
            self.assertEqual(rc, 1)
            self.assertIn("Imagem de capa não encontrada", err.getvalue())


if __name__ == "__main__":
    unittest.main()
