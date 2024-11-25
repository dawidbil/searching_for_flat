A crude attempt to automate scrolling through apartment listings on facebook & OLX. Two scripts: `scrap_fb.py` & `scrap_olx.py` - will generate CSV with data that can then be named as `feed.csv` to be used by `parse.py` to generate file `parsed.csv` with contents that can be imported to Excel or other software.

An `OPENAI_API_KEY` environment variable is required to use the model. You can put it inside `.env` file.

The `scrap_*.py` scripts might not work anymore.

GPT-4o model is used to generate JSON out of postings content. All prompts are in polish as the posts were scraped in the same language. Aside from generating JSON there is another call made to gpt-4o that takes the generated JSON and verifies whether it's correct (i.e. value types in JSON fields). Until the "verification agent" is satisfied, the "JSON generating agent" will keep making JSONs.
