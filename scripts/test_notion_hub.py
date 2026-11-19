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
    """Cliente fake stateful em memória para validar chamadas de API sem rede."""

    def __init__(self) -> None:
        super().__init__(token="ntn_test_token_only")
        self.calls: list[tuple[str, str, dict | None]] = []
        self.uploads: list[dict] = []
        self.fail_first_task_db = False
        self.fail_callout_icon = False
        self.children_by_parent: dict[str, list[dict]] = {}
        self.deleted_blocks: list[str] = []
        self.page_by_id: dict[str, dict] = {}
        self.databases: dict[str, dict] = {}
        self.views_by_id: dict[str, dict] = {}
        self.views_by_db: dict[str, list[str]] = {}
        self.query_results_override: list[dict] | None = None
        self.query_override_by_ds: dict[str, list[dict]] = {}
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
                "in_trash": False,
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
                "results": list(self.children_by_parent.get(bid, [])),
                "has_more": False,
                "next_cursor": None,
            }

        if method == "DELETE" and path.startswith("/blocks/"):
            bid = path.split("/blocks/")[1]
            self.deleted_blocks.append(bid)
            for parent_id, kids in list(self.children_by_parent.items()):
                self.children_by_parent[parent_id] = [k for k in kids if k.get("id") != bid]
            return {"object": "block", "id": bid, "in_trash": True}

        if method == "PATCH" and path.startswith("/blocks/") and path.endswith("/children"):
            if self.fail_callout_icon and payload:
                for blk in payload.get("children", []):
                    if blk.get("type") == "callout":
                        icon = (blk.get("callout") or {}).get("icon") or {}
                        if icon.get("type") == "icon":
                            raise nh.NotionAPIError(400, "validation_error", "native callout icon unsupported")
            return {"object": "list", "results": []}

        if method == "GET" and path.startswith("/databases/"):
            db_id = path.split("/databases/")[1]
            if db_id in self.databases:
                return self.databases[db_id]
            return {"id": db_id, "parent": {"type": "page_id", "page_id": ""}, "is_inline": False, "data_sources": []}

        if method == "PATCH" and path.startswith("/databases/"):
            db_id = path.split("/databases/")[1]
            db_obj = self.databases.setdefault(db_id, {"id": db_id, "parent": {}, "is_inline": True})
            if payload:
                if "parent" in payload:
                    new_parent = payload["parent"].get("page_id")
                    old_parent = (db_obj.get("parent") or {}).get("page_id")
                    if old_parent and old_parent in self.children_by_parent:
                        moved = [b for b in self.children_by_parent[old_parent] if b.get("id") == db_id]
                        self.children_by_parent[old_parent] = [
                            b for b in self.children_by_parent[old_parent] if b.get("id") != db_id
                        ]
                        if new_parent and moved:
                            self.children_by_parent.setdefault(new_parent, []).extend(moved)
                    elif new_parent:
                        self.children_by_parent.setdefault(new_parent, []).append(
                            {
                                "id": db_id,
                                "type": "child_database",
                                "child_database": {"title": db_obj.get("title_text", "Database")},
                            }
                        )
                    db_obj["parent"] = payload["parent"]
                if "is_inline" in payload:
                    db_obj["is_inline"] = payload["is_inline"]
                if "title" in payload:
                    title_txt = "".join((t.get("text") or {}).get("content", "") for t in payload["title"])
                    db_obj["title_text"] = title_txt
                    for kids in self.children_by_parent.values():
                        for b in kids:
                            if b.get("id") == db_id and b.get("type") == "child_database":
                                b["child_database"]["title"] = title_txt
            return db_obj

        if method == "POST" and path == "/databases":
            title_txt = "".join(t["text"]["content"] for t in (payload or {}).get("title", []))
            if "Task" in title_txt:
                if self.fail_first_task_db:
                    self.fail_first_task_db = False
                    raise nh.NotionAPIError(400, "validation_error", "status group unsupported on create")
                db_id = "11111111-1111-1111-1111-111111111111"
                ds_id = "22222222-2222-2222-2222-222222222222"
            else:
                db_id = "33333333-3333-3333-3333-333333333333"
                ds_id = "44444444-4444-4444-4444-444444444444"
            res = {
                "id": db_id,
                "parent": (payload or {}).get("parent", {}),
                "is_inline": (payload or {}).get("is_inline", False),
                "title_text": title_txt,
                "data_sources": [{"id": ds_id, "name": title_txt}],
            }
            self.databases[db_id] = res
            parent_pid = ((payload or {}).get("parent") or {}).get("page_id")
            if parent_pid:
                self.children_by_parent.setdefault(parent_pid, []).append(
                    {"id": db_id, "type": "child_database", "child_database": {"title": title_txt}}
                )
            return res

        if method == "GET" and path.startswith("/views?"):
            qs = path.split("?", 1)[1]
            params = dict(part.split("=", 1) for part in qs.split("&") if "=" in part)
            db_id = nh.urllib.parse.unquote(params.get("database_id", ""))
            ids = self.views_by_db.get(db_id, [])
            return {
                "object": "list",
                "results": [{"object": "view", "id": vid} for vid in ids],
                "has_more": False,
                "next_cursor": None,
            }

        if method == "GET" and path.startswith("/views/"):
            vid = path.split("/views/")[1]
            return self.views_by_id.get(vid, {"object": "view", "id": vid, "name": "Table"})

        if method == "PATCH" and path.startswith("/views/"):
            vid = path.split("/views/")[1]
            view_obj = self.views_by_id.setdefault(vid, {"object": "view", "id": vid, "name": ""})
            if payload and "name" in payload:
                view_obj["name"] = payload["name"]
            return view_obj

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
            parent = (payload or {}).get("parent") or {}
            if parent.get("type") == "page_id":
                parent_id = parent["page_id"]
                props = (payload or {}).get("properties") or {}
                title_spans = ((props.get("title") or {}).get("title") or [])
                title_txt = "".join((s.get("text") or {}).get("content", "") for s in title_spans) or "Page"
                self.children_by_parent.setdefault(parent_id, []).append(
                    {"id": pid, "type": "child_page", "child_page": {"title": title_txt}}
                )
                self.page_by_id[pid] = {
                    "object": "page",
                    "id": pid,
                    "url": f"https://www.notion.so/{pid.replace('-', '')}",
                    "in_trash": False,
                    "properties": {"title": {"type": "title", "title": [{"plain_text": title_txt}]}},
                }
            return {"id": pid, "url": f"https://www.notion.so/{pid.replace('-', '')}"}

        if method == "POST" and path.endswith("/query"):
            ds_id = path.split("/data_sources/")[1].split("/query")[0]
            if ds_id in self.query_override_by_ds:
                return {
                    "results": self.query_override_by_ds[ds_id],
                    "has_more": False,
                    "next_cursor": None,
                }
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

    def test_bootstrap_creates_team_root_dev_subpage_clean_dbs_views_and_seed(self) -> None:
        client = FakeNotionClient()
        client.fail_first_task_db = True
        root_id = "99999999-9999-9999-9999-999999999999"
        client.page_by_id[root_id] = {
            "object": "page",
            "id": root_id,
            "url": f"https://www.notion.so/{root_id.replace('-', '')}",
            "properties": {"title": {"type": "title", "title": [{"plain_text": "Velho"}]}},
        }
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text("NOTION_API_KEY=ntn_fake\n", encoding="utf-8")
            ids = nh.cmd_bootstrap(
                client=client,
                page_id_raw=f"https://www.notion.so/EMORPHOSIS-HUB-{root_id.replace('-', '')}",
                seed=True,
                save_env=True,
                env_path=env_file,
            )
            self.assertEqual(ids["NOTION_ROOT_PAGE_ID"], root_id)
            dev_id = ids["NOTION_DEV_PAGE_ID"]
            self.assertTrue(dev_id)
            self.assertEqual(ids["NOTION_TASKS_DS_ID"], "22222222-2222-2222-2222-222222222222")
            self.assertEqual(ids["NOTION_IDEAS_DS_ID"], "44444444-4444-4444-4444-444444444444")

            # Raiz renomeada para EMORPHOSIS com capa e ícone oficiais
            root_patch = [p for m, path, p in client.calls if m == "PATCH" and path == f"/pages/{root_id}"][-1]
            self.assertEqual(root_patch["properties"]["title"]["title"][0]["text"]["content"], "EMORPHOSIS")
            self.assertIn("cover", root_patch)
            self.assertIn("icon", root_patch)

            # Bancos criados dentro da subpágina Desenvolvimento como full-page (is_inline=False) e sem emojis
            db_creates = [p for m, path, p in client.calls if m == "POST" and path == "/databases"]
            self.assertTrue(all(p["parent"]["page_id"] == dev_id for p in db_creates))
            self.assertTrue(all(p["is_inline"] is False for p in db_creates))

            # Views sem emojis e sem parênteses
            view_calls = [p for m, path, p in client.calls if m == "POST" and path == "/views"]
            self.assertEqual([v["name"] for v in view_calls], ["Kanban", "Prioridades Ativas", "Concluídas", "Moodboard", "Inbox", "Pipeline"])

            # Verifica que back-relation foi renomeada para "Tarefas Geradas"
            patch_ideas = [
                p for m, path, p in client.calls
                if m == "PATCH" and path == "/data_sources/44444444-4444-4444-4444-444444444444"
            ]
            self.assertTrue(any(p and p.get("properties", {}).get("back_rel_id", {}).get("name") == "Tarefas Geradas" for p in patch_ideas))

            # Seed: 1 ideia + 3 tarefas sem parênteses nos títulos
            ds_pages = [
                p for m, path, p in client.calls
                if m == "POST" and path == "/pages" and p["parent"]["type"] == "data_source_id"
            ]
            self.assertEqual(len(ds_pages), 4)
            task_titles = [
                "".join(t["text"]["content"] for t in p["properties"]["Tarefa"]["title"])
                for p in ds_pages
                if "Tarefa" in p["properties"]
            ]
            self.assertTrue(all("(" not in t and ")" not in t for t in task_titles))

            # .env contém NOTION_DEV_PAGE_ID
            self.assertIn(f"NOTION_DEV_PAGE_ID={dev_id}", env_file.read_text(encoding="utf-8"))

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

    def test_cmd_theme_migrates_single_page_hub_to_multi_page_and_strips_ai_slop(self) -> None:
        client = FakeNotionClient()
        root_id = "8a89378c-be6b-83f3-bc24-81a553d09ed0"
        ideas_db_id = "33333333-3333-3333-3333-333333333333"
        tasks_db_id = "11111111-1111-1111-1111-111111111111"
        ideas_ds_id = "44444444-4444-4444-4444-444444444444"
        tasks_ds_id = "22222222-2222-2222-2222-222222222222"
        fitlab_id = "cccccccc-cccc-cccc-cccc-000000000001"
        seed_t2 = "dddddddd-dddd-dddd-dddd-000000000002"
        user_t = "dddddddd-dddd-dddd-dddd-000000000009"

        client.page_by_id[root_id] = {
            "object": "page",
            "id": root_id,
            "url": f"https://www.notion.so/{root_id.replace('-', '')}",
            "properties": {"title": {"type": "title", "title": [{"plain_text": "EMORPHOSIS // DEV HUB"}]}},
        }
        client.databases = {
            ideas_db_id: {
                "id": ideas_db_id,
                "parent": {"type": "page_id", "page_id": root_id},
                "is_inline": True,
                "title_text": "Idea & Media Vault",
                "data_sources": [{"id": ideas_ds_id}],
            },
            tasks_db_id: {
                "id": tasks_db_id,
                "parent": {"type": "page_id", "page_id": root_id},
                "is_inline": True,
                "title_text": "Dev Task Tracker",
                "data_sources": [{"id": tasks_ds_id}],
            },
        }
        client.views_by_db = {
            tasks_db_id: ["v-t1", "v-t2", "v-t3"],
            ideas_db_id: ["v-i1", "v-i2", "v-i3"],
        }
        client.views_by_id = {
            "v-t1": {"id": "v-t1", "name": "📋 Kanban (Status)"},
            "v-t2": {"id": "v-t2", "name": "🔥 Prioridades Ativas"},
            "v-t3": {"id": "v-t3", "name": "✅ Concluídas (DEVLOG)"},
            "v-i1": {"id": "v-i1", "name": "🎨 Moodboard (Galeria)"},
            "v-i2": {"id": "v-i2", "name": "📥 Inbox de Captura"},
            "v-i3": {"id": "v-i3", "name": "🚀 Pipeline de Ideias"},
        }
        client.children_by_parent = {
            root_id: [
                {"id": "old-banner", "type": "callout", "callout": {"rich_text": [{"plain_text": "EMORPHOSIS // DEV HUB"}]}},
                {"id": "old-cols", "type": "column_list", "has_children": True, "column_list": {}},
                {"id": "old-div-top", "type": "divider", "divider": {}},
                {"id": "old-h-ideas", "type": "heading_2", "heading_2": {"rich_text": [{"plain_text": "01 // IDEA & MEDIA VAULT"}]}},
                {"id": ideas_db_id, "type": "child_database", "child_database": {"title": "Idea & Media Vault"}},
                {"id": "old-div-mid", "type": "divider", "divider": {}},
                {"id": "old-h-tasks", "type": "heading_2", "heading_2": {"rich_text": [{"plain_text": "02 // DEV TASK TRACKER"}]}},
                {"id": tasks_db_id, "type": "child_database", "child_database": {"title": "Dev Task Tracker"}},
                {"id": "user-div", "type": "divider", "divider": {}},
                {"id": "user-note", "type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Notas manuais do time"}]}},
                {"id": "old-div-foot", "type": "divider", "divider": {}},
                {"id": "old-toggle", "type": "toggle", "toggle": {"rich_text": [{"plain_text": "03 // TERMINAL CHEATSHEET & VISUAL"}]}},
            ],
            "old-cols": [{"id": "col-1", "type": "column", "has_children": True, "column": {}}],
            "col-1": [{"id": "col-1-callout", "type": "callout", "callout": {"rich_text": [{"plain_text": "00 // TERMINAL_NAV"}]}}],
        }
        client.query_override_by_ds = {
            ideas_ds_id: [
                {
                    "id": fitlab_id,
                    "cover": None,
                    "properties": {
                        "Ideia": {"type": "title", "title": [{"plain_text": "Expandir biblioteca do Fit Lab"}]},
                        "Anexos / Capa": {"type": "files", "files": []},
                    },
                }
            ],
            tasks_ds_id: [
                {
                    "id": seed_t2,
                    "properties": {
                        "Tarefa": {"type": "title", "title": [{"plain_text": "Expandir recortes PNG reais no Fit Lab (novas marcas)"}]},
                    },
                },
                {
                    "id": user_t,
                    "properties": {
                        "Tarefa": {"type": "title", "title": [{"plain_text": "Nota customizada (NÃO MEXER)"}]},
                    },
                },
            ],
        }
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

        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text("NOTION_API_KEY=ntn_fake\n", encoding="utf-8")
            env = {
                "NOTION_ROOT_PAGE_ID": root_id,
                "NOTION_IDEAS_DB_ID": ideas_db_id,
                "NOTION_IDEAS_DS_ID": ideas_ds_id,
                "NOTION_TASKS_DB_ID": tasks_db_id,
                "NOTION_TASKS_DS_ID": tasks_ds_id,
            }
            nh.cmd_theme(client, env, save_env=True, env_path=env_file)
            saved_env_text = env_file.read_text(encoding="utf-8")

        # 1. Raiz renomeada para EMORPHOSIS e subpágina Desenvolvimento criada e gravada no .env
        root_patch = [p for m, path, p in client.calls if m == "PATCH" and path == f"/pages/{root_id}"][-1]
        self.assertEqual(root_patch["properties"]["title"]["title"][0]["text"]["content"], "EMORPHOSIS")
        self.assertIn("cover", root_patch)
        self.assertIn("icon", root_patch)
        self.assertIn("NOTION_DEV_PAGE_ID=aaaaaaaa-aaaa-aaaa-aaaa-000000000001", saved_env_text)
        dev_id = "aaaaaaaa-aaaa-aaaa-aaaa-000000000001"

        # 2. Ambos os bancos movidos para Desenvolvimento com is_inline=False (subpáginas dedicadas!)
        self.assertEqual(client.databases[tasks_db_id]["parent"], {"type": "page_id", "page_id": dev_id})
        self.assertFalse(client.databases[tasks_db_id]["is_inline"])
        self.assertEqual(client.databases[ideas_db_id]["parent"], {"type": "page_id", "page_id": dev_id})
        self.assertFalse(client.databases[ideas_db_id]["is_inline"])

        # 3. Todas as 6 views limpas sem emojis e sem parênteses
        self.assertEqual(client.views_by_id["v-t1"]["name"], "Kanban")
        self.assertEqual(client.views_by_id["v-t2"]["name"], "Prioridades Ativas")
        self.assertEqual(client.views_by_id["v-t3"]["name"], "Concluídas")
        self.assertEqual(client.views_by_id["v-i1"]["name"], "Moodboard")
        self.assertEqual(client.views_by_id["v-i2"]["name"], "Inbox")
        self.assertEqual(client.views_by_id["v-i3"]["name"], "Pipeline")

        # 4. Chrome antigo removido na raiz, nota customizada e bancos intactos
        self.assertEqual(
            set(client.deleted_blocks),
            {"old-banner", "old-cols", "old-div-top", "old-h-ideas", "old-div-mid", "old-h-tasks", "old-div-foot", "old-toggle"},
        )
        self.assertNotIn("user-div", client.deleted_blocks)
        self.assertNotIn("user-note", client.deleted_blocks)

        # 5. Layout limpo aplicado tanto na raiz quanto dentro de Desenvolvimento
        root_appends = [p for m, path, p in client.calls if m == "PATCH" and path == f"/blocks/{root_id}/children"]
        self.assertEqual(root_appends[0]["position"], {"type": "start"})
        self.assertEqual(root_appends[1]["position"], {"type": "after_block", "after_block": {"id": dev_id}})

        dev_appends = [p for m, path, p in client.calls if m == "PATCH" and path == f"/blocks/{dev_id}/children"]
        self.assertEqual(dev_appends[0]["position"], {"type": "start"})
        self.assertEqual(dev_appends[1]["position"], {"type": "after_block", "after_block": {"id": ideas_db_id}})

        # 6. Apenas tarefa seed literal foi limpa; tarefa do usuário não foi tocada
        seed_patch = [p for m, path, p in client.calls if m == "PATCH" and path == f"/pages/{seed_t2}"]
        self.assertTrue(seed_patch)
        self.assertEqual(seed_patch[-1]["properties"]["Tarefa"]["title"][0]["text"]["content"], "Expandir recortes PNG no Fit Lab para novas marcas")
        self.assertFalse(any(path == f"/pages/{user_t}" for _, path, _ in client.calls))

        # 7. Fit Lab recebeu aevus-jaqueta.png sem texto parentético
        fitlab_patch = [p for m, path, p in client.calls if m == "PATCH" and path == f"/pages/{fitlab_id}"][-1]
        self.assertIn("cover", fitlab_patch)

        # 8. Idempotência: rodar theme uma segunda vez reutiliza Desenvolvimento (não cria página duplicada)
        client.page_by_id[fitlab_id]["cover"] = {"type": "file", "file": {"url": "https://cdn.notion.so/aevus.png"}}
        client.query_override_by_ds[ideas_ds_id][0]["cover"] = client.page_by_id[fitlab_id]["cover"]
        client.query_override_by_ds[tasks_ds_id][0]["properties"]["Tarefa"]["title"] = [
            {"plain_text": "Expandir recortes PNG no Fit Lab para novas marcas"}
        ]
        dev_page_creates_before = len(
            [p for m, path, p in client.calls if m == "POST" and path == "/pages" and (p or {}).get("parent", {}).get("type") == "page_id"]
        )
        env["NOTION_DEV_PAGE_ID"] = dev_id
        nh.cmd_theme(client, env, save_env=False)
        dev_page_creates_after = len(
            [p for m, path, p in client.calls if m == "POST" and path == "/pages" and (p or {}).get("parent", {}).get("type") == "page_id"]
        )
        self.assertEqual(dev_page_creates_before, dev_page_creates_after)
        self.assertNotIn("user-div", client.deleted_blocks)
        self.assertNotIn("user-note", client.deleted_blocks)

    def test_cmd_theme_fallback_when_callout_icon_rejected_and_skip_layout(self) -> None:
        client = FakeNotionClient()
        root_id = "8a89378c-be6b-83f3-bc24-81a553d09ed0"
        dev_id = "aaaaaaaa-aaaa-aaaa-aaaa-000000000099"
        client.fail_callout_icon = True
        client.page_by_id[root_id] = {
            "object": "page",
            "id": root_id,
            "in_trash": False,
            "properties": {"title": {"type": "title", "title": [{"plain_text": "EMORPHOSIS"}]}},
        }
        client.page_by_id[dev_id] = {
            "object": "page",
            "id": dev_id,
            "in_trash": False,
            "properties": {"title": {"type": "title", "title": [{"plain_text": "Desenvolvimento"}]}},
        }
        client.children_by_parent[root_id] = [
            {"id": dev_id, "type": "child_page", "child_page": {"title": "Desenvolvimento"}}
        ]
        env = {"NOTION_ROOT_PAGE_ID": root_id, "NOTION_DEV_PAGE_ID": dev_id}

        nh.cmd_theme(client, env)
        root_appends = [p for m, path, p in client.calls if m == "PATCH" and path == f"/blocks/{root_id}/children"]
        # Callout com icon nativo falha -> fallback envia paragraph limpo (sem emoji!)
        self.assertEqual([b["type"] for b in root_appends[2]["children"]], ["divider", "heading_3", "paragraph"])

        # Testa --skip-layout via CLI main()
        client_skip = FakeNotionClient()
        client_skip.page_by_id[root_id] = client.page_by_id[root_id]
        skip_env = {"NOTION_API_KEY": "ntn_fake", "NOTION_ROOT_PAGE_ID": root_id}
        with mock.patch.object(nh, "load_env", return_value=skip_env), mock.patch.object(
            nh, "NotionClient", return_value=client_skip
        ), mock.patch("sys.stdout", new_callable=nh.io.StringIO):
            rc = nh.main(["theme", "--skip-layout"])
            self.assertEqual(rc, 0)
        self.assertEqual(client_skip.deleted_blocks, [])
        self.assertEqual([c for c in client_skip.calls if c[0] == "PATCH" and "/blocks/" in c[1]], [])
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
