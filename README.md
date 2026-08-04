# Letters for your Heart

A password-protected editor for you, a read-only page for them.

## What it does

- **Reader view (default, public link):** a grid of mood letters — Happy, Sad, Lonely, Exhausted,
  Angry, Overwhelmed, Missing Me, Just Need This Today. Click one to open it, with a photo on the
  side if you've added one. No edit controls are shown here.
- **Editor (you only):** open the sidebar, enter your password, and you can write/edit every
  letter, add a photo per letter, add new moods, or delete ones you don't want. Only visible
  after the correct password is entered.

## Run it locally

```bash
pip install -r requirements.txt --break-system-packages
streamlit run app.py
```

Your local edit password is set in `.streamlit/secrets.toml` (defaults to `changeme` — change it
before you do anything real with it).

## Deploy so you can share a live link

1. Push this folder to a **GitHub repo** (can be private).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in, and click **New app**.
3. Point it at your repo, branch `main`, file `app.py`.
4. Before deploying (or after, in **App settings → Secrets**), add:
   ```toml
   EDIT_PASSWORD = "pick-something-only-you-know"
   ```
   This keeps your real password out of the public repo — do **not** commit your real password
   into `secrets.toml` if the repo is public.
5. Deploy. You'll get a URL like `https://your-app-name.streamlit.app` — that's the link you
   share. Anyone who opens it lands in reader view. Only you, with the password in the sidebar,
   can edit.

## A note on persistence

Letters and photos are saved to `data/letters.json` on the server. This persists while the app is
running, but Streamlit Cloud can occasionally restart an app and reset it to what's in your GitHub
repo. Once you're happy with your letters, it's worth committing `data/letters.json` back to the
repo (or just keeping a copy) so nothing gets lost.

## Photos

Photos are stored as compressed JPEGs directly inside `data/letters.json` (as base64), so there's
no separate images folder to manage or lose track of.
