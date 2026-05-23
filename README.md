# social-publisher

A [Hermes agent](https://hermes-agent.nousresearch.com/) plugin for creating and managing social media posts for LinkedIn and Facebook, with AI image generation and a read-only review dashboard.

## How it works

- **LinkedIn**: always manual. Hermes creates and stores the post; you copy the text from the dashboard and paste it on LinkedIn yourself.
- **Facebook**: auto-publishes to a configured page. Supports multiple pages via numbered env vars (`FACEBOOK_PAGE_1_NAME/ID/TOKEN`, `FACEBOOK_PAGE_2_*`, …). Say "post to \<page name\>" and the right page is selected automatically. Falls back to the legacy single-page env vars (`FACEBOOK_PAGE_ACCESS_TOKEN` + `FACEBOOK_PAGE_ID`) if no numbered pages are set. Without any FB credentials, Facebook posts are manual.
- **Images**: generated or enhanced via OpenAI GPT Image and stored locally. The dashboard lets you view and open them.

## Plugin tools

| Tool | Description |
|---|---|
| `generate_image` | Generate an image from a text prompt (GPT Image) |
| `enhance_image` | Enhance or edit an existing image (GPT Image) |
| `create_post` | Create and store a post for LinkedIn and/or Facebook |
| `update_post` | Edit a stored post's text, platforms, image, or schedule |
| `publish_post` | Immediately publish a post's Facebook target (requires FB credentials) |
| `list_posts` | List stored posts with full metadata, optionally filtered by status |
| `get_post` | Fetch a single post by ID |
| `delete_post` | Delete a stored post by ID |
| `list_facebook_pages` | List the configured Facebook pages by name |

Supported platforms: `linkedin_page`, `facebook_page`

## Installation

### 1. Install dependencies

```bash
pip install openai requests pillow
```

### 2. Copy the plugin to your Hermes server

```bash
scp -r . user@your-server:~/.hermes/plugins/social-publisher/
```

### 3. Set environment variables on the server

```bash
# Required
export OPENAI_API_KEY="sk-..."

# Optional — configure one or more Facebook pages for auto-publishing
# Each page needs three vars; increment the number for additional pages.
export FACEBOOK_PAGE_1_NAME="Sahan'aina"
export FACEBOOK_PAGE_1_ID="110092318253855"
export FACEBOOK_PAGE_1_TOKEN="EAA..."

export FACEBOOK_PAGE_2_NAME="My Other Page"
export FACEBOOK_PAGE_2_ID="987654321"
export FACEBOOK_PAGE_2_TOKEN="EAA..."
```

Once configured, tell Hermes which page to target: *"post to Sahan'aina"* and `create_post` will route to that page automatically. Use `list_facebook_pages` to see all available page names.

#### Legacy single-page fallback

If no numbered `FACEBOOK_PAGE_<N>_*` vars are set, the plugin falls back to the old single-page scheme:

```bash
export FACEBOOK_PAGE_ACCESS_TOKEN="EAA..."
export FACEBOOK_PAGE_ID="123456789"
export FACEBOOK_PAGE_NAME="My Page"  # optional; defaults to "default"
```

This keeps existing deployments working until you migrate to the numbered scheme.

#### Getting your credentials

| Credential | Where to get it |
|---|---|
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `FACEBOOK_PAGE_<N>_TOKEN` | A **long-lived page token** (see note below) |
| `FACEBOOK_PAGE_<N>_ID` | Your page's About section or Graph API Explorer |

> **Facebook token — important:** the token you copy straight from the Graph API Explorer is *short-lived* (~1h) and will fail later with `code 190 / subcode 463 "Session has expired"`. You need a **long-lived page token** (`expires_at: 0`). Full step-by-step guide, including the common pitfalls (user-vs-page token, the `(#100) nonexisting field (accounts)` error, App Secret handling, and the "post is Public but only I can see it" → Page visibility issue):
>
> 📌 biblion forum **`fr_boldwombat`** — *"How to create the Facebook long-lived (non-expiring) page token"* (join with `forum_join`).

### 4. Enable the plugin

```bash
hermes plugins enable social-publisher
```

## Web dashboard

A read-only dashboard lets you review posts, copy text for manual posting, and view images.

### Run with Docker Compose

```bash
docker compose up --build
```

- Dashboard: [http://localhost:52847](http://localhost:52847)
- API: [http://localhost:37421](http://localhost:37421)

### Connecting to the real Hermes DB and images

By default the dashboard uses an isolated Docker volume. To point it at the actual Hermes data, update the backend volumes in `docker-compose.yml`:

```yaml
backend:
  volumes:
    - /home/USER/.hermes/plugins/social-publisher/schedule.db:/data/schedule.db
    - /home/USER/.hermes/plugins/social-publisher/images:/data/images
```

## Post statuses

| Status | Meaning |
|---|---|
| `draft` | Stored, no scheduled time |
| `scheduled` | Has a future scheduled_time; Facebook target will auto-publish when due (if FB configured) |
| `publishing` | Being published right now |
| `published` | Successfully published to Facebook |
| `failed` | Facebook publish attempt failed — check the error field |

## Notes

- LinkedIn posts never auto-publish. Use the dashboard to copy post text and paste it manually.
- Images are saved to `~/.hermes/plugins/social-publisher/images/` on the Hermes server.
- Scheduled posts are checked every 30 seconds by a background thread inside the Hermes process.

## License

MIT
