# VulcanBoard – notes for AI agents

A hotkey board for desktop touchscreens (Kivy GUI + FastAPI HTTP API). Its main production use is the touchscreen of the livestreaming PC of the Mennonitengemeinde Basel-Holee, where it runs inside the `python_venv` toolbox (Fedora Silverblue, **Python 3.13**) and is the central control surface during the Sunday service. Stability matters more than features.

## Layout

- `VulcanBoard.py` → the app: builds the grid, runs button commands, 300 ms per-button debounce, starts the HTTP API (uvicorn) with the routes in `_setup_api_routes()`.
- `config/` → `load.py` (YAML loading + **all validation**), `classes.py` (`Config` dataclass), `const.py` (default colors, `DEFAULT_STATE_ID = 0`, `ERROR_SINK_STATE_ID = 1`), `state.py` (exit code → state), `path.py` (config path: `$XDG_CONFIG_HOME/VulcanBoard/config.yml`, `%APPDATA%` on Windows).
- `ui/button.py` (`AutoResizeButton`), `vulcanboard.kv`, `util/` (logging, GUI error exit).
- `example-config.yml` → minimal example. The real config, with about 60 buttons, lives in `livestreaming-pc-infra` (see below).
- `ConfigEditorApp.py`, `Settings.py` → work-in-progress GUI config editor (roadmap item), not used in production.

## Behavior that the code defines

The code is authoritative; the README is partly outdated.

- **Threading:** Kivy runs on the main thread. Button commands and the uvicorn server run as coroutines on a separate asyncio loop in a daemon thread (`async_task`). **Widget changes must go through `Clock.schedule_once`**, never directly from that loop.
- `position: [row, col]`. The grid is keyed `(row, col)`. The API's `x`/`y` and `affects_buttons` entries are the same `[row, col]` pair, despite the names.
- **For stateful buttons (more than one state), the command's exit code always selects the new state**, and an unknown exit code goes to state `1` (error sink). There is no implicit cycling, contrary to the README. `follow_up_state` (an int or `exit_code`) only decides whether the command of the resulting state is run as well; `follow_up_execute_states` limits that.
- Validation in `config/load.py`: every button needs state `0`; stateful buttons also need state `1`; `affects_buttons` targets must exist, be stateful and have the **same set of state IDs** as the source button; button `id`s are unique strings.
- `POST /set_state` (also accepted as `GET`) only changes the displayed state. It does **not** run the command and does not touch `affects_buttons`. `GET /get_current_state` and `GET /get_states` accept `id` or `x`+`y`.
- The config is read once at startup; there is no reload.

## Conventions

- **New config key:** read it in `config/load.py`, validate it there, add it to `Config` in `config/classes.py`, give it a sensible default, and document it in the README.
- The config schema and the API (routes, parameters, response JSON such as `{"state_id": N}`) are used by `livestreaming-pc-infra`'s scripts, Home Assistant and `diy_ptz_switch`. Treat them as a public interface: keep changes backwards compatible, or flag the breakage explicitly.
- Windows support (`os.name == "nt"` paths) still exists. Don't remove it without asking.
- Match the existing style (black-style formatting, type hints where present, `# pyright: ignore` / `# pylint: disable=...` only where needed). There are no tests. Verify with a temporary config via `XDG_CONFIG_HOME=<tmpdir> python VulcanBoard.py`; the API then listens on 8080 (or `api_port`).

## Safety

- On the livestreaming PC (`ssh livestream@192.168.71.139`), VulcanBoard drives real hardware through its button commands. **Read only:** don't press buttons through the API, don't restart VulcanBoard and don't edit `~/.config/VulcanBoard/config.yml` there without asking. That file is deployed by Ansible anyway; change it in `livestreaming-pc-infra`.

## Sibling repos

On the dev machine, the related repos are checked out next to this one in `~/dox/src/` (`../<name>/`).

| Sibling | Interface with this repo |
| :--- | :--- |
| `livestreaming-pc-infra` | Deploys this repo (from the `master` branch of the GitHub URL) and holds the production config `roles/sw_setup/files/config.yml` and `templates/launch-vulcanboard.j2`. Its scripts read and set button states through the API (`get_current_state`, `set_state` by `id`). |
| `diy_ptz_switch` | Pushes the PTZ speed level to a button via `POST /set_state` with `x`/`y` (`vulcan_speed_push` in its config). |
| `technik-dokumentation` | Full technical documentation (German). Read its `AGENTS.md` (section map) first, then only the relevant sections of `home.md`, never the whole file. Most relevant: `### Wie funktioniert das VulcanBoard? (Einfach erklärt)`, `### Die Licht- und Audioautomation mit VulcanBoard erklärt`. |

Home Assistant also calls `set_state` (`rest_command` on the NAS, documented in `technik-dokumentation`).

Rules:

* When changing config semantics, validation or the API, check the production config and the callers in `livestreaming-pc-infra` (e.g. `grep -rn '8080' ../livestreaming-pc-infra/roles`) and make the matching change, or explicitly say what needs to change there.
* Read siblings selectively, never whole repos.
* If a sibling is not checked out, say so instead of guessing its interface.

## Workflow

* **NEVER commit or push.** Leave all git history operations to the user.
* When a change is done, suggest a commit message following Conventional Commits,
  **unscoped** (`feat!: ...`, `feat: ...`, `fix: ...`, `chore: ...`, `doc: ...`, `refactor: ...`),
  lowercase, imperative, matching `git log`. If the change spans several repos, suggest
  one message per repo.
