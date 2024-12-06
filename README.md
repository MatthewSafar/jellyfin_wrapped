# Jellyfin Wrapped

This is a quick and dirty python script for creating a Jellyfin wrapped using the "PlayCount" field. This field is cumulative for all time, so it will not create statistics for only a year, but for however long the user has had an account.

If you are interested in getting better statistics, consider using the PlayBack Reporter plugin that is official.

Run with:
```bash
python ./jellyfin_recap.py
```
after filling in the appropriate `api_key` and `server_address` variables at the bottom of the script.
```
```


