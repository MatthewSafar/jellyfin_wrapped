import requests
import os
import json
import tqdm


def get_item_image(item_id: str, server_address: str, output_dir: str):
    """
    Get the image associated with an item, such as the album cover for a song.

    Args:
        item_id (str): The UUID of the item.
        server_address (str): The address to the server, to grab the image.
        output_dir (str): Path to the directory where you want to put the image

    Returns:
        None
    """
    image_response = requests.get(
        f"{server_address}/Items/{item_id}/Images/Primary",
        headers={"accept":"image/*"},
        stream=True
    )
    if (image_response.ok):
        with open(os.path.join(output_dir,item_id),'wb') as outfile:
            for chunk in image_response:
                outfile.write(chunk)
    else:
        raise Exception(
            f"""Could not get items from Jellyfin Server:
            request : {image_response.request.path_url}: {image_response.request.headers}
            response: {image_response.status_code}: {image_response.reason}
            """)



def get_item_userdata(item_id : str, user_id : str, server_address : str, api_key: str) -> dict:
    """
    Get the user data of an item, which is used to get things like Play Count for each user.

    Args:
        item_id (str): The UUID of the item.
        user_id (str): The UUID of the user.
        server_address (str): The address to the server, to grab the image.
        api_key (str): The API key to get the information from the server.

    Returns:
        A dictionary containing the userdata for that particular user and item
        
    """
    userdata_response = requests.get(f"{server_address}/UserItems/{item_id}/UserData?userId={user_id}",
                                     headers={"accept":"application/json","Authorization":f"Mediabrowser Token=\"{api_key}\""})
    if (userdata_response.ok):
        userdata= json.loads(userdata_response.content)
    else:
        raise Exception(
            f"""Could not get items from Jellyfin Server:
            request : {userdata_response.request.path_url}: {userdata_response.request.headers}
            response: {userdata_response.status_code}: {userdata_response.reason}
            """)
    return userdata

def get_all_users(server_address: str, api_key: str) -> list[dict]:
    """
    Make a request to the server to get all of the users and information about them.

    Args:
        server_address (str): The address to the server, to grab the image.
        api_key (str): The API key to get the information from the server.
        
    Returns:
        A list of dictionaries, where each dictionary corresponds to a user.
    """
    all_user_response = requests.get(f"{server_address}/Users",
                                    headers={"accept":"application/json","Authorization":f"Mediabrowser Token=\"{api_key}\""})
    if (all_user_response.ok):
        users = json.loads(all_user_response.content)
    else:
        raise Exception(
            f"""Could not get items from Jellyfin Server:
            request : {all_user_response.request.path_url}: {all_user_response.request.headers}
            response: {all_user_response.status_code}: {all_user_response.reason}
            """)
    return users


def get_all_audio_items(server_address: str, api_key: str) -> list[dict]:
    """
    Requests all of the items with Item Type "Audio" (on the filesystem) from the server.

    Args:
        server_address (str): The address to the server, to grab the image.
        api_key (str): The API key to get the information from the server.
        
    Returns:
        A list of dictionaries, where each dictionary corresponds to an audio item.
    """
    all_item_response = requests.get(f"{server_address}/Items?locationTypes=FileSystem&recursive=true&includeItemTypes=Audio&&enableImages=true",
                 headers={"accept":"application/json","Authorization":f"Mediabrowser Token=\"{api_key}\""})
    if (all_item_response.ok):
        item_data = json.loads(all_item_response.content)
    else:
        raise Exception(
            f"""Could not get items from Jellyfin Server:
            request : {all_item_response.request.path_url}: {all_item_response.request.headers}
            response: {all_item_response.status_code}: {all_item_response.reason}
            """)
    return item_data["Items"]



def generate_jellyfin_recap(
        server_addres:str,
        api_key: str,
        output_dir: str,
        num_top_songs: int = 5,
        num_top_artists: int = 5
) -> None:
    """
    Generates a jellyfin recap similar to the one you might get from a Spotify Wrapped, using the PlayCount field in UserData.

    For a better experience, use something like the PlayBack Reporting plugin that actually captures more data on this stuff.

    Args:
        server_address (str): The address to the server, to grab the image.
        api_key (str): The API key to get the information from the server.
        output_dir (str): the path to the directory to store the final output.
        num_top_songs (int): How many top songs to grab. Default 5.
        num_top_artists (int): How many top artists to grab. Default 5.
    
    Returns:
        None
    """
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
    if not os.path.isdir(os.path.join(output_dir,"assets")):
        os.mkdir(os.path.join(output_dir,"assets"))
    
    # get all audio items from the jellyfin server
    print("Retreiving item info...")
    item_data = get_all_audio_items(server_address, api_key)
    print(f"Finished retrieving item info for {len(item_data)} items.")
    
    # for every item, retrieve user data, most importantly play count
    print("Retreiving Users...")
    users = get_all_users(server_address, api_key)
    print(f"Found {len(users)} users.")
    with open(os.path.join(output_dir,"users.json"),'w') as outfile:
        json.dump(users,outfile,indent=4)
    print("Adding userdata to items...")
    for item in tqdm.tqdm(item_data):
        item["UserData"] = {}
        for user in users:
            userdata = get_item_userdata(item["Id"],user["Id"],server_address,api_key)
            item["UserData"][user["Name"]] = userdata
    print("Finished adding userdata to items.")

    with open(os.path.join(output_dir,"all_items.json"),'w') as outfile:
        json.dump(item_data,outfile,indent=4)

    # with open(os.path.join(output_dir,"all_items.json"),'r') as infile:
    #     item_data = json.load(infile)
    # with open(os.path.join(output_dir,"users.json"),'r') as infile:
    #     users = json.load(infile)

    # get most listened songs
    most_listened_songs = {user["Name"]:[] for user in users}
    
    print(f"Finding {num_top_songs} most listened songs...")
    for user, songlist in most_listened_songs.items():
        songlist.extend(sorted(item_data,key=lambda x:x["UserData"][user]["PlayCount"],reverse=True)[:num_top_songs])
    
    print(f"Finding {num_top_artists} most listened artists...")
    most_listened_artists = {user["Name"]: [] for user in users}
    for user, artistlist in most_listened_artists.items():
        # bake
        artists = {}
        for item in item_data:
            for item_artist in item["Artists"]:
                if item_artist in artists:
                    artists[item_artist] += item["UserData"][user]["PlayCount"]
                else:
                    artists[item_artist] = item["UserData"][user]["PlayCount"]
        artistlist.extend(sorted(artists.items(),key=lambda x: x[1], reverse=True)[:num_top_artists])
    
    print(f"Finding total minutes listened...")
    minutes_listened = {user["Name"]:0 for user in users}
    for user in minutes_listened.keys():
        for item in item_data:
            minutes_listened[user] += (item["RunTimeTicks"] / 6e7) * item["UserData"][user]["PlayCount"]
    
    # most_listened_songs = [(thing["Name"],thing["AlbumArtist"]) for thing in most_listened_songs["maf"]]
    print([(thing["Name"],thing["AlbumArtist"]) for thing in most_listened_songs["maf"]])
    print(most_listened_artists)
    print(minutes_listened)
    
    for user in most_listened_songs.keys():
        most_listened_song_image = get_item_image(most_listened_songs[user][0]["Id"],server_address,os.path.join(output_dir,"assets"))
    
    for user in most_listened_songs.keys():
        html_output = os.path.join(output_dir,f"{user}_jellyfin_wrapped.html")
        with open(html_output,'w') as outfile:
            outfile.write("""
<!DOCTYPE html>
<html>

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="icon" href="favicon.png">
  <style>
    #content {
      width: 500px;
      height: 700px;
      background-color: purple;
      border-radius: 20px;
      margin: auto;
      padding: 25px;
      text-align: center;
      color: white;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    }

    #main_image {
      width: 50%;
      display: inline-block;
    }

    #main_table {
      margin: auto;
      text-align: left;
      width: 100%;
    }

    td {
      font-weight: 700;
    }

    th {
      font-weight: normal;
    }
  </style>
</head>

<body>
  <div id="content">
    <h1>Jellyfin Wrapped</h1>
                          """)
            # image
            outfile.write(f"<img src=\"./assets/{most_listened_songs[user][0]['Id']}\" id=\"main_image\">")
            outfile.write("""
    <table id="main_table">
      <tr>
        <th>Top Artists</th>
        <th>Top Songs</th>
      </tr>
                          """)
            for i in range(min(num_top_songs,num_top_artists)):
                outfile.write("\t\t\t<tr>\n")
                outfile.write(f"\t\t\t\t<td>{i+1}. {most_listened_artists[user][i][0]}</td>\n")
                outfile.write(f"\t\t\t\t<td>{i+1}. {most_listened_songs[user][i]['Name']}</td>\n")
                outfile.write("\t\t\t</tr>\n")
            outfile.write("\t\t</table>\n")
            outfile.write(f"\t\t<p id=\"minutes_listened\">Minutes Listened: {minutes_listened[user]}</p>\n")
            outfile.write("""
  </div>
</body>

</html>
                          """)


if __name__ == "__main__":
    api_key = ""
    output_dir = "./output"
    server_address = "http://localhost:8096"
    generate_jellyfin_recap(server_address,api_key,output_dir)
