"""
Antigravity IDE - Mobile (Android/iOS)
Built with Flet for cross-platform mobile deployment.
Run: flet build apk
"""
import flet as ft
import json
import os
import httpx

SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".antigravity", "mobile_settings.json")

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {"api_key": "", "model": "google/gemma-4-31b-it", "base_url": "https://openrouter.ai/api/v1"}

def save_settings(s):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(s, f, indent=2)

def main(page: ft.Page):
    page.title = "Antigravity AI"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#1e1e1e"
    page.padding = 0

    settings = load_settings()
    chat_history = []

    # ── Chat Messages ListView ──
    chat_list = ft.ListView(expand=True, spacing=4, auto_scroll=True, padding=ft.padding.all(12))

    def add_msg(role, text):
        color = "#eee" if role == "user" else "#ccc"
        bg = "#252526" if role == "user" else "#1e1e1e"
        avatar_color = "#764ba2" if role == "user" else "#007acc"
        avatar_letter = "U" if role == "user" else "A"

        chat_list.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Text(avatar_letter, size=13, weight=ft.FontWeight.BOLD, color="#fff"),
                        width=30, height=30, border_radius=8,
                        bgcolor=avatar_color, alignment=ft.alignment.center,
                    ),
                    ft.Container(
                        content=ft.Markdown(text, selectable=True,
                            extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED,
                            code_theme=ft.MarkdownCodeTheme.MONOKAI,
                        ),
                        expand=True, padding=ft.padding.only(left=8),
                    ),
                ], alignment=ft.CrossAxisAlignment.START),
                bgcolor=bg, border_radius=8, padding=12, margin=ft.margin.only(bottom=4),
            )
        )
        page.update()

    # ── Send Message ──
    async def send_message(e):
        text = input_field.value.strip()
        if not text:
            return
        input_field.value = ""
        send_btn.disabled = True
        page.update()

        add_msg("user", text)
        chat_history.append({"role": "user", "content": text})

        # Call AI API
        try:
            messages = [{"role": "system", "content": "You are Antigravity AI, an elite coding assistant. Be concise, helpful, and write production-quality code."}]
            messages.extend(chat_history[-20:])

            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{settings['base_url']}/chat/completions",
                    headers={"Authorization": f"Bearer {settings['api_key']}", "Content-Type": "application/json"},
                    json={"model": settings["model"], "messages": messages, "max_tokens": 4096},
                )
                data = resp.json()
                reply = data["choices"][0]["message"]["content"]
                chat_history.append({"role": "assistant", "content": reply})
                add_msg("assistant", reply)
        except Exception as ex:
            add_msg("assistant", f"**Error:** {str(ex)}")

        send_btn.disabled = False
        page.update()

    # ── Input Area ──
    input_field = ft.TextField(
        hint_text="Ask anything...", expand=True, border_radius=20,
        bgcolor="#252526", border_color="#3c3c3c", color="#fff",
        focused_border_color="#007acc", text_size=14, min_lines=1, max_lines=4,
        on_submit=send_message,
    )
    send_btn = ft.IconButton(icon=ft.Icons.SEND_ROUNDED, icon_color="#007acc", on_click=send_message)

    # ── Settings Dialog ──
    api_key_field = ft.TextField(label="API Key", value=settings["api_key"], password=True, bgcolor="#1e1e1e", color="#fff")
    model_field = ft.TextField(label="Model", value=settings["model"], bgcolor="#1e1e1e", color="#fff")
    base_url_field = ft.TextField(label="Base URL", value=settings["base_url"], bgcolor="#1e1e1e", color="#fff")

    def save_settings_click(e):
        settings["api_key"] = api_key_field.value
        settings["model"] = model_field.value
        settings["base_url"] = base_url_field.value
        save_settings(settings)
        settings_dialog.open = False
        page.update()

    settings_dialog = ft.AlertDialog(
        title=ft.Text("Settings", weight=ft.FontWeight.BOLD),
        content=ft.Column([api_key_field, model_field, base_url_field], tight=True, spacing=12, width=300),
        actions=[ft.TextButton("Save", on_click=save_settings_click)],
    )

    def open_settings(e):
        page.overlay.append(settings_dialog)
        settings_dialog.open = True
        page.update()

    # ── New Chat ──
    def new_chat(e):
        chat_history.clear()
        chat_list.controls.clear()
        page.update()

    # ── Layout ──
    page.add(
        ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Text("Antigravity AI", size=16, weight=ft.FontWeight.BOLD, color="#fff"),
                        ft.Row([
                            ft.IconButton(icon=ft.Icons.ADD_COMMENT_ROUNDED, icon_color="#aaa", on_click=new_chat, tooltip="New Chat"),
                            ft.IconButton(icon=ft.Icons.SETTINGS_ROUNDED, icon_color="#aaa", on_click=open_settings, tooltip="Settings"),
                        ], spacing=0),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    bgcolor="#181818", padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    border=ft.border.only(bottom=ft.BorderSide(1, "#2b2b2b")),
                ),
                # Chat area
                chat_list,
                # Input area
                ft.Container(
                    content=ft.Row([input_field, send_btn], spacing=8),
                    padding=ft.padding.all(12),
                    border=ft.border.only(top=ft.BorderSide(1, "#2b2b2b")),
                    bgcolor="#181818",
                ),
            ], spacing=0, expand=True),
            expand=True,
        )
    )

ft.app(target=main)
